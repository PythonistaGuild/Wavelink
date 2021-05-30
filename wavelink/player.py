"""MIT License

Copyright (c) 2019-2021 PythonistaGuild

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

import datetime
import logging

import discord

from .abc import *
from .pool import Node, NodePool
from .queue import WaitQueue


logger = logging.getLogger(__name__)


class Player(discord.VoiceProtocol):
    """WaveLink Player object.

    This class subclasses :class:`~discord.VoiceProtocol` and such should be treated as one with additions.

    Examples
    --------

        .. code::

            @commands.command()
            async def connect(self, channel: discord.VoiceChannel):

                voice_client = await channel.connect(cls=wavelink.Player)


    .. warning::
        This class should not be created manually but can be subclassed to add additional functionality.
        You should instead use :meth:`~discord.VoiceChannel.connect()` and pass the player object to the cls kwarg.
    """

    def __call__(self, client: discord.Client, channel: discord.VoiceChannel):
        self.client = client
        self.channel = channel

        return self

    def __init__(self, client: discord.Client = None, channel: discord.VoiceChannel = None, /, *, node: Node = None):
        self.client = client
        self.channel = channel

        self.node = node or NodePool.get_node()
        self.node._players.append(self)

        self._voice_state = {}

        self.last_update: datetime.datetime = None
        self.last_position: float = None

        self.volume = 100
        self._paused = False
        self._source = None
        # self._equalizer = Equalizer.flat()

        self.queue = WaitQueue()

    @property
    def guild(self) -> discord.Guild:
        """The :class:`~discord.Guild` this :class:`Player` is in."""
        return self.channel.guild

    @property
    def user(self) -> discord.ClientUser:
        """The :class:`~discord.ClientUser` of the :class:`~discord.Client`"""
        return self.client.user

    @property
    def source(self):
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

    async def update_state(self, state):
        state = state['state']

        self.last_update = datetime.datetime.fromtimestamp(state.get('time', 0) / 1000, datetime.timezone.utc)
        self.last_position = round(state.get('position', 0) / 1000, 1)

    async def on_voice_server_update(self, data):
        self._voice_state.update({
            'event': data
        })

        await self._dispatch_voice_update(self._voice_state)

    async def on_voice_state_update(self, data):
        self._voice_state.update({
            'sessionId': data['session_id']
        })

        channel_id = data['channel_id']
        if not channel_id:  # We're disconnecting
            self._voice_state.clear()
            return

        self.channel = self.guild.get_channel(int(channel_id))
        await self._dispatch_voice_update({**self._voice_state, 'event': data})

    async def _dispatch_voice_update(self, voice_state):
        logger.debug(f'Dispatching voice update:: {self.channel.id}')

        if {'sessionId', 'event'} == self._voice_state.keys():
            await self.node._websocket.send(op='voiceUpdate', guildId=str(self.guild.id), **voice_state)

    async def connect(self, *, timeout: float, reconnect: bool):
        await self.guild.change_voice_state(channel=self.channel)
        self._connected = True

        logger.info(f'Connected to voice channel:: {self.channel.id}')

    async def disconnect(self, *, force: bool):
        try:
            logger.info(f'Disconnected from voice channel:: {self.channel.id}')

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
        logger.info(f'Moving to voice channel:: {channel.id}')

    async def play(self, source: Playable, replace: bool = True, start: int = 0, end: int = 0):
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

        await self.node._websocket.send(**payload)

        logger.debug(f'Started playing track:: {str(source)} ({self.channel.id})')

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
        await self.node._websocket.send(op='stop', guildId=str(self.guild.id))
        logger.debug(f'Current track stopped:: {str(self.source)} ({self.channel.id})')
        self._source = None

    async def set_pause(self, pause: bool) -> None:
        """|coro|

        Set the players paused state.

        Parameters
        ----------
        pause: bool
            A bool indicating if the player's paused state should be set to True or False.
        """
        await self.node._websocket.send(op='pause', guildId=str(self.guild.id), pause=pause)
        self._paused = pause
        logger.info(f'Set pause:: {self._paused} ({self.channel.id})')

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
        await self.node._websocket.send(op='volume', guildId=str(self.guild.id), volume=self.volume)
        logger.debug(f'Set volume:: {self.volume} ({self.channel.id})')

    async def seek(self, position: int = 0):
        """|coro|

        Seek to the given position in the song.

        Parameters
        ----------
        position: int
            The position as an int in milliseconds to seek to. Could be None to seek to beginning.
        """
        await self.node._websocket.send(op='seek', guildId=str(self.guild.id), position=position)
