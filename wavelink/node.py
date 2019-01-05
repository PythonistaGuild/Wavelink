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
import inspect
import logging
from discord.ext import commands
from typing import Optional, Union
from urllib.parse import quote

from .errors import *
from .player import Player, Track
from .websocket import WebSocket


__log__ = logging.getLogger(__name__)


class Node:

    def __init__(self, host: str, port: int, shards: int, user_id: int, *, client, session, rest_uri: str, password: str,
                 region: str, identifier: str, shard_id: int=None):
        self.host = host
        self.port = port
        self.rest_uri = rest_uri
        self.shards = shards
        self.uid = user_id
        self.password = password
        self.region = region
        self.identifier = identifier

        self.shard_id = shard_id

        self.players = {}

        self.session = session
        self._websocket = None
        self._client = client

        self.hook = None
        self.available = True

        self.stats = None

    def __repr__(self):
        return f'{self.identifier} - ({self.host}:{self.port}) | {self.region} | (Shard: {self.shard_id})'

    @property
    def is_available(self) -> bool:
        return self._websocket.is_connected and self.available

    def close(self):
        self.available = False

    def open(self):
        self.available = True

    @property
    def penalty(self):
        """Returns the load-balancing penalty for this node."""
        if not self.available or not self.stats:
            return 9e30

        return self.stats.penalty.total

    async def connect(self, bot: Union[commands.Bot, commands.AutoShardedBot]):
        self._websocket = WebSocket(bot, self, self.host, self.port, self.password, self.shards, self.uid)
        await self._websocket._connect()

        __log__.info(f'NODE | {self.identifier} connected:: {self.__repr__()}')

    async def get_tracks(self, query: str) -> Optional[list]:
        async with self.session.get(f'{self.rest_uri}/loadtracks?identifier={quote(query)}',
                                    headers={'Authorization': self.password}) as resp:
            data = await resp.json()

            if not data['tracks']:
                __log__.info(f'REST | No tracks with query:: <{query}> found.')
                return None

            tracks = []
            for track in data['tracks']:
                tracks.append(Track(id_=track['track'], info=track['info']))

            __log__.debug(f'REST | Found <{len(tracks)}> tracks with query:: <{query}> ({self.__repr__()})')

            return tracks

    def get_player(self, guild_id: int) -> Optional[Player]:
        return self.players.get(guild_id, None)

    async def on_event(self, event):
        __log__.info(f'NODE | Event dispatched:: <{str(event)}> ({self.__repr__()})')
        await event.player.hook(event)

        if not self.hook:
            return

        if inspect.iscoroutinefunction(self.hook):
            await self.hook(event)
        else:
            self.hook(event)

    def set_hook(self, func):
        if not callable(func):
            raise WavelinkException('Node hook must be a callable.')

        self.hook = func

    async def _send(self, **data):
        __log__.debug(f'NODE | Sending payload:: <{data}> ({self.__repr__()})')
        await self._websocket._send(**data)
