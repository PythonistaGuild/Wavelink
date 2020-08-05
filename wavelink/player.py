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
import logging
import time
import re
from discord.ext import commands
from discord.gateway import DiscordWebSocket
from typing import Optional, Union

from .errors import *
from .eqs import *
from .events import *


__all__ = ('Track', 'TrackPlaylist', 'Player')
__log__ = logging.getLogger(__name__)


class Track:
    """Wavelink Tack object.

    Attributes
    ------------
    id: str
        The Base64 Track ID.
    info: dict
        The raw track info.
    title: str
        The track title.
    identifier: Optional[str]
        The tracks identifier. could be None depending on track type.
    ytid: Optional[str]
        The tracks YouTube ID. Could be None if ytsearch was not used.
    length:
        The duration of the track.
    duration:
        Alias to length.
    uri: Optional[str]
        The tracks URI. Could be None.
    author: Optional[str]
        The author of the track. Could be None
    is_stream: bool
        Indicated whether the track is a stream or not.
    thumb: Optional[str]
        The thumbnail URL associated with the track. Could be None.
    """

    __slots__ = ('id',
                 'info',
                 'query',
                 'title',
                 'identifier',
                 'ytid',
                 'length',
                 'duration',
                 'uri',
                 'author',
                 'is_stream',
                 'dead',
                 'thumb')

    def __init__(self, id_, info: dict, query: str = None):
        self.id = id_
        self.info = info
        self.query = query

        self.title = info.get('title')
        self.identifier = info.get('identifier')
        self.ytid = self.identifier if re.match(r"^[a-zA-Z0-9_-]{11}$", self.identifier) else None
        self.length = info.get('length')
        self.duration = self.length
        self.uri = info.get('uri')
        self.author = info.get('author')

        self.is_stream = info.get('isStream')
        self.dead = False

        if self.ytid:
            self.thumb = f"https://img.youtube.com/vi/{self.ytid}/maxresdefault.jpg"
        else:
            self.thumb = None

    def __str__(self):
        return self.title

    @property
    def is_dead(self):
        return self.dead


class TrackPlaylist:
    """Track Playlist object.

    Attributes
    ------------
    data: dict
        The raw playlist info dict.
    tracks: list
        A list of individual :class:`Track` objects from the playlist.
    """

    def __init__(self, data: dict):
        self.data = data
        self.tracks = [Track(id_=track['track'], info=track['info']) for track in data['tracks']]


