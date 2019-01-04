import asyncio
import json
import logging
import websockets
from discord.ext import commands
from typing import Union

from .backoff import ExponentialBackoff
from .events import *


__log__ = logging.getLogger(__name__)


class WebSocket:

    def __init__(self, bot: Union[commands.Bot, commands.AutoShardedBot], node, host: str, port: int,
                 password: str, shard_count: int, user_id: int):
        self.bot = bot
        self.host = host
        self.port = port
        self.password = password
        self.shard_count = shard_count
        self.user_id = user_id

        self._websocket = None
        self._last_exc = None

        self._node = node

    @property
    def headers(self):
        return {'Authorization': self.password,
                'Num-Shards': self.shard_count,
                'User-Id': str(self.user_id)}

    @property
    def is_connected(self) -> bool:
        return self._websocket is not None and self._websocket.open

    async def _connect(self):
        await self.bot.wait_until_ready()

        try:
            self._websocket = await websockets.connect(uri=f'ws://{self.host}:{self.port}', extra_headers=self.headers)
        except Exception as e:
            self._last_exc = e

        asyncio.create_task(self._listen())
        self._closed = False

    async def _listen(self):
        backoff = ExponentialBackoff()

        if not self.is_connected and self._last_exc:
            __log__.error(f'WEBSOCKET | Connection failure:: {self._last_exc}')
            raise websockets.ConnectionClosed(reason=f'Websocket connection failure:\n\n{self._last_exc}', code=1006)

        while True:
            try:
                data = json.loads(await self._websocket.recv())
                __log__.debug(f'WEBSOCKET | Received Payload:: <{data}>')
            except websockets.ConnectionClosed:
                self._closed = True
                retry = backoff.delay()

                __log__.warning(f'WEBSOCKET | Connection closed:: Retrying connection in <{retry}> seconds')

                await self._connect()
                await asyncio.sleep(retry)
                continue

            op = data.get('op', None)
            if not op:
                continue

            if op == 'event':
                data['player'] = self._node.players[int(data['guildId'])]
                event = self._get_event(data['type'], data)

                __log__.debug(f'WEBSOCKET | op: event:: {data}')
                await self._node.on_event(event)
            elif op == 'playerUpdate':
                __log__.debug(f'WEBSOCKET | op: playerUpdate:: {data}')
                await self._node.players[int(data['guildId'])].update_state(data)

    def _get_event(self, name: str, data) -> Union[TrackEnd, TrackException, TrackStuck]:
        if name == 'TrackEndEvent':
            return TrackEnd(data['player'], data['track'], data['reason'])
        elif name == 'TrackExceptionEvent':
            return TrackException(data['player'], data['track'], data['error'])
        elif name == 'TrackStuckEvent':
            return TrackStuck(data['player'], data['track'], int(data['threshold']))

    async def _send(self, **data):
        if self.is_connected:
            __log__.debug(f'WEBSOCKET | Sending Payload:: {data}')
            await self._websocket.send(json.dumps(data))
