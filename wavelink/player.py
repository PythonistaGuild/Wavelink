"""MIT License
Copyright (c) 2019-2020 PythonistaGuild
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

from typing import Any, Dict, Optional

import discord

import wavelink.abc
from .equalizer import Equalizer
from .errors import WavelinkException, ZeroConnectedNodes
from .node import Node


log = logging.getLogger(__name__)


class Player(discord.VoiceProtocol):
    """Represents a Wavelink Player.

    .. warning::
        You should not create :class:`Player` objects manually.
        Instead you should use the :func:`~discord.abc.Connectable.connect` method.

    Attributes
    ----------
    client: :class:`~discord.Client`
        The discord :class:`~discord.Client` attached to this :class:`Player`.
    node: :class:`Node`
        The node this :class:`Player` belongs to.
    channel: Optional[:class:`~discord.VoiceChannel`]
        The :class:`~discord.VoiceChannel` the :class:`~discord.Client` is connected to. Could be ``None``.
    volume: int
        The :class:`Player`'s current volume.
    """

    def __init__(self, client: discord.Client, channel: discord.VoiceChannel):
        self.client = client
        self.channel = channel

        node = Node.get_best_node(client, guild=channel.guild)
        if node is None:
            raise ZeroConnectedNodes

        self.node = node
        self.node.players.append(self)

        self._voice_state: Dict[str, Any] = {}

        self.last_update: datetime.datetime = None  # type: ignore
        self.last_position: float = None  # type: ignore

        self.volume = 100
        self._paused = False
        self._source: Optional[wavelink.abc.Playable] = None
        self._equalizer = Equalizer.flat()

    @property
    def guild(self) -> discord.Guild:
        """The :class:`~discord.Guild` this :class:`Player` is in."""
        return self.channel.guild

    @property
    def user(self) -> discord.ClientUser:
        """The :class:`~discord.ClientUser` of the :class:`~discord.Client`"""
        return self.client.user

    @property
    def equalizer(self) -> Equalizer:
        """The currently applied Equalizer."""
        return self._equalizer

    eq = equalizer

    @property
    def source(self) -> Optional[wavelink.abc.Playable]:
        """The currently playing audio source."""
        return self._source

    track = source

    @property
    def position(self) -> float:
        """The current seek position of the playing source in seconds. If nothing is playing this defaults to ``0``."""
        if not self.is_playing():
            return 0

        if self.is_paused():
            return min(self.last_position, self.source.duration)  # type: ignore

        delta = (datetime.datetime.now(datetime.timezone.utc) - self.last_update).total_seconds()
        position = round(self.last_position + delta, 1)

        return min(position, self.source.duration)  # type: ignore

    async def update_state(self, state: Dict[str, Any]):
        state = state['state']

        self.last_update = datetime.datetime.fromtimestamp(state.get('time', 0) / 1000, datetime.timezone.utc)
        self.last_position = round(state.get('position', 0) / 1000, 1)

    async def on_voice_server_update(self, data: Dict[str, Any]):
        self._voice_state.update({
            'event': data
        })

        await self._dispatch_voice_update(self._voice_state)

    async def on_voice_state_update(self, data: Dict[str, Any]):
        self._voice_state.update({
            'sessionId': data['session_id']
        })

        channel_id = data['channel_id']
        if not channel_id:  # We're disconnecting
            self._voice_state.clear()
            return

        self.channel = self.guild.get_channel(int(channel_id))
        await self._dispatch_voice_update({**self._voice_state, 'event': data})

    async def _dispatch_voice_update(self, voice_state: Dict[str, Any]):
        log.debug(f'PLAYER | Dispatching voice update:: {self.channel.id}')
        if {'sessionId', 'event'} == self._voice_state.keys():
            await self.node.websocket.send(op='voiceUpdate', guildId=str(self.guild.id), **voice_state)

    async def connect(self, *, timeout: float, reconnect: bool):
        await self.guild.change_voice_state(channel=self.channel)
        self._connected = True
        log.info(f'PLAYER | Connected to voice channel:: {self.channel.id}')

    async def disconnect(self, *, force: bool):
        try:
            log.info(f'PLAYER | Disconnected from voice channel:: {self.channel.id}')
            await self.guild.change_voice_state(channel=None)
            self._connected = False
        finally:
            self.node.players.remove(self)
            self.cleanup()

    async def move_to(self, channel: discord.VoiceChannel):
        """|coro|

        Moves the player to a different voice channel.

        Parameters
        -----------
        channel: :class:`~discord,VoiceChannel`
            The channel to move to. Must be a voice channel.
        """
        await self.guild.change_voice_state(channel=channel)
        log.info(f'PLAYER | Moving to voice channel:: {channel.id}')

    async def play(self, source: wavelink.abc.Playable, replace: bool = True, start: int = 0, end: int = 0):
        """|coro|

        Play a WaveLink Track.

        Parameters
        ----------
        source: :class:`abc.Playable`
            The :class:`abc.Playable` to initiate playing.
        replace: bool
            Whether or not the current track, if there is one, should be replaced or not. Defaults to ``True``.
        start: int
            The position to start the player from in milliseconds. Defaults to ``0``.
        end: int
            The position to end the track on in milliseconds.
            By default this always allows the current song to finish playing.
        """
        if replace or not self.is_playing():
            await self.update_state({'state': {}})
            self._paused = False
        else:
            return

        self._source = source

        payload = {'op': 'play',
                   'guildId': str(self.guild.id),
                   'track': source.id,
                   'noReplace': not replace,
                   'startTime': str(start)
                   }
        if end > 0:
            payload['endTime'] = str(end)

        await self.node.websocket.send(**payload)

        log.debug(f'PLAYER | Started playing track:: {str(source)} ({self.channel.id})')

    def is_connected(self) -> bool:
        """Indicates whether the player is connected to voice."""
        return self._connected

    def is_playing(self) -> bool:
        """Indicates wether a track is currently being played."""
        return self.is_connected() and self._source is not None

    def is_paused(self) -> bool:
        """Indicates wether the currently playing track is paused."""
        return self._paused

    async def stop(self):
        """|coro|

        Stop the Player's currently playing song.
        """
        await self.node.websocket.send(op='stop', guildId=str(self.guild.id))
        log.debug(f'PLAYER | Current track stopped:: {str(self.source)} ({self.channel.id})')
        self._source = None

    async def set_pause(self, pause: bool) -> None:
        """|coro|

        Set the players paused state.

        Parameters
        ----------
        pause: bool
            A bool indicating if the player's paused state should be set to True or False.
        """
        await self.node.websocket.send(op='pause', guildId=str(self.guild.id), pause=pause)
        self._paused = pause
        log.info(f'PLAYER | Set pause:: {self._paused} ({self.channel.id})')

    async def pause(self):
        """|coro|

        Pauses the player if it was playing.
        """
        await self.set_pause(True)

    async def resume(self):
        """|coro|

        Resumes the player if it was paused.
        """
        await self.set_pause(False)

    async def set_volume(self, volume: int):
        """|coro|

        Set the player's volume, between 0 and 1000.

        Parameters
        ----------
        volume: int
            The volume to set the player to.
        """
        self.volume = max(min(volume, 1000), 0)
        await self.node.websocket.send(op='volume', guildId=str(self.guild.id), volume=self.volume)
        log.debug(f'PLAYER | Set volume:: {self.volume} ({self.channel.id})')

    async def seek(self, position: int = 0):
        """|coro|

        Seek to the given position in the song.

        Parameters
        ----------
        position: int
            The position as an int in milliseconds to seek to. Could be None to seek to beginning.
        """
        await self.node.websocket.send(op='seek', guildId=str(self.guild.id), position=position)

    async def change_node(self, node: Optional[Node]):
        """|coro|

        Change the players current :class:`Node`. Useful when a Node fails or when changing regions.
        The change Node behaviour allows for near seamless fallbacks and changeovers to occur.

        Parameters
        ----------
        Optional[Node]
            The node to change to. If None, the next best available Node will be found.
        """
        if node is not None:
            if node == self.node:
                raise WavelinkException('Player is already on this node.')
        else:
            self.node.close()
            node = Node.get_best_node(self.client, region=self.node.region, shard_id=self.node.shard_id)
            self.node.open()
            if node is None:
                raise WavelinkException('No Nodes available for changeover.')

        old_node = self.node
        old_node.players.remove(self)
        await old_node.websocket.send(op='destroy', guildId=str(self.guild.id))

        self.node = node
        self.node.players.append(self)

        if self._voice_state:
            await self._dispatch_voice_update(self._voice_state)

        if self._source is not None:
            await self.node.websocket.send(op='play', guildId=str(self.guild.id), track=self._source.id, startTime=int(self.position))
            self.last_update = datetime.datetime.now(datetime.timezone.utc)

            if self.is_paused():
                await self.node.websocket.send(op='pause', guildId=str(self.guild.id), pause=self._paused)

        if self.volume != 100:
            await self.node.websocket.send(op='volume', guildId=str(self.guild.id), volume=self.volume)