class Player:
    """Wavelink Player class.

    Attributes
    ------------
    bot: Union[discord.ext.commands.Bot, discord.ext.commands.AutoShardedBot]
        The discord Bot instance.
    guild_id: int
        The guild ID the player is connected to.
    node: :class:`wavelink.node.Node`
        The node the player belongs to.
    volume: int
        The players volume.
    channel_id: int
        The channel the player is connected to. Could be None if the player is not connected.
    """

    def __init__(self, bot: Union[commands.Bot, commands.AutoShardedBot], guild_id: int, node, **kwargs):
        self.bot = bot
        self.guild_id = guild_id
        self.node = node

        self.last_update = None
        self.last_position = None
        self.position_timestamp = None

        self._voice_state = {}

        self.volume = 100
        self.paused = False
        self.current = None
        self._equalizer = Equalizer.flat()
        self.channel_id = None

    @property
    def equalizer(self):
        """The currently applied Equalizer."""
        return self._equalizer

    @property
    def eq(self):
        """Alias to :func:`equalizer`."""
        return self.equalizer

    @property
    def is_connected(self) -> bool:
        """Returns whether the player is connected to a voicechannel or not."""
        return self.channel_id is not None

    @property
    def is_playing(self) -> bool:
        """Returns whether or not the player is currently playing."""
        return self.is_connected and self.current is not None

    @property
    def is_paused(self) -> bool:
        """Returns whether or not the player is paused."""
        return self.paused

    @property
    def position(self):
        if not self.is_playing:
            return 0

        if not self.current:
            return 0

        if self.paused:
            return min(self.last_position, self.current.duration)

        difference = (time.time() * 1000) - self.last_update
        position = self.last_position + difference

        if position > self.current.duration:
            return 0

        return min(position, self.current.duration)

    async def update_state(self, state: dict) -> None:
        state = state['state']

        self.last_update = time.time() * 1000
        self.last_position = state.get('position', 0)
        self.position_timestamp = state.get('time', 0)

    async def _voice_server_update(self, data) -> None:
        self._voice_state.update({
            'event': data
        })

        await self._dispatch_voice_update()

    async def _voice_state_update(self, data) -> None:
        self._voice_state.update({
            'sessionId': data['session_id']
        })

        channel_id = data['channel_id']

        if not channel_id:  # We're disconnecting
            self._voice_state.clear()
            return

        self.channel_id = int(channel_id)
        await self._dispatch_voice_update()

    async def _dispatch_voice_update(self) -> None:
        __log__.debug(f'PLAYER | Dispatching voice update:: {self.channel_id}')
        if {'sessionId', 'event'} == self._voice_state.keys():
            await self.node._send(op='voiceUpdate', guildId=str(self.guild_id), **self._voice_state)

    async def hook(self, event) -> None:
        if isinstance(event, (TrackEnd, TrackException, TrackStuck)):
            self.current = None

    def _get_shard_socket(self, shard_id: int) -> Optional[DiscordWebSocket]:
        if isinstance(self.bot, commands.AutoShardedBot):
            try:
                return self.bot.shards[shard_id].ws
            except AttributeError:
                return self.bot.shards[shard_id]._parent.ws

        if self.bot.shard_id is None or self.bot.shard_id == shard_id:
            return self.bot.ws

    async def connect(self, channel_id: int):
        """|coro|

        Connect to a Discord Voice Channel.

        Parameters
        ------------
        channel_id: int
            The channel ID to connect to.
        """
        guild = self.bot.get_guild(self.guild_id)
        if not guild:
            raise InvalidIDProvided(f'No guild found for id <{self.guild_id}>')

        self.channel_id = channel_id
        await self._get_shard_socket(guild.shard_id).voice_state(self.guild_id, str(channel_id))
        __log__.info(f'PLAYER | Connected to voice channel:: {self.channel_id}')

    async def disconnect(self) -> None:
        """|coro|

        Disconnect from a Discord Voice Channel.
        """
        guild = self.bot.get_guild(self.guild_id)
        if not guild:
            raise InvalidIDProvided(f'No guild found for id <{self.guild_id}>')

        __log__.info(f'PLAYER | Disconnected from voice channel:: {self.channel_id}')
        self.channel_id = None
        await self._get_shard_socket(guild.shard_id).voice_state(self.guild_id, None)

    async def play(self, track: Track, *, replace: bool = True, start: int = 0, end: int = 0) -> None:
        """|coro|

        Play a WaveLink Track.

        Parameters
        ------------
        track: :class:`Track`
            The :class:`Track` to initiate playing.
        replace: bool
            Whether or not the current track, if there is one, should be replaced or not. Defaults to True.
        start: int
            The position to start the player from in milliseconds. Defaults to 0.
        end: int
            The position to end the track on in milliseconds. By default this always allows the current
            song to finish playing.
        """
        if replace or not self.is_playing:
            self.last_update = 0
            self.last_position = 0
            self.position_timestamp = 0
            self.paused = False
        else:
            return

        no_replace = not replace

        self.current = track

        payload = {'op': 'play',
                   'guildId': str(self.guild_id),
                   'track': track.id,
                   'noReplace': no_replace,
                   'startTime': str(start)
                   }
        if end > 0:
            payload['endTime'] = str(end)

        await self.node._send(**payload)

        __log__.debug(f'PLAYER | Started playing track:: {str(track)} ({self.channel_id})')

    async def stop(self) -> None:
        """|coro|

        Stop the Player's currently playing song.
        """
        await self.node._send(op='stop', guildId=str(self.guild_id))
        __log__.debug(f'PLAYER | Current track stopped:: {str(self.current)} ({self.channel_id})')
        self.current = None

    async def destroy(self) -> None:
        """|coro|

        Stop the player, and remove any internal references to it.
        """
        await self.stop()
        await self.disconnect()

        await self.node._send(op='destroy', guildId=str(self.guild_id))
        del self.node.players[self.guild_id]

    async def set_eq(self, equalizer: Equalizer) -> None:
        """|coro|

        Set the Players Equalizer.

        .. versionchanged:: 0.5.0
            set_eq now accepts an :class:`Equalizer` instead of raw band/gain pairs.

        Parameters
        ------------
        equalizer: :class:`Equalizer`
            The Equalizer to set.
        """
        await self.node._send(op='equalizer', guildId=str(self.guild_id), bands=equalizer.eq)
        self._equalizer = equalizer

    async def set_equalizer(self, equalizer: Equalizer) -> None:
        """|coro|

        An alias to :func:`set_eq`.
        """
        await self.set_eq(equalizer)

    async def set_pause(self, pause: bool) -> None:
        """|coro|

        Set the players paused state.

        Parameters
        ------------
        pause: bool
            A bool indicating if the player's paused state should be set to True or False.
        """
        await self.node._send(op='pause', guildId=str(self.guild_id), pause=pause)
        self.paused = pause
        __log__.debug(f'PLAYER | Set pause:: {self.paused} ({self.channel_id})')

    async def set_volume(self, vol: int) -> None:
        """|coro|

        Set the player's volume, between 0 and 1000.

        Parameters
        ------------
        vol: int
            The volume to set the player to.
        """
        self.volume = max(min(vol, 1000), 0)
        await self.node._send(op='volume', guildId=str(self.guild_id), volume=self.volume)
        __log__.debug(f'PLAYER | Set volume:: {self.volume} ({self.channel_id})')

    async def seek(self, position: int = 0) -> None:
        """Seek to the given position in the song.

        Parameters
        ------------
        position: int
            The position as an int in milliseconds to seek to. Could be None to seek to beginning.
        """

        await self.node._send(op='seek', guildId=str(self.guild_id), position=position)

    async def change_node(self, identifier: str = None) -> None:
        """|coro|

        Change the players current :class:`wavelink.node.Node`. Useful when a Node fails or when changing regions.
        The change Node behaviour allows for near seamless fallbacks and changeovers to occur.

        Parameters
        ------------
        Optional[identifier: str]
            An optional Node identifier to change to. If None, the next best available Node will be found.
        """
        client = self.node._client

        if identifier:
            node = client.get_node(identifier)

            if not node:
                raise WavelinkException(f'No Nodes matching identifier:: {identifier}')
            elif node == self.node:
                raise WavelinkException('Node identifiers must not be the same while changing.')
        else:
            self.node.close()
            node = None

            if self.node.region:
                node = client.get_node_by_region(self.node.region)

            if not node and self.node.shard_id:
                node = client.get_node_by_shard(self.node.shard_id)

            if not node:
                node = client.get_best_node()

            if not node:
                self.node.open()
                raise WavelinkException('No Nodes available for changeover.')

        self.node.open()

        old = self.node
        del old.players[self.guild_id]
        await old._send(op='destroy', guildId=str(self.guild_id))

        self.node = node
        self.node.players[int(self.guild_id)] = self

        if self._voice_state:
            await self._dispatch_voice_update()

        if self.current:
            await self.node._send(op='play', guildId=str(self.guild_id), track=self.current.id, startTime=int(self.position))
            self.last_update = time.time() * 1000

            if self.paused:
                await self.node._send(op='pause', guildId=str(self.guild_id), pause=self.paused)

        if self.volume != 100:
            await self.node._send(op='volume', guildId=str(self.guild_id), volume=self.volume)
