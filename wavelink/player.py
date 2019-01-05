"""MIT License

Copyright (c) 2019 EvieePy(MysterialPy)

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
from discord.ext import commands
from discord.gateway import DiscordWebSocket
from typing import Optional, Union

from .errors import *


__log__ = logging.getLogger(__name__)


class Track:

    __slots__ = ('id', 'info', 'query', 'title', 'ytid', 'length', 'duration', 'uri', 'is_stream', 'dead')

    def __init__(self, id_, info, query=None):
        self.id = id_
        self.info = info
        self.query = query

        self.title = info.get('title')
        self.ytid = info.get('identifier')
        self.length = info.get('length')
        self.duration = self.length
        self.uri = info.get('uri')

        self.is_stream = info.get('isStream')
        self.dead = False

    def __str__(self):
        return self.title

    @property
    def is_dead(self):
        return self.dead


class Player:

    def __init__(self, bot: Union[commands.Bot, commands.AutoShardedBot], guild_id: int, node):
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
        self.channel_id = None

    @property
    def is_connected(self):
        """ Returns whether the player is connected to a voicechannel or not """
        return self.channel_id is not None

    @property
    def is_playing(self):
        """ Returns the player's track state. """
        return self.is_connected and self.current is not None

    @property
    def position(self):
        if not self.is_playing:
            return 0

        if self.paused:
            return min(self.last_position, self.current.duration)

        difference = (time.time() * 1000) - self.last_update
        return min(self.last_position + difference, self.current.duration)

    async def update_state(self, state: dict):
        state = state['state']

        self.last_update = time.time() * 1000
        self.last_position = state.get('position', 0)
        self.position_timestamp = state.get('time', 0)

    async def _voice_server_update(self, data):
        self._voice_state.update({
            'event': data
        })

        await self._dispatch_voice_update()

    async def _voice_state_update(self, data):
        self._voice_state.update({
            'sessionId': data['session_id']
        })

        self.channel_id = data['channel_id']

        if not self.channel_id:  # We're disconnecting
            self._voice_state.clear()
            return

        await self._dispatch_voice_update()

    async def _dispatch_voice_update(self):
        __log__.debug(f'PLAYER | Dispatching voice update:: {self.channel_id}')
        if {'sessionId', 'event'} == self._voice_state.keys():
            await self.node._send(op='voiceUpdate', guildId=str(self.guild_id), **self._voice_state)

    async def hook(self, event):
        pass

    def _get_shard_socket(self, shard_id: int) -> Optional[DiscordWebSocket]:
        if self.bot.shard_id is None:
            return self.bot.ws

        return self.bot.shards[shard_id].ws

    async def connect(self, channel_id: int):
        guild = self.bot.get_guild(self.guild_id)
        if not guild:
            raise InvalidIDProvided(f'No guild found for id <{self.guild_id}>')

        self.channel_id = channel_id
        await self._get_shard_socket(guild.shard_id).voice_state(self.guild_id, str(channel_id))
        __log__.info(f'PLAYER | Connected to voice channel:: {self.channel_id}')

    async def disconnect(self):
        guild = self.bot.get_guild(self.guild_id)
        if not guild:
            raise InvalidIDProvided(f'No guild found for id <{self.guild_id}>')

        __log__.info(f'PLAYER | Disconnected from voice channel:: {self.channel_id}')
        self.channel_id = None
        await self._get_shard_socket(guild.shard_id).voice_state(self.guild_id, None)

    async def play(self, track):
        self.last_update = 0
        self.last_position = 0
        self.position_timestamp = 0
        self.paused = False

        await self.node._send(op='play', guildId=str(self.guild_id), track=track.id)
        __log__.debug(f'PLAYER | Started playing track:: {str(track)} ({self.channel_id})')
        self.current = track

    async def stop(self):
        await self.node._send(op='stop', guildId=str(self.guild_id))
        __log__.debug(f'PLAYER | Current track stopped:: {str(self.current)} ({self.channel_id})')
        self.current = None

    async def set_pause(self, pause: bool):
        await self.node._send(op='pause', guildId=str(self.guild_id), pause=pause)
        self.paused = pause
        __log__.debug(f'PLAYER | Set pause:: {self.paused} ({self.channel_id})')

    async def set_volume(self, vol: int):
        self.volume = max(min(vol, 1000), 0)
        await self.node._send(op='volume', guildId=str(self.guild_id), volume=self.volume)
        __log__.debug(f'PLAYER | Set volume:: {self.volume} ({self.channel_id})')

    async def change_node(self, identifier: str=None):
        client = self.node._client

        if identifier:
            node = client.get_node(identifier)

            if not node:
                raise WavelinkException(f'No Nodes matching identifier:: {identifier}')
            elif node == self.node:
                raise WavelinkException('Node identifiers must not be the same while changing')
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