"""
MIT License

Copyright (c) 2019-Present PythonistaGuild

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

import datetime
import logging
from typing import TYPE_CHECKING, Any, Union

import discord
from discord.utils import MISSING

from .enums import *
from .ext import spotify
from .filters import Filter
from .node import Node, NodePool
from .payloads import TrackEventPayload
from .queue import Queue
from .tracks import *


if TYPE_CHECKING:
    from discord.types.voice import GuildVoiceState, VoiceServerUpdate
    from typing_extensions import Self

    from .types.events import PlayerState, PlayerUpdateOp
    from .types.request import EncodedTrackRequest, Request
    from .types.state import DiscordVoiceState

__all__ = ("Player",)


logger: logging.Logger = logging.getLogger(__name__)


VoiceChannel = Union[
    discord.VoiceChannel, discord.StageChannel
]  # todo: VocalGuildChannel?


class Player(discord.VoiceProtocol):
    """Wavelink Player class.

    This class is used as a :class:`discord.VoiceProtocol` and inherits all its members.


    .. note::

        The Player class come with an in-built queue. See :class:`queue.Queue`.

    Parameters
    ----------
    nodes: Optional[list[:class:`node.Node`]]
        An optional list of :class:`node.Node` to use with this Player. If no Nodes are provided
        the best connected Node will be used.
    swap_node_on_disconnect: bool
        If a list of :class:`node.Node` is provided the Player will swap Nodes on Node disconnect.
        Defaults to True.

    Attributes
    ----------
    client: :class:discord.Client`
        The discord Client or Bot associated with this Player.
    channel: :class:`discord.VoiceChannel`
        The channel this player is currently connected to.
    nodes: list[:class:`node.Node`]
        The list of Nodes this player is currently using.
    current_node: :class:`node.Node`
        The Node this player is currently using.
    queue: :class:`queue.Queue`
        The wavelink built in Queue. See :class:`queue.Queue`. This queue always takes precedence over the auto_queue.
        Meaning any songs in this queue will be played before auto_queue songs.
    auto_queue: :class:`queue.Queue`
        The built-in AutoPlay Queue. This queue keeps track of recommended songs only.
        When a song is retrieved from this queue in the AutoPlay event, it is added to the main Queue.history.
    filter: dict[:class:`str`, :class:`Any`]
        The current filters applied.
    """

    def __call__(self, client: discord.Client, channel: VoiceChannel) -> Self:
        self.client = client
        self.channel = channel

        return self

    def __init__(
        self,
        client: discord.Client = MISSING,
        channel: VoiceChannel = MISSING,
        *,
        nodes: list[Node] | None = None,
        swap_node_on_disconnect: bool = True
    ) -> None:
        self.client: discord.Client = client
        self.channel: VoiceChannel | None = channel

        self.nodes: list[Node]
        self.current_node: Node

        if swap_node_on_disconnect and not nodes:
            self.nodes = list(NodePool.nodes.values())
            self.current_node = self.nodes[0]
        elif nodes:
            self.current_node = nodes[0]
            self.nodes = nodes
        else:
            self.current_node = NodePool.get_connected_node()
            self.nodes = [self.current_node]

        if not self.client:
            if self.current_node.client is None:
                raise RuntimeError('')
            self.client = self.current_node.client

        self._guild: discord.Guild | None = None
        self._voice_state: DiscordVoiceState = {}
        self._player_state: dict[str, Any] = {}

        self.swap_on_disconnect: bool = swap_node_on_disconnect

        self.last_update: datetime.datetime | None = None
        self.last_position: int = 0

        self._ping: int = 0

        self.queue: Queue = Queue()
        self._current: Playable | None = None

        self._volume: int = 50
        self._paused: bool = False

        self._autoplay: bool = False
        self.auto_queue: Queue = Queue()
        self._auto_threshold: int = 20
        self._filter: Filter | None = None

    async def _auto_play_event(self, payload: TrackEventPayload) -> None:
        if not self.autoplay:
            return

        if self.queue:
            populate = len(self.auto_queue) < self._auto_threshold
            await self.play(self.queue.get(), populate=populate)

            return

        if not self.auto_queue:
            return

        await self.queue.put_wait(await self.auto_queue.get_wait())
        populate = self.auto_queue.is_empty

        await self.play(await self.queue.get_wait(), populate=populate)

    @property
    def autoplay(self) -> bool:
        """Bool whether the Player is in AutoPlay mode or not.

        Can be set to True or False.
        """
        return self._autoplay

    @autoplay.setter
    def autoplay(self, value: bool) -> None:
        """Set AutoPlay to True or False."""
        self._autoplay = value

    def is_playing(self) -> bool:
        """Whether the Player is currently playing a track."""
        return self.current is not None

    def is_paused(self) -> bool:
        """Whether the Player is currently paused."""
        return self._paused

    @property
    def volume(self) -> int:
        """The current volume of the Player."""
        return self._volume

    @property
    def guild(self) -> discord.Guild | None:
        """The discord Guild associated with the Player."""
        return self._guild

    @property
    def position(self) -> float:
        """The position of the currently playing track in milliseconds."""

        if not self.is_playing():
            return 0

        if self.is_paused():
            return min(self.last_position, self.source.duration)  # type: ignore

        delta = (datetime.datetime.now(datetime.timezone.utc) - self.last_update).total_seconds() * 1000
        position = self.last_position + delta

        return min(position, self.current.duration)

    @property
    def ping(self) -> int:
        """The ping to the discord endpoint in milliseconds."""
        return self._ping

    @property
    def current(self) -> Playable | None:
        """The currently playing Track if there is one.

        Could be None if no Track is playing.
        """
        return self._current

    @property
    def filter(self) -> dict[str, Any]:
        return self._filter._payload

    async def _update_event(self, data: PlayerUpdateOp | None) -> None:
        assert self._guild is not None

        if data is None: 
            if self.swap_on_disconnect:

                if len(self.nodes) < 2:
                    return

                new: Node = [n for n in self.nodes if n != self.current_node and n.status is NodeStatus.CONNECTED][0]
                del self.current_node._players[self._guild.id]

                if not new:
                    return

                self.current_node: Node = new
                new._players[self._guild.id] = self

                await self._dispatch_voice_update()
                await self._swap_state()
            return

        data.pop('op')  # type: ignore
        self._player_state.update(**data)

        state: PlayerState = data['state']
        self.last_update = datetime.datetime.fromtimestamp(state.get("time", 0) / 1000, datetime.timezone.utc)
        self.last_position = state.get('position', 0)

        self._ping = state['ping']

    async def on_voice_server_update(self, data: VoiceServerUpdate) -> None:
        self._voice_state['token'] = data['token']
        self._voice_state['endpoint'] = data['endpoint']

        await self._dispatch_voice_update()

    async def on_voice_state_update(self, data: GuildVoiceState) -> None:
        assert self._guild is not None

        channel_id = data["channel_id"]

        if not channel_id:
            await self.destroy()
            return

        self._voice_state['session_id'] = data['session_id']
        self.channel = self.client.get_channel(int(channel_id))  # type: ignore

        if not self._guild:
            self._guild = self.channel.guild  # type: ignore
            assert self._guild is not None
            self.current_node._players[self._guild.id] = self

    async def _dispatch_voice_update(self, data: DiscordVoiceState | None = None) -> None:
        assert self._guild is not None

        data = data or self._voice_state

        try:
            session_id: str = data['session_id']
            token: str = data['token']
            endpoint: str = data['endpoint']
        except KeyError:
            return

        voice: Request = {'voice': {'sessionId': session_id, 'token': token, 'endpoint': endpoint}}
        self._player_state.update(**voice)

        resp: dict[str, Any] = await self.current_node._send(method='PATCH',
                                                             path=f'sessions/{self.current_node._session_id}/players',
                                                             guild_id=self._guild.id,
                                                             data=voice)

        logger.debug(f'Dispatching VOICE_UPDATE: {resp}')

    async def connect(self, *, timeout: float, reconnect: bool, **kwargs: Any) -> None:
        if self.channel is None:
            raise RuntimeError('')

        if not self._guild:
            self._guild = self.channel.guild
            self.current_node._players[self._guild.id] = self

        await self.channel.guild.change_voice_state(channel=self.channel, **kwargs)

    async def move_to(self, channel: discord.VoiceChannel) -> None:
        """|coro|

        Moves the player to a different voice channel.

        Parameters
        -----------
        channel: :class:`discord.VoiceChannel`
            The channel to move to. Must be a voice channel.
        """
        await self.guild.change_voice_state(channel=channel)
        logger.info(f"Moving to voice channel:: {channel.id}")

    async def play(self,
                   track: Playable,
                   replace: bool = True,
                   start: int | None = None,
                   end: int | None = None,
                   volume: int | None = None,
                   *,
                   populate: bool = False
                   ) -> Playable:
        """|coro|

        Play a WaveLink Track.

        Parameters
        ----------
        track: :class:`tracks.Playable`
            The :class:`tracks.Playable` track to start playing.
        replace: bool
            Whether this track should replace the current track. Defaults to ``True``.
        start: Optional[int]
            The position to start the track at in milliseconds.
            Defaults to ``None`` which will start the track at the beginning.
        end: Optional[int]
            The position to end the track at in milliseconds.
            Defaults to ``None`` which means it will play until the end.
        volume: Optional[int]
            Sets the volume of the player. Must be between ``0`` and ``1000``.
            Defaults to ``None`` which will not change the volume.
        populate: bool
            Whether to populate the AutoPlay queue. This is done automatically when AutoPlay is on.
            Defaults to False.

        Returns
        -------
        :class:`tracks.Playable`
            The track that is now playing.
        """
        assert self._guild is not None

        if isinstance(track, spotify.SpotifyTrack):
            track = await track.fulfill(player=self, cls=YouTubeTrack, populate=populate)

        data = {
            'encodedTrack': track.encoded,
            'position': start or 0,
            'volume': volume or self._volume
        }

        if end:
            data['endTime'] = end

        resp: dict[str, Any] = await self.current_node._send(method='PATCH',
                                                             path=f'sessions/{self.current_node._session_id}/players',
                                                             guild_id=self._guild.id,
                                                             data=data,
                                                             query=f'noReplace={not replace}')

        self._player_state['track'] = resp['track']['encoded']
        self._current = track

        return track

    async def set_volume(self, value: int) -> None:
        """|coro|

        Set the Player volume.

        Parameters
        ----------
        value: int
            A volume value between 0 and 1000.
        """
        assert self._guild is not None

        self._volume = max(min(value, 1000), 0)

        resp: dict[str, Any] = await self.current_node._send(method='PATCH',
                                                             path=f'sessions/{self.current_node._session_id}/players',
                                                             guild_id=self._guild.id,
                                                             data={'volume': self._volume})

        logger.debug(f'Player {self.guild.id} volume was set to {self._volume}.')

    async def seek(self, position: int) -> None:
        """|coro|

        Seek to the provided position, in milliseconds.

        Parameters
        ----------
        position: int
            The position to seek to in milliseconds.
        """
        if not self._current:
            return

        resp: dict[str, Any] = await self.current_node._send(method='PATCH',
                                                             path=f'sessions/{self.current_node._session_id}/players',
                                                             guild_id=self._guild.id,
                                                             data={'position': position})

        logger.debug(f'Player {self.guild.id} seeked current track to position {position}.')

    async def pause(self) -> None:
        """|coro|

        Pauses the Player.
        """
        assert self._guild is not None

        resp: dict[str, Any] = await self.current_node._send(method='PATCH',
                                                             path=f'sessions/{self.current_node._session_id}/players',
                                                             guild_id=self._guild.id,
                                                             data={'paused': True})

        self._paused = True
        logger.debug(f'Player {self.guild.id} was paused.')

    async def resume(self) -> None:
        """|coro|

        Resumes the Player.
        """
        assert self._guild is not None

        resp: dict[str, Any] = await self.current_node._send(method='PATCH',
                                                             path=f'sessions/{self.current_node._session_id}/players',
                                                             guild_id=self._guild.id,
                                                             data={'paused': False})

        self._paused = False
        logger.debug(f'Player {self.guild.id} was resumed.')

    async def stop(self) -> None:
        """|coro|

        Stops the currently playing Track.
        """
        assert self._guild is not None

        resp: dict[str, Any] = await self.current_node._send(method='PATCH',
                                                             path=f'sessions/{self.current_node._session_id}/players',
                                                             guild_id=self._guild.id,
                                                             data={'encodedTrack': None})

        self._player_state['track'] = None
        logger.debug(f'Player {self.guild.id} was stopped.')

    async def set_filter(
        self,
        _filter: Filter,
        /, *,
        seek: bool = False
    ) -> None:
        """|coro|

        Set the player's filter.

        Parameters
        ----------
        filter: :class:`wavelink.Filter`
            The filter to apply to the player.
        seek: bool
            Whether to seek the player to its current position
            which will apply the filter immediately. Defaults to ``False``.
        """

        assert self._guild is not None

        self._filter = _filter
        data: Request = {"filters": _filter._payload}

        resp: dict[str, Any] = await self.current_node._send(method='PATCH',
                                                             path=f'sessions/{self.current_node._session_id}/players',
                                                             guild_id=self._guild.id,
                                                             data=data)        

        if self.is_playing() and seek:
            await self.seek(int(self.position * 1000))
        logger.debug(f"Set filter:: {self._filter} ({self.channel.id})")

    async def destroy(self) -> None:
        assert self._guild is not None

        self.autoplay = False
        self._voice_state = {}
        self._player_state = {}
        self.cleanup()

        await self.current_node._send(method='DELETE',
                                      path=f'sessions/{self.current_node._session_id}/players',
                                      guild_id=self._guild.id)

        del self.current_node._players[self.guild.id]
        logger.debug(f'Player {self.guild.id} was destroyed.')

    async def _swap_state(self) -> None:
        assert self._guild is not None

        try:
            self._player_state['track']
        except KeyError:
            return

        data: EncodedTrackRequest = {'encodedTrack': self._player_state['track'], 'position': self.position}
        resp: dict[str, Any] = await self.current_node._send(method='PATCH',
                                                             path=f'sessions/{self.current_node._session_id}/players',
                                                             guild_id=self._guild.id,
                                                             data=data)

        logger.debug(f'Swapping State: {resp}')
