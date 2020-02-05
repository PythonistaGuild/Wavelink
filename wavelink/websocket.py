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
import asyncio
import json
import logging
import sys
import traceback
import websockets
from discord.ext import commands
from typing import Union

from .backoff import ExponentialBackoff
from .events import *
from .stats import Stats


__log__ = logging.getLogger(__name__)


class WebSocket:

    def __init__(self, bot: Union[commands.Bot, commands.AutoShardedBot], node, host: str, port: int,
                 password: str, shard_count: int, user_id: int, secure: bool):
        self.bot = bot
        self.host = host
        self.port = port
        self.password = password
        self.shard_count = shard_count
        self.user_id = user_id
        self.secure = secure

        self._websocket = None
        self._last_exc = None
        self._task = None

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
            if self.secure is True:
                uri = f'wss://{self.host}:{self.port}'
            else:
                uri = f'ws://{self.host}:{self.port}'

            if not self.is_connected:
                self._websocket = await websockets.connect(uri=uri, extra_headers=self.headers)

        except Exception as error:
            self._last_exc = error
            self._node.available = False

            __log__.error(f'WEBSOCKET | Connection Failure:: {error}')
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            return

        if not self._task:
            self._task = self.bot.loop.create_task(self._listen())

        self._last_exc = None
        self._closed = False
        self._node.available = True

        if self.is_connected:
            print(f'\nWAVELINK:WEBSOCKET | Connection established::{self._node.__repr__()}\n')
            __log__.debug('WEBSOCKET | Connection established...%s', self._node.__repr__())

    async def _listen(self):
        backoff = ExponentialBackoff(base=7)

        while True:
            try:
                data = await self._websocket.recv()
                __log__.debug(f'WEBSOCKET | Received Payload:: <{data}>')
            except websockets.ConnectionClosed as e:
                self._last_exc = e

                if e.code == 4001:
                    print(f'\nAuthorization Failed for Node:: {self._node}\n', file=sys.stderr)
                    break

                self._closed = True
                retry = backoff.delay()

                __log__.warning(f'\nWEBSOCKET | Connection closed:: Retrying connection in <{retry}> seconds\n')

                await asyncio.sleep(retry)
                if not self.is_connected:
                    self.bot.loop.create_task(self._connect())
            else:
                self.bot.loop.create_task(self.process_data(data))

    async def process_data(self, data: str):
        data = json.loads(data)

        op = data.get('op', None)
        if not op:
            return

        if op == 'stats':
            self._node.stats = Stats(self._node, data)
        if op == 'event':
            try:
                data['player'] = self._node.players[int(data['guildId'])]
            except KeyError:
                return

            event = self._get_event(data['type'], data)

            __log__.debug(f'WEBSOCKET | op: event:: {data}')

            try:
                await self._node.on_event(event)
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__, file=sys.stderr)

        elif op == 'playerUpdate':
            __log__.debug(f'WEBSOCKET | op: playerUpdate:: {data}')
            try:
                await self._node.players[int(data['guildId'])].update_state(data)
            except KeyError:
                pass

    def _get_event(self, name: str, data) -> Union[TrackEnd, TrackException, TrackStuck, WebsocketClosed]:
        if name == 'TrackEndEvent':
            return TrackEnd(data['player'], data.get('track', None), data.get('reason', None))
        elif name == 'TrackExceptionEvent':
            return TrackException(data['player'], data['track'], data['error'])
        elif name == 'TrackStuckEvent':
            return TrackStuck(data['player'], data['track'], int(data['threshold']))
        elif name == 'WebSocketClosedEvent':
            return WebsocketClosed(data['player'], data['reason'], data['code'], data['guildId'])

    async def _send(self, **data):
        if self.is_connected:
            __log__.debug(f'WEBSOCKET | Sending Payload:: {data}')
            await self._websocket.send(json.dumps(data))
