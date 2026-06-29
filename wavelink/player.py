"""Copyright 2026 Evie. P. <evieepy@gmail.com>, PythonistaGuild

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import annotations

import datetime
import inspect
import logging
from functools import wraps
from typing import TYPE_CHECKING, Any, Concatenate, ParamSpec, Self, TypeVar

import wavelink

from ._lib import VoiceProtocol
from .exceptions import InvalidPlayerState, InvalidTrackError, NodeNotFound
from .queue import Queue
from .tracks import Search, Track
from .utils import MISSING, VoiceUpdateCondition


if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from wavelink.enums import Source

    from ._lib import Client, Connectable, Guild, GuildVoiceStatePayload, VoiceChannel, VoiceServerUpdatePayload
    from .enums import EventType
    from .helpers import InactivityStrategy
    from .node import Node
    from .types_.rest import UpdatePlayerReqT
    from .types_.websocket import PlayerStateT, WebSocketClosedEventT


P = ParamSpec("P")
R = TypeVar("R")


LOGGER: logging.Logger = logging.getLogger(__name__)


def has_channel[**P, R](func: Callable[Concatenate[Any, P], Awaitable[R]]) -> Callable[Concatenate[Any, P], Awaitable[R]]:
    @wraps(func)
    async def wrapper(self: Any, *args: P.args, **kwargs: P.kwargs) -> R:
        if not self._guild or not self.channel:
            raise InvalidPlayerState("Unable to update player. No connected Voice Channel.")

        return await func(self, *args, **kwargs)

    return wrapper


class Player(VoiceProtocol):
    """Wavelink Player class which inherits from your libraries ``VoiceProtocol``.

    The :class:`~.Player` class is usually not constructed manually, instead you pass it to your libraries
    ``channel.connect(cls=wavelink.Player)`` method instead; e.g. :meth:`discord.VoiceChannel.connect`.

    Since the :class:`~.Player` requires a :class:`~.Node`, there are a few options available to allow
    :class:`~.Player` to work.

    - Use :class:`~.MusicBot`. This will automatically pass the best :class:`~.Node` to this player.

    - Use :class:`~.Pool` and assign it to your ``Client`` as the ``.wave`` attribute.
      This will automatically pass the best :class:`~.Node` to this player.

    - Use either :class:`~.Pool` or a standalone :class:`~.Node` and pass that to :meth:`discord.VoiceChannel.connect`.
      This will construct a :class:`~.Player` for you based on what you provide. e.g. ``Channel.connect(cls=self.node)``

    Players are unique to each :class:`discord.Guild`. You may only have one :class:`~.Player` connected per
    :class:`discord.Guild` at any given time.

    The :class:`~.Player` will automatically attempt to re-establish connection to discord in cases where disconnection
    was not intended. You should not and do not need to implement re-connection logic on this class. Doing so may interfere
    or conflict with the internal logic. If you would like to implement you own activity/inactivity checks on this player,
    please refer to :attr:`.inactivity_strategy`.

    .. note::

        Any :class:`~.MusicBot`, :class:`~.Pool` or :class:`~.Node` can be passed to :meth:`discord.VoiceChannel.connect`
        to create a :class:`~.Player` and assign it an appropriate :class:`~.Node`.

    Parameters
    ----------
    client: :class:`discord.Client`
        The :class:`discord.Client` currently running.
    channel: :class:`discord.Connectable`
        The voice channel this :class:`~.Player` has connected to.
    node: :class:`~.Node` | ``None``
        An optional :class:`~.Node` to pass to use for this :class:`~.Player`. Defaults to ``None``. See above for more
        details.
    """

    channel: VoiceChannel

    def __init__(self, client: Client, channel: Connectable, /, *, node: Node | None = None) -> None:
        super().__init__(client, channel)

        node = node or self._get_node()
        if not node:
            raise NodeNotFound(f"No Node was provided or could be found and used for {self!r}.")

        # Passing the Client to Node is optional; since we get Client here we can take advantage of this to set
        # Client if it was never originally set...
        if not node._client and client.application_id == node._client_id:
            node._client = client

        self._inactivity: InactivityStrategy | type[InactivityStrategy] | None = node._inactivity

        self._node: Node = node
        self._guild: Guild | None = None
        self._guild_id: int | None = None

        self._condition = VoiceUpdateCondition()
        self._should_reconnect = MISSING

        self._volume: int = 100
        self._is_playing: bool = False
        self._is_paused: bool = False
        self._is_deaf: bool = False
        self._is_mute: bool = False
        self._lava_connected: bool = False
        self._ping: int = -1
        self._position: int = 0
        self._last_update: int | None = 0

        self.queue: Queue = Queue()

    def __repr__(self) -> str:
        return f"Player(guild={self._guild}, channel={self.channel})"

    @classmethod
    def factory(cls, client: Client, channel: Connectable, *args: Any, **kwargs: Any) -> Self:
        # NOTE: Allows customizing the player when passed to Channel.connect(cls=...)
        return cls(client, channel, *args, **kwargs)

    @property
    def node(self) -> Node:
        """Property returning the :class:`~.Node` associated with the player.

        Returns
        -------
        Node
        """
        return self._node

    @property
    def guild(self) -> Guild | None:
        """Property returning the :class:`~discord.Guild` associated with the player.

        Returns
        -------
        discord.Guild
        """
        return self._guild

    @property
    def volume(self) -> int:
        """Property returning the current volume of the player. Defaults to ``100``.

        Returns
        -------
        int
        """
        return self._volume

    @property
    def ping(self) -> int:
        """Property returning the ping of Lavalink to Discord.

        If the ping is ``-1`` the player is disconnected.

        Returns
        -------
        int
        """
        return self._ping

    @property
    def position(self) -> int:
        """Property returning the current playing track position in ``ms``.

        Returns
        -------
        int
        """
        return self._position

    @property
    def last_update(self) -> datetime.datetime | None:
        """Property return the datetime the player was last updated via Lavalink.

        Could be ``None`` if the player has not been updated.

        Returns
        -------
        datetime.datetime
            The time the player was last updated.
        None
            The player has not been updated.
        """
        return datetime.datetime.fromtimestamp(self._last_update) if self._last_update else None

    @property
    def is_playing(self) -> bool:
        """Property returning a :class:`bool` indicating whether the player is currently playing a track.

        .. note::

            Pausing the player has no effect on this property.

        Returns
        -------
        bool
        """
        return self._is_playing

    @property
    def is_paused(self) -> bool:
        """Property returning a :class:`bool` indicating whether the player is currently paused.

        Returns
        -------
        bool
        """
        return self._is_paused

    @property
    def is_deaf(self) -> bool:
        """Property returning a :class:`bool` indicating whether the player is currently self deafened.

        Returns
        -------
        bool
        """
        return self._is_deaf

    @property
    def is_mute(self) -> bool:
        """Property returning a :class:`bool` indicating whether the player is self muted.

        .. note::

            This is not the same as turning down the volume to ``0``.

        Returns
        -------
        bool
        """
        return self._is_mute

    @property
    def inactivity_strategy(self) -> InactivityStrategy | type[InactivityStrategy] | None:
        return self._inactivity

    @inactivity_strategy.setter
    def inactivity_strategy(self, value: InactivityStrategy | type[InactivityStrategy] | None) -> None:
        self._inactivity = value

    async def _event_dispatched(self, event: EventType) -> None:
        if self._inactivity is None:
            return

        inst = self._inactivity() if inspect.isclass(self._inactivity) else self._inactivity
        if not await inst.check(self, event):
            return

        await inst.action(self, event)

    def _get_node(self) -> Node | None:
        if isinstance(self.client, wavelink.MusicBot):
            return self.client.get_node()

        pool = getattr(self, "wave", getattr(self, "pool", None))
        if not pool:
            return

        if not isinstance(pool, wavelink.Pool):
            return

        try:
            return pool.get_node()
        except Exception:
            pass

    async def _node_close(self, data: WebSocketClosedEventT) -> None: ...

    def _lavalink_update(self, data: PlayerStateT) -> None:
        self._lava_connected = data["connected"]
        self._ping = data["ping"]
        self._position = data["position"]
        self._last_update = data["time"]

    async def on_voice_server_update(self, data: VoiceServerUpdatePayload) -> None:
        endpoint = data["endpoint"]
        if not endpoint:
            return

        guild_id = int(data.get("guild_id", 0))
        guild = self.client.get_guild(guild_id)
        self._guild_id = guild_id

        if guild:
            self._guild = guild

        self._condition.endpoint = endpoint
        self._condition.token = data["token"]

        await self._dispatch_voice()

    async def on_voice_state_update(self, data: GuildVoiceStatePayload) -> None:
        channel_id = str(data["channel_id"]) if data["channel_id"] else None

        if not channel_id:
            return await self.destroy()

        if self._guild:
            self.channel = self._guild.get_channel(int(channel_id))  # type: ignore

        original = self._condition.channelId
        self._condition.channelId = channel_id
        self._condition.sessionId = data["session_id"]

        self._is_deaf = data["self_deaf"]
        self._is_mute = data["self_mute"]

        if original != channel_id:
            await self._dispatch_voice()

    async def _dispatch_voice(self) -> None:
        if self._condition.waiting:
            return

        await self._condition.wait()
        assert self._guild_id

        data: UpdatePlayerReqT = {"voice": self._condition.as_dict()}
        await self._node.update_player(self._guild_id, data=data)

    async def connect(
        self,
        *,
        timeout: float = 10.0,
        reconnect: bool = True,
        self_deaf: bool = False,
        self_mute: bool = False,
    ) -> None:
        if self.channel is MISSING:
            raise InvalidPlayerState(f"No valid channel could be found to connect for {self!r}.")

        if not self._guild:
            self._guild = self.channel.guild

        self._should_reconnect = reconnect
        async with self._condition.timeout(timeout):
            await self._guild.change_voice_state(channel=self.channel, self_mute=self_mute, self_deaf=self_deaf)

        self._node._players[self._guild.id] = self

    @has_channel
    async def disconnect(self, *, force: bool = False) -> None:  # type: ignore
        await self.destroy()

    async def destroy(self) -> None:
        assert self._guild_id
        node = self._node

        if self._guild:
            try:
                await self._guild.change_voice_state(channel=None)
            except Exception as e:
                LOGGER.debug("Unable to disconnect player. Possibly already disconnected: %s. Disregarding.", e)

        if node.get_player(self._guild_id):
            try:
                await node.destroy_player(self._guild_id)
            except Exception as e:
                LOGGER.debug("Unable to destroy player on Lavalink: %s. Disregarding.", e)

        node._players.pop(self._guild_id, None)
        self._condition.reset()
        self.queue.clear()

        super().cleanup()
        LOGGER.debug("Successfully disconnected and destroyed player %r.", self)

    @has_channel
    async def play(
        self,
        track: Track | Search,
        *,
        volume: int | None = None,
        paused: bool | None = None,
        replace: bool = True,
    ) -> None:
        assert self._guild
        playable = track.first if isinstance(track, Search) else track

        if not playable:
            raise InvalidTrackError(
                f"Could not determine playable from {track}. Excpected {type(Track).__name__!r}, got {playable!r}."
            )

        data: UpdatePlayerReqT = {
            "endTime": playable.end,
            "position": playable.start,
            "track": {"encoded": playable.encoded},
        }

        if volume is not None:
            data["volume"] = volume
        if paused is not None:
            data["paused"] = paused

        await self._node.update_player(self._guild.id, data=data, no_replace=not replace)

    @has_channel
    async def search_play(
        self,
        search: str,
        *,
        source: Source,
        volume: int | None = None,
        paused: bool | None = None,
        replace: bool = True,
    ) -> Track:
        """|coro|

        Method to search for and play a track with the provided search term.

        Unlike :meth:`.play` you do not pass a :class:`~.wavelink.Track`; rather a search term to lookup and directly play a
        track from.

        This method is useful when receving a :class:`~.wavelink.Track` before making a play request is not required.

        .. versionadded:: 4.0.0

        Parameters
        ----------
        search: str
            The search to use to search for and play a track, provided a track is found.
        source: :class:`~.wavelink.Source`
            The source to use to execute the search. Defaults to :attr:`~.wavelink`
        volume: int | None
            An optional :class:`int` of a volume between ``1`` and ``1000`` to set when starting the track.
            Defaults to ``None`` which keeps the currently set volume.
        paused: bool | None
            An optional :class:`bool` indicating whether the player should be placed into or out of a paused state
            upon loading this track. Defaults to ``None`` which keeps the player in the current pause state.
        replace: bool
            An optional :class:`bool` indicating whether to directly replace the currently playing track. If set to
            ``False``, the player will not start playing the requested track if a track is currently playing.
            Defaults to ``True``.

        Raises
        ------
        HTTPException
            An error occurred making the play request to Lavalink.
        LavalinkException
            An error occurred on Lavalink.
        """
        assert self._guild

        result = await self._node.search(search)
        playable = result.first

        if not playable:
            raise InvalidTrackError(f"Could not find tracks for search {search!r}. {result} was empty.")

        data: UpdatePlayerReqT = {
            "endTime": playable.end,
            "position": playable.start,
            "track": {"encoded": playable.encoded},
        }

        if volume is not None:
            data["volume"] = volume
        if paused is not None:
            data["paused"] = paused

        await self._node.update_player(self._guild.id, data=data, no_replace=not replace)
        return playable

    @has_channel
    async def direct_play(
        self,
        *,
        identifier: str | None = None,
        encoded: str | None = None,
        volume: int | None = None,
        paused: bool | None = None,
        replace: bool = True,
    ) -> None:
        """|coro|

        Method to start playing a track directly based on the provided ``identifier`` or ``encoded`` parameters.

        Unlike :meth:`.play` you do not pass a :class:`~wavelink.Track`; rather the encoded or identifier string received via
        Lavalink.

        This method is useful for applications that store track data persistently.

        .. note::

            Only one of ``identifier`` or ``encoded`` can be passed.

        .. versionadded:: 4.0.0

        Parameters
        ----------
        identifier: str | None
            An optional :class:`str`, which is the identifier of the track as received via Lavalink. Defaults to ``None``.
            If this parameter is not passed or ``None``, ``encoded`` must be used.
        encoded: str | None
            An optional :class:`str`, which is the encoded string o the track received via Lavalink. Defaults to ``None``.
            If this parameter is not passed or ``None``, ``identifier`` must be used.
        volume: int | None
            An optional :class:`int` of a volume between ``1`` and ``1000`` to set when starting the track.
            Defaults to ``None`` which keeps the currently set volume.
        paused: bool | None
            An optional :class:`bool` indicating whether the player should be placed into or out of a paused state
            upon loading this track. Defaults to ``None`` which keeps the player in the current pause state.
        replace: bool
            An optional :class:`bool` indicating whether to directly replace the currently playing track. If set to
            ``False``, the player will not start playing the requested track if a track is currently playing.
            Defaults to ``True``.

        Raises
        ------
        HTTPException
            An error occurred making the play request to Lavalink.
        LavalinkException
            An error occurred on Lavalink.
        """
        assert self._guild

        if not identifier and not encoded:
            raise ValueError("The 'identifier' and 'encoded' parameters are missing. One must be provided.")
        elif identifier and encoded:
            raise ValueError("Only one of 'indentifier' and 'encoded' can be provided.")

        data: UpdatePlayerReqT = {"track": {}}

        if encoded:
            data["track"]["encoded"] = encoded
        elif identifier:
            data["track"]["identifier"] = identifier

        if volume is not None:
            data["volume"] = volume
        if paused is not None:
            data["paused"] = paused

        await self._node.update_player(self._guild.id, data=data, no_replace=not replace)

    @has_channel
    async def pause(self) -> None:
        """|coro|

        Method which pauses the player.

        .. note::

            This method will cause the player to be in a paused state; even if no track is currently playing.

        .. versionchanged:: 4.0.0

            This method no longer accepts a bool and no longer acts as a toggle.

        Raises
        ------
        HTTPException
            The request to pause the song failed.
        """
        assert self._guild

        if self._is_paused:
            return

        data: UpdatePlayerReqT = {"paused": True}
        await self._node.update_player(self._guild.id, data=data)
        self._is_paused = True

    @has_channel
    async def resume(self) -> None:
        """|coro|

        Method which resumes playback of the player.

        .. versionadded:: 4.0.0

        Raises
        ------
        HTTPException
            The request to resume the player failed.
        """
        assert self._guild

        if not self._is_paused:
            return

        data: UpdatePlayerReqT = {"paused": False}
        await self._node.update_player(self._guild.id, data=data)
        self._is_paused = False

    @has_channel
    async def toggle_pause(self) -> None:
        """|coro|

        Method to toggle the pause state of the player.

        Unlike :meth:`.pause` and :meth:`.resume` this method instead acts as a switch between the two states.

        .. versionadded:: 4.0.0
        """
        assert self._guild

        paused = not self._is_paused
        data: UpdatePlayerReqT = {"paused": paused}

        await self._node.update_player(self._guild.id, data=data)
        self._is_paused = paused

    @has_channel
    async def skip(self) -> None:
        """|coro|

        Method which skips the currently playing :class:`~.wavelink.Track`. If no track is in the queue, the
        :class:`~wavelink.Player` is effectively stopped.

        .. note::

            A new :class:`~.wavelink.Track` should not be started automatically after skip is called.

        .. versionchanged:: 4.0.0

            This method now truly "skips" a track insted of simply stopping the player.

        Raises
        ------
        HTTPException
            The request to skip the track failed.
        """
        assert self._guild_id

        encoded: str | None = f"{self.queue.get():b64}" if self.queue else None
        data: UpdatePlayerReqT = {"track": {"encoded": encoded}}

        await self.node.update_player(self._guild_id, data=data, no_replace=False)

    @has_channel
    async def stop(self) -> None:
        """|coro|

        Method to stop the currently playing :class:`~.wavelink.Track`.

        .. note::

            A new :class:`~.wavelink.Track` should not be started automatically after stop is called.

        Raises
        ------
        HTTPException
            The request to stop the player failed.
        """
        assert self._guild_id

        data: UpdatePlayerReqT = {"track": {"encoded": None}}
        await self.node.update_player(self._guild_id, data=data, no_replace=False)

    @has_channel
    async def set_volume(self, volume: int = 100, /) -> int:
        """|coro|

        Method to set the volume of the :class:`~wavelink.Player`.

        Parameters
        ----------
        volume: int
            The new volume of the :class:`~wavelink.Player`. Must be between ``1`` and ``1000``.


        Returns
        -------
        int
            The volume before the player was updated.

        Raises
        -------
        HTTPException
            The request to update the volume failed.
        ValueError
            The ``volume`` parameter must be an :class:`int` between ``1`` and ``1000``.
        """
        assert self._guild

        if not 0 <= volume <= 1000:
            raise ValueError(f"'volume' parameter must be an integer between 1 and 1000. Got {volume}.")

        data: UpdatePlayerReqT = {"volume": volume}
        old = self._volume

        await self._node.update_player(self._guild.id, data=data)
        self._volume = volume

        return old

    @has_channel
    async def mute(self) -> None:
        """|coro|

        Method which self mutes the :class:`~wavelink.Player`.

        .. versionadded: 4.0.0

        Raises
        ------
        discord.HTTPException
            The request to self mute failed.
        """
        assert self._guild and self.channel
        if self._is_mute:
            return

        await self._guild.change_voice_state(channel=self.channel, self_mute=True, self_deaf=self._is_deaf)

    @has_channel
    async def deafen(self) -> None:
        """|coro|

        Method which self deafens the :class:`~wavelink.Player`.

        .. versionadded:: 4.0.0

        Raises
        ------
        discord.HTTPException
            The request to self deafen failed.
        """
        assert self._guild and self.channel
        if self._is_deaf:
            return

        await self._guild.change_voice_state(channel=self.channel, self_deaf=True, self_mute=self._is_mute)

    @has_channel
    async def move(
        self,
        channel: VoiceChannel,
        *,
        timeout: float = 10.0,
        self_deaf: bool | None = None,
        self_mute: bool | None = None,
    ) -> None:
        """|coro|

        Method which attempts to move a currently connected :class:`~.wavelink.Player` to the provided channel.

        .. note::

            :meth:`.move_to` is an alias to this method.

        Parameters
        ----------
        channel: :class:`discord.VoiceChannel`
            The channel to move the :class:`~wavelink.Player` to.
        timeout: float
            The amount of seconds before the request will timeout. Defaults to ``10.0``.
        self_deaf: bool | None
            Whether the :class:`~wavelink.Player` should be deafened on move. Defaults to ``None`` which keeps the current
            state.
        self_mute: bool | None
            Whether the :class:`~wavelink.Player` should be muted on move. Defaults to ``None`` which keeps the current
            state.

        Raises
        ------
        TimeoutError
            Moving to the provided channel failed.
        discord.HTTPException
            The request to move to the provided chanel failed.
        """
        assert self._guild
        if self.channel.id == channel.id:
            return

        async with self._condition.timeout(timeout):
            await self._guild.change_voice_state(
                channel=channel,
                self_mute=self_mute or self._is_mute,
                self_deaf=self_deaf or self._is_deaf,
            )

        self._node._players[self._guild.id] = self

    move_to = move
