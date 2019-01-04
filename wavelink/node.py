import logging
from discord.ext import commands
from typing import Optional, Union
from urllib.parse import quote

from .player import Player, Track
from .websocket import WebSocket


__log__ = logging.getLogger(__name__)


class Node:

    def __init__(self, host: str, port: int, shards: int, user_id: int, *, session, rest_uri: str, password: str,
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

    def __repr__(self):
        return f'{self.identifier}-{self.host}:{self.port}|{self.region}(Shard: {self.shard_id})'

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

            __log__.debug(f'REST | Found <{len(tracks)}> tracks with query:: <{query}>')

            return tracks

    def get_player(self, guild_id: int) -> Optional[Player]:
        return self.players.get(guild_id, None)

    async def on_event(self, event):
        __log__.info(f'NODE | Event dispatched:: <{str(event)}>')
        await event.player.hook(event)

    async def _send(self, **data):
        __log__.debug(f'NODE | Sending payload:: <{data}>')
        await self._websocket._send(**data)
