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

import nextcord
from nextcord.utils import MISSING

from .enums import *
from .exceptions import *
from .ext import spotify
from .filters import Filter
from .node import Node, NodePool
from .payloads import TrackEventPayload
from .queue import Queue
from .tracks import *


if TYPE_CHECKING:
    from nextcord.types.voice import GuildVoiceState, VoiceServerUpdate
    from typing_extensions import Self

    from .types.events import PlayerState, PlayerUpdateOp
    from .types.request import EncodedTrackRequest, Request
    from .types.state import DiscordVoiceState

__all__ = ("Player",)


logger: logging.Logger = logging.getLogger(__name__)


VoiceChannel = Union[
    nextcord.VoiceChannel, nextcord.StageChannel
]  # todo: VocalGuildChannel?


class Player(nextcord.VoiceProtocol):
    """Wavelink Player class.

    This class is used as a :class:`~nextcord.VoiceProtocol` and inherits all its members.


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
    client: :class:`nextcord.Client`
        The nextcord Client or Bot associated with this Player.
    channel: :class:`nextcord.VoiceChannel`
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

    def __call__(self, client: nextcord.Client, channel: VoiceChannel) -> Self:
        self.client = client
        self.channel = channel

        return self

    def __init__(
        self,
        client: nextcord.Client = MISSING,
        channel: VoiceChannel = MISSING,
        *,
        nodes: list[Node] | None = None,
        swap_node_on_disconnect: bool = True
    ) -> None:
        self.client: nextcord.Client = client
        self.channel: VoiceChannel | None = channel

        self.nodes: list[Node]
        self.current_node: Node

        if swap_node_on_disconnect and not nodes:
            nodes = list(NodePool.nodes.values())
            self.nodes = sorted(nodes, key=lambda n: len(n.players))
            self.current_node = self.nodes[0]
        elif nodes:
            nodes = sorted(nodes, key=lambda n: len(n.players))
            self.current_node = nodes[0]
            self.nodes = nodes
        else:
            self.current_node = NodePool.get_connected_node()
            self.nodes = [self.current_node]

        if not self.client:
            if self.current_node.client is None:
                raise RuntimeError('')
            self.client = self.current_node.client

        self._guild: nextcord.Guild | None = None
        self._voice_state: DiscordVoiceState = {}
        self._player_state: dict[str, Any] = {}

        self.swap_on_disconnect: bool = swap_node_on_disconnect

        self.last_update: datetime.datetime | None = None
        self.last_position: int = 0

        self._ping: int = 0

        self.queue: Queue = Queue()
        self._current: Playable | None = None
        self._original: Playable | None = None

        self._volume: int = 50
        self._paused: bool = False

        self._track_seeds: list[str] = []
        self._autoplay: bool = False
        self.auto_queue: Queue = Queue()
        self._auto_threshold: int = 20
        self._filter: Filter | None = None

    async def _auto_play_event(self, payload: TrackEventPayload) -> None:
        if not self.autoplay:
            return

        if payload.reason == 'REPLACED':
            return

        if self.queue.loop:
            try:
                track = self.queue.get()
            except QueueEmpty:
                return

            await self.play(track)
            return

        if self.queue:
            populate = len(self.auto_queue) < self._auto_threshold
            await self.play(self.queue.get(), populate=populate)

            return

        if self.queue.loop_all:
            await self.play(self.queue.get())
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

    def is_connected(self) -> bool:
        """Whether the player is connected to a voice channel."""
        return self.channel is not None and self.channel is not MISSING

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
    def guild(self) -> nextcord.Guild | None:
        """The nextcord Guild associated with the Player."""
        return self._guild

    @property
    def position(self) -> float:
        """The position of the currently playing track in milliseconds."""

        if not self.is_playing():
            return 0

        if self.is_paused():
            return min(self.last_position, self.current.duration)  # type: ignore

        delta = (datetime.datetime.now(datetime.timezone.utc) - self.last_update).total_seconds() * 1000
        position = self.last_position + delta

        return min(position, self.current.duration)

    @property
    def ping(self) -> int:
        """The ping to the nextcord endpoint in milliseconds."""
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
            await self._destroy()
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
            self._invalidate()

            msg: str = 'Please use the method "nextcord.VoiceChannel.connect" and pass this player to cls='
            raise InvalidChannelStateError(msg)

        if not self.channel.permissions_for(self.channel.guild.me).connect:
            self._invalidate()

            raise InvalidChannelPermissions('You do not have connect permissions to join this channel.')

        limit: int = self.channel.user_limit
        total: int = len(self.channel.members)

        if limit == 0:
            pass

        elif total >= limit:
            self._invalidate()

            msg: str = f'There are currently too many users in this channel. <{total}/{limit}>'
            raise InvalidChannelPermissions(msg)

        if not self._guild:
            self._guild = self.channel.guild
            self.current_node._players[self._guild.id] = self

        await self.channel.guild.change_voice_state(channel=self.channel, **kwargs)

    async def move_to(self, channel: nextcord.VoiceChannel) -> None:
        """|coro|

        Moves the player to a different voice channel.

        Parameters
        -----------
        channel: :class:`nextcord.VoiceChannel`
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
            original = track
            track = await track.fulfill(player=self, cls=YouTubeTrack, populate=populate)

            for attr, value in original.__dict__.items():
                if hasattr(track, attr):
                    logger.warning(f'Unable to set attribute "{attr}" as it conflicts with new track type.')
                    continue

                setattr(track, attr, value)

        data = {
            'encodedTrack': track.encoded,
            'position': start or 0,
            'volume': volume or self._volume
        }

        if end:
            data['endTime'] = end

        self._current = track
        self._original = track

        try:

            resp: dict[str, Any] = await self.current_node._send(
                method='PATCH',
                path=f'sessions/{self.current_node._session_id}/players',
                guild_id=self._guild.id,
                data=data,
                query=f'noReplace={not replace}'
            )

        except InvalidLavalinkResponse as e:
            self._current = None
            self._original = None
            raise e

        self._player_state['track'] = resp['track']['encoded']

        if self.queue.loop and self.queue._loaded:
            pass
        else:
            self.queue.history.put(track)

        self.queue._loaded = track

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

        self.queue._loaded = None

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
            await self.seek(int(self.position))
        logger.debug(f"Set filter:: {self._filter} ({self.channel.id})")

    def _invalidate(self) -> None:
        try:
            self.cleanup()
        except Exception as e:
            logger.debug(f'Failed to cleanup player, most likely due to never having been connected: {e}')

        self._voice_state = {}
        self._player_state = {}
        self.channel = None

    async def _destroy(self) -> None:
        self._invalidate()

        await self.current_node._send(method='DELETE',
                                      path=f'sessions/{self.current_node._session_id}/players',
                                      guild_id=self._guild.id)

        del self.current_node._players[self._guild.id]
        logger.debug(f'Player {self._guild.id} was destroyed.')

    async def disconnect(self, **kwargs) -> None:
        """|coro|

        Disconnect the Player from voice and cleanup the Player state.
        """
        self._invalidate()
        await self.guild.change_voice_state(channel=None)

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
