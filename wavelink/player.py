"""
MIT License

Copyright (c) 2019-Current PythonistaGuild, EvieePy

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from __future__ import annotations

import asyncio
import logging
import random
import time
from collections import deque
from typing import TYPE_CHECKING, Any, TypeAlias

import async_timeout
import discord
from discord.abc import Connectable
from discord.utils import MISSING

import wavelink

from .enums import AutoPlayMode, NodeStatus, QueueMode
from .exceptions import (
    ChannelTimeoutException,
    InvalidChannelStateException,
    LavalinkException,
    LavalinkLoadException,
    QueueEmpty,
)
from .filters import Filters
from .node import Pool
from .payloads import PlayerUpdateEventPayload, TrackEndEventPayload
from .queue import Queue
from .tracks import Playable, Playlist

if TYPE_CHECKING:
    from discord.types.voice import GuildVoiceState as GuildVoiceStatePayload
    from discord.types.voice import VoiceServerUpdate as VoiceServerUpdatePayload
    from typing_extensions import Self

    from .node import Node
    from .types.request import Request as RequestPayload
    from .types.state import PlayerVoiceState, VoiceState

    VocalGuildChannel = discord.VoiceChannel | discord.StageChannel

logger: logging.Logger = logging.getLogger(__name__)


T_a: TypeAlias = list[Playable] | Playlist


class Player(discord.VoiceProtocol):
    """The Player is a :class:`discord.VoiceProtocol` used to connect your :class:`discord.Client` to a
    :class:`discord.VoiceChannel`.

    The player controls the music elements of the bot including playing tracks, the queue, connecting etc.
    See Also: The various methods available.

    .. note::

        Since the Player is a :class:`discord.VoiceProtocol`, it is attached to the various ``voice_client`` attributes
        in discord.py, including ``guild.voice_client``, ``ctx.voice_client`` and ``interaction.voice_client``.
    """

    channel: VocalGuildChannel

    def __call__(self, client: discord.Client, channel: VocalGuildChannel) -> Self:
        super().__init__(client, channel)

        self._guild = channel.guild

        return self

    def __init__(
        self, client: discord.Client = MISSING, channel: Connectable = MISSING, *, nodes: list[Node] | None = None
    ) -> None:
        super().__init__(client, channel)

        self.client: discord.Client = client
        self._guild: discord.Guild | None = None

        self._voice_state: PlayerVoiceState = {"voice": {}}

        self._node: Node
        if not nodes:
            self._node = Pool.get_node()
        else:
            self._node = sorted(nodes, key=lambda n: len(n.players))[0]

        if self.client is MISSING and self.node.client:
            self.client = self.node.client

        self._last_update: int | None = None
        self._last_position: int = 0
        self._ping: int = -1

        self._connected: bool = False
        self._connection_event: asyncio.Event = asyncio.Event()

        self._current: Playable | None = None
        self._original: Playable | None = None
        self._previous: Playable | None = None

        self.queue: Queue = Queue()
        self.auto_queue: Queue = Queue()

        self._volume: int = 100
        self._paused: bool = False

        self._auto_cutoff: int = 20
        self._auto_weight: int = 3
        self._previous_seeds_cutoff: int = self._auto_cutoff * self._auto_weight
        self._history_count: int | None = None

        self._autoplay: AutoPlayMode = AutoPlayMode.disabled
        self.__previous_seeds: asyncio.Queue[str] = asyncio.Queue(maxsize=self._previous_seeds_cutoff)

        self._auto_lock: asyncio.Lock = asyncio.Lock()
        self._error_count: int = 0

        self._filters: Filters = Filters()

    async def _auto_play_event(self, payload: TrackEndEventPayload) -> None:
        if self._autoplay is AutoPlayMode.disabled:
            return

        if self._error_count >= 3:
            logger.warning(
                "AutoPlay was unable to continue as you have received too many consecutive errors."
                "Please check the error log on Lavalink."
            )
            return

        if payload.reason == "replaced":
            self._error_count = 0
            return

        elif payload.reason == "loadFailed":
            self._error_count += 1

        else:
            self._error_count = 0

        if self.node.status is not NodeStatus.CONNECTED:
            logger.warning(f'"Unable to use AutoPlay on Player for Guild "{self.guild}" due to disconnected Node.')
            return

        if not isinstance(self.queue, Queue) or not isinstance(self.auto_queue, Queue):  # type: ignore
            logger.warning(f'"Unable to use AutoPlay on Player for Guild "{self.guild}" due to unsupported Queue.')
            return

        if self.queue.mode is QueueMode.loop:
            await self._do_partial(history=False)

        elif self.queue.mode is QueueMode.loop_all:
            await self._do_partial()

        elif self._autoplay is AutoPlayMode.partial or self.queue:
            await self._do_partial()

        elif self._autoplay is AutoPlayMode.enabled:
            async with self._auto_lock:
                await self._do_recommendation()

    async def _do_partial(self, *, history: bool = True) -> None:
        if self._current is None:
            try:
                track: Playable = self.queue.get()
            except QueueEmpty:
                return

            await self.play(track, add_history=history)

    async def _do_recommendation(self):
        assert self.guild is not None
        assert self.queue.history is not None and self.auto_queue.history is not None

        if len(self.auto_queue) > self._auto_cutoff + 1:
            track: Playable = self.auto_queue.get()
            self.auto_queue.history.put(track)

            await self.play(track, add_history=False)
            return

        weighted_history: list[Playable] = self.queue.history[::-1][: max(5, 5 * self._auto_weight)]
        weighted_upcoming: list[Playable] = self.auto_queue[: max(3, int((5 * self._auto_weight) / 3))]
        choices: list[Playable | None] = [*weighted_history, *weighted_upcoming, self._current, self._previous]

        # Filter out tracks which are None...
        _previous: deque[str] = self.__previous_seeds._queue  # type: ignore
        seeds: list[Playable] = [t for t in choices if t is not None and t.identifier not in _previous]
        random.shuffle(seeds)

        spotify: list[str] = [t.identifier for t in seeds if t.source == "spotify"]
        youtube: list[str] = [t.identifier for t in seeds if t.source == "youtube"]

        spotify_query: str | None = None
        youtube_query: str | None = None

        count: int = len(self.queue.history)
        changed_by: int = min(3, count) if self._history_count is None else count - self._history_count

        if changed_by > 0:
            self._history_count = count

        changed_history: list[Playable] = self.queue.history[::-1]

        added: int = 0
        for i in range(min(changed_by, 3)):
            track: Playable = changed_history[i]

            if added == 2 and track.source == "spotify":
                break

            if track.source == "spotify":
                spotify.insert(0, track.identifier)
                added += 1

            elif track.source == "youtube":
                youtube[0] = track.identifier

        if spotify:
            spotify_seeds: list[str] = spotify[:3]
            spotify_query = f"sprec:seed_tracks={','.join(spotify_seeds)}&limit=10"

            for s_seed in spotify_seeds:
                self._add_to_previous_seeds(s_seed)

        if youtube:
            ytm_seed: str = youtube[0]
            youtube_query = f"https://music.youtube.com/watch?v={ytm_seed}8&list=RD{ytm_seed}"
            self._add_to_previous_seeds(ytm_seed)

        async def _search(query: str | None) -> T_a:
            if query is None:
                return []

            try:
                search: wavelink.Search = await Pool.fetch_tracks(query)
            except (LavalinkLoadException, LavalinkException):
                return []

            if not search:
                return []

            tracks: list[Playable]
            if isinstance(search, Playlist):
                tracks = search.tracks.copy()
            else:
                tracks = search

            return tracks

        results: tuple[T_a, T_a] = await asyncio.gather(_search(spotify_query), _search(youtube_query))

        # track for result in results for track in result...
        filtered_r: list[Playable] = [t for r in results for t in r]

        if not filtered_r:
            logger.debug(f'Player "{self.guild.id}" could not load any songs via AutoPlay.')
            return

        if not self._current:
            now: Playable = filtered_r.pop(1)
            now._recommended = True
            self.auto_queue.history.put(now)

            await self.play(now, add_history=False)

        # Possibly adjust these thresholds?
        history: list[Playable] = (
            self.auto_queue[:40] + self.queue[:40] + self.queue.history[:-41:-1] + self.auto_queue.history[:-61:-1]
        )

        added: int = 0
        for track in filtered_r:
            if track in history:
                continue

            track._recommended = True
            added += await self.auto_queue.put_wait(track)

        random.shuffle(self.auto_queue._queue)
        logger.debug(f'Player "{self.guild.id}" added "{added}" tracks to the auto_queue via AutoPlay.')

    @property
    def autoplay(self) -> AutoPlayMode:
        """A property which returns the :class:`wavelink.AutoPlayMode` the player is currently in.

        This property can be set with any :class:`wavelink.AutoPlayMode` enum value.


        .. versionchanged:: 3.0.0

            This property now accepts and returns a :class:`wavelink.AutoPlayMode` enum value.
        """
        return self._autoplay

    @autoplay.setter
    def autoplay(self, value: Any) -> None:
        if not isinstance(value, AutoPlayMode):
            raise ValueError("Please provide a valid 'wavelink.AutoPlayMode' to set.")

        self._autoplay = value

    @property
    def node(self) -> Node:
        """The :class:`Player`'s currently selected :class:`Node`.


        .. versionchanged:: 3.0.0

            This property was previously known as ``current_node``.
        """
        return self._node

    @property
    def guild(self) -> discord.Guild | None:
        """Returns the :class:`Player`'s associated :class:`discord.Guild`.

        Could be None if this :class:`Player` has not been connected.
        """
        return self._guild

    @property
    def connected(self) -> bool:
        """Returns a bool indicating if the player is currently connected to a voice channel.

        .. versionchanged:: 3.0.0

            This property was previously known as ``is_connected``.
        """
        return self.channel and self._connected

    @property
    def current(self) -> Playable | None:
        """Returns the currently playing :class:`~wavelink.Playable` or None if no track is playing."""
        return self._current

    @property
    def volume(self) -> int:
        """Returns an int representing the currently set volume, as a percentage.

        See: :meth:`set_volume` for setting the volume.
        """
        return self._volume

    @property
    def filters(self) -> Filters:
        """Property which returns the :class:`~wavelink.Filters` currently assigned to the Player.

        See: :meth:`~wavelink.Player.set_filters` for setting the players filters.

        .. versionchanged:: 3.0.0

            This property was previously known as ``filter``.
        """
        return self._filters

    @property
    def paused(self) -> bool:
        """Returns the paused status of the player. A currently paused player will return ``True``.

        See: :meth:`pause` and :meth:`play` for setting the paused status.
        """
        return self._paused

    @property
    def ping(self) -> int:
        """Returns the ping in milliseconds as int between your connected Lavalink Node and Discord (Players Channel).

        Returns ``-1`` if no player update event has been received or the player is not connected.
        """
        return self._ping

    @property
    def playing(self) -> bool:
        """Returns whether the :class:`~Player` is currently playing a track and is connected.

        Due to relying on validation from Lavalink, this property may in some cases return ``True`` directly after
        skipping/stopping a track, although this is not the case when disconnecting the player.

        This property will return ``True`` in cases where the player is paused *and* has a track loaded.

        .. versionchanged:: 3.0.0

            This property used to be known as the `is_playing()` method.
        """
        return self._connected and self._current is not None

    @property
    def position(self) -> int:
        """Returns the position of the currently playing :class:`~wavelink.Playable` in milliseconds.

        This property relies on information updates from Lavalink.

        In cases there is no :class:`~wavelink.Playable` loaded or the player is not connected,
        this property will return ``0``.

        This property will return ``0`` if no update has been received from Lavalink.

        .. versionchanged:: 3.0.0

            This property now uses a monotonic clock.
        """
        if self.current is None or not self.playing:
            return 0

        if not self.connected:
            return 0

        if self._last_update is None:
            return 0

        if self.paused:
            return self._last_position

        position: int = int((time.monotonic_ns() - self._last_update) / 1000000) + self._last_position
        return min(position, self.current.length)

    async def _update_event(self, payload: PlayerUpdateEventPayload) -> None:
        # Convert nanoseconds into milliseconds...
        self._last_update = time.monotonic_ns()
        self._last_position = payload.position

        self._ping = payload.ping

    async def on_voice_state_update(self, data: GuildVoiceStatePayload, /) -> None:
        channel_id = data["channel_id"]

        if not channel_id:
            await self._destroy()
            return

        self._connected = True

        self._voice_state["voice"]["session_id"] = data["session_id"]
        self.channel = self.client.get_channel(int(channel_id))  # type: ignore

    async def on_voice_server_update(self, data: VoiceServerUpdatePayload, /) -> None:
        self._voice_state["voice"]["token"] = data["token"]
        self._voice_state["voice"]["endpoint"] = data["endpoint"]

        await self._dispatch_voice_update()

    async def _dispatch_voice_update(self) -> None:
        assert self.guild is not None
        data: VoiceState = self._voice_state["voice"]

        try:
            session_id: str = data["session_id"]
            token: str = data["token"]
        except KeyError:
            return

        endpoint: str | None = data.get("endpoint", None)
        if not endpoint:
            return

        request: RequestPayload = {"voice": {"sessionId": session_id, "token": token, "endpoint": endpoint}}

        try:
            await self.node._update_player(self.guild.id, data=request)
        except LavalinkException:
            await self.disconnect()
        else:
            self._connection_event.set()

        logger.debug(f"Player {self.guild.id} is dispatching VOICE_UPDATE.")

    async def connect(
        self, *, timeout: float = 10.0, reconnect: bool, self_deaf: bool = False, self_mute: bool = False
    ) -> None:
        """

        .. warning::

            Do not use this method directly on the player. See: :meth:`discord.VoiceChannel.connect` for more details.


        Pass the :class:`wavelink.Player` to ``cls=`` in :meth:`discord.VoiceChannel.connect`.


        Raises
        ------
        ChannelTimeoutException
            Connecting to the voice channel timed out.
        InvalidChannelStateException
            You tried to connect this player without an appropriate voice channel.
        """
        if self.channel is MISSING:
            msg: str = 'Please use "discord.VoiceChannel.connect(cls=...)" and pass this Player to cls.'
            raise InvalidChannelStateException(f"Player tried to connect without a valid channel: {msg}")

        if not self._guild:
            self._guild = self.channel.guild
            self.node._players[self._guild.id] = self

        assert self.guild is not None
        await self.guild.change_voice_state(channel=self.channel, self_mute=self_mute, self_deaf=self_deaf)

        try:
            async with async_timeout.timeout(timeout):
                await self._connection_event.wait()
        except (asyncio.TimeoutError, asyncio.CancelledError):
            msg = f"Unable to connect to {self.channel} as it exceeded the timeout of {timeout} seconds."
            raise ChannelTimeoutException(msg)

    async def move_to(
        self,
        channel: VocalGuildChannel | None,
        *,
        timeout: float = 10.0,
        self_deaf: bool | None = None,
        self_mute: bool | None = None,
    ) -> None:
        """Method to move the player to another channel.

        Parameters
        ----------
        channel: :class:`discord.VoiceChannel` | :class:`discord.StageChannel`
            The new channel to move to.
        timeout: float
            The timeout in ``seconds`` before raising. Defaults to 10.0.
        self_deaf: bool | None
            Whether to deafen when moving. Defaults to ``None`` which keeps the current setting or ``False``
            if they can not be determined.
        self_mute: bool | None
            Whether to self mute when moving. Defaults to ``None`` which keeps the current setting or ``False``
            if they can not be determined.

        Raises
        ------
        ChannelTimeoutException
            Connecting to the voice channel timed out.
        InvalidChannelStateException
            You tried to connect this player without an appropriate guild.
        """
        if not self.guild:
            raise InvalidChannelStateException("Player tried to move without a valid guild.")

        self._connection_event.clear()
        voice: discord.VoiceState | None = self.guild.me.voice

        if self_deaf is None and voice:
            self_deaf = voice.self_deaf

        if self_mute is None and voice:
            self_mute = voice.self_mute

        self_deaf = bool(self_deaf)
        self_mute = bool(self_mute)

        await self.guild.change_voice_state(channel=channel, self_mute=self_mute, self_deaf=self_deaf)

        if channel is None:
            return

        try:
            async with async_timeout.timeout(timeout):
                await self._connection_event.wait()
        except (asyncio.TimeoutError, asyncio.CancelledError):
            msg = f"Unable to connect to {channel} as it exceeded the timeout of {timeout} seconds."
            raise ChannelTimeoutException(msg)

    async def play(
        self,
        track: Playable,
        *,
        replace: bool = True,
        start: int = 0,
        end: int | None = None,
        volume: int | None = None,
        paused: bool | None = None,
        add_history: bool = True,
        filters: Filters | None = None,
    ) -> Playable:
        """Play the provided :class:`~wavelink.Playable`.

        Parameters
        ----------
        track: :class:`~wavelink.Playable`
            The track to being playing.
        replace: bool
            Whether this track should replace the currently playing track, if there is one. Defaults to ``True``.
        start: int
            The position to start playing the track at in milliseconds.
            Defaults to ``0`` which will start the track from the beginning.
        end: Optional[int]
            The position to end the track at in milliseconds.
            Defaults to ``None`` which means this track will play until the very end.
        volume: Optional[int]
            Sets the volume of the player. Must be between ``0`` and ``1000``.
            Defaults to ``None`` which will not change the current volume.
            See Also: :meth:`set_volume`
        paused: bool | None
            Whether the player should be paused, resumed or retain current status when playing this track.
            Setting this parameter to ``True`` will pause the player. Setting this parameter to ``False`` will
            resume the player if it is currently paused. Setting this parameter to ``None`` will not change the status
            of the player. Defaults to ``None``.
        add_history: Optional[bool]
            If this argument is set to ``True``, the :class:`~Player` will add this track into the
            :class:`wavelink.Queue` history, if loading the track was successful. If ``False`` this track will not be
            added to your history. This does not directly affect the ``AutoPlay Queue`` but will alter how ``AutoPlay``
            recommends songs in the future. Defaults to ``True``.
        filters: Optional[:class:`~wavelink.Filters`]
            An Optional[:class:`~wavelink.Filters`] to apply when playing this track. Defaults to ``None``.
            If this is ``None`` the currently set filters on the player will be applied.


        Returns
        -------
        :class:`~wavelink.Playable`
            The track that began playing.


        .. versionchanged:: 3.0.0

            Added the ``paused`` parameter. Parameters ``replace``, ``start``, ``end``, ``volume`` and ``paused``
            are now all keyword-only arguments.

            Added the ``add_history`` keyword-only argument.

            Added the ``filters`` keyword-only argument.
        """
        assert self.guild is not None

        original_vol: int = self._volume
        vol: int = volume or self._volume

        if vol != self._volume:
            self._volume = vol

        if replace or not self._current:
            self._current = track
            self._original = track

        old_previous = self._previous
        self._previous = self._current

        pause: bool
        if paused is not None:
            pause = paused
        else:
            pause = self._paused

        if filters:
            self._filters = filters

        request: RequestPayload = {
            "track": {"encoded": track.encoded, "userData": dict(track.extras)},
            "volume": vol,
            "position": start,
            "endTime": end,
            "paused": pause,
            "filters": self._filters(),
        }

        try:
            await self.node._update_player(self.guild.id, data=request, replace=replace)
        except LavalinkException as e:
            self._current = None
            self._original = None
            self._previous = old_previous
            self._volume = original_vol
            raise e

        self._paused = pause

        if add_history:
            assert self.queue.history is not None
            self.queue.history.put(track)

        return track

    async def pause(self, value: bool, /) -> None:
        """Set the paused or resume state of the player.

        Parameters
        ----------
        value: bool
            A bool indicating whether the player should be paused or resumed. True indicates that the player should be
            ``paused``. False will resume the player if it is currently paused.


        .. versionchanged:: 3.0.0

            This method now expects a positional-only bool value. The ``resume`` method has been removed.
        """
        assert self.guild is not None

        request: RequestPayload = {"paused": value}
        await self.node._update_player(self.guild.id, data=request)

        self._paused = value

    async def seek(self, position: int = 0, /) -> None:
        """Seek to the provided position in the currently playing track, in milliseconds.

        Parameters
        ----------
        position: int
            The position to seek to in milliseconds. To restart the song from the beginning,
            you can disregard this parameter or set position to 0.


        .. versionchanged:: 3.0.0

            The ``position`` parameter is now positional-only, and has a default of 0.
        """
        assert self.guild is not None

        if not self._current:
            return

        request: RequestPayload = {"position": position}
        await self.node._update_player(self.guild.id, data=request)

    async def set_filters(self, filters: Filters | None = None, /, *, seek: bool = False) -> None:
        """Set the :class:`wavelink.Filters` on the player.

        Parameters
        ----------
        filters: Optional[:class:`~wavelink.Filters`]
            The filters to set on the player. Could be ```None`` to reset the currently applied filters.
            Defaults to ``None``.
        seek: bool
            Whether to seek immediately when applying these filters. Seeking uses more resources, but applies the
            filters immediately. Defaults to ``False``.


        .. versionchanged:: 3.0.0

            This method now accepts a positional-only argument of filters, which now defaults to None. Filters
            were redesigned in this version, see: :class:`wavelink.Filters`.


        .. versionchanged:: 3.0.0

            This method was previously known as ``set_filter``.
        """
        assert self.guild is not None

        if filters is None:
            filters = Filters()

        request: RequestPayload = {"filters": filters()}
        await self.node._update_player(self.guild.id, data=request)
        self._filters = filters

        if self.playing and seek:
            await self.seek(self.position)

    async def set_volume(self, value: int = 100, /) -> None:
        """Set the :class:`Player` volume, as a percentage, between 0 and 1000.

        By default, every player is set to 100 on creation. If a value outside 0 to 1000 is provided it will be
        clamped.

        Parameters
        ----------
        value: int
            A volume value between 0 and 1000. To reset the player to 100, you can disregard this parameter.


        .. versionchanged:: 3.0.0

            The ``value`` parameter is now positional-only, and has a default of 100.
        """
        assert self.guild is not None
        vol: int = max(min(value, 1000), 0)

        request: RequestPayload = {"volume": vol}
        await self.node._update_player(self.guild.id, data=request)

        self._volume = vol

    async def disconnect(self, **kwargs: Any) -> None:
        """Disconnect the player from the current voice channel and remove it from the :class:`~wavelink.Node`.

        This method will cause any playing track to stop and potentially trigger the following events:

            - ``on_wavelink_track_end``
            - ``on_wavelink_websocket_closed``


        .. warning::

            Please do not re-use a :class:`Player` instance that has been disconnected, unwanted side effects are
            possible.
        """
        assert self.guild

        await self._destroy()
        await self.guild.change_voice_state(channel=None)

    async def stop(self, *, force: bool = True) -> Playable | None:
        """An alias to :meth:`skip`.

        See Also: :meth:`skip` for more information.

        .. versionchanged:: 3.0.0

            This method is now known as ``skip``, but the alias ``stop`` has been kept for backwards compatability.
        """
        return await self.skip(force=force)

    async def skip(self, *, force: bool = True) -> Playable | None:
        """Stop playing the currently playing track.

        Parameters
        ----------
        force: bool
            Whether the track should skip looping, if :class:`wavelink.Queue` has been set to loop.
            Defaults to ``True``.

        Returns
        -------
        :class:`~wavelink.Playable` | None
            The currently playing track that was skipped, or ``None`` if no track was playing.


        .. versionchanged:: 3.0.0

            This method was previously known as ``stop``. To avoid confusion this method is now known as ``skip``.
            This method now returns the :class:`~wavelink.Playable` that was skipped.
        """
        assert self.guild is not None
        old: Playable | None = self._current

        if force:
            self.queue._loaded = None

        request: RequestPayload = {"track": {"encoded": None}}
        await self.node._update_player(self.guild.id, data=request, replace=True)

        return old

    def _invalidate(self) -> None:
        self._connected = False
        self._connection_event.clear()

        try:
            self.cleanup()
        except (AttributeError, KeyError):
            pass

    async def _destroy(self) -> None:
        assert self.guild

        self._invalidate()
        player: Player | None = self.node._players.pop(self.guild.id, None)

        if player:
            try:
                await self.node._destroy_player(self.guild.id)
            except LavalinkException:
                pass

    def _add_to_previous_seeds(self, seed: str) -> None:
        # Helper method to manage previous seeds.
        if self.__previous_seeds.full():
            self.__previous_seeds.get_nowait()
        self.__previous_seeds.put_nowait(seed)
