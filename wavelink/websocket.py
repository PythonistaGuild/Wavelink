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

import aiohttp
import asyncio
import logging
import sys
import traceback
from typing import Any, Dict, Tuple, TYPE_CHECKING

from .backoff import ExponentialBackoff
from .stats import Stats

if TYPE_CHECKING:
    from .node import Node
    from .player import Player

log = logging.getLogger(__name__)


class WebSocket:

    def __init__(self, node: Node, host: str, port: str, password: str, secure: bool):
        self.node = node
        self.client = node.client

        self.host = host
        self.port = port
        self.password = password
        self.secure = secure

        self.websocket = None
        self.last_exc = None
        self.task = None

    def is_connected(self) -> bool:
        return self.websocket is not None and not self.websocket.closed

    async def connect(self):
        await self.client.wait_until_ready()

        try:
            if self.secure is True:
                uri = f'wss://{self.host}:{self.port}'
            else:
                uri = f'ws://{self.host}:{self.port}'

            if not self.is_connected():
                headers = {'Authorization': self.password,
                           'Num-Shards': str(self.client.shard_count or 1),
                           'User-Id': str(self.client.user.id)}
                self.websocket = await self.node._session.ws_connect(uri, headers=headers, heartbeat=self.node.heartbeat)

        except Exception as error:
            self.last_exc = error
            self.node.available = False

            if isinstance(error, aiohttp.WSServerHandshakeError) and error.status == 401:
                print(f'\nAuthorization Failed for Node:: {self.node}\n', file=sys.stderr)
            else:
                log.error(f'WEBSOCKET | Connection Failure:: {error}')
                traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            return

        if not self.task:
            self.task = self.client.loop.create_task(self._listen())

        self.last_exc = None
        self.node._available = True

        if self.is_connected:
            self.dispatch('node_ready', self.node)
            log.debug('WEBSOCKET | Connection established...%s', self.node.__repr__())

    def dispatch(self, event, *args, **kwargs):
        self.client.dispatch(f'wavelink_{event}', *args, **kwargs)

    async def _listen(self):
        backoff = ExponentialBackoff(base=7)

        while True:
            msg = await self.websocket.receive()

            if msg.type is aiohttp.WSMsgType.CLOSED:
                log.debug(f'WEBSOCKET | Close data: {msg.extra}')

                retry = backoff.delay()
                log.warning(f'\nWEBSOCKET | Connection closed:: Retrying connection in <{retry}> seconds\n')

                await asyncio.sleep(retry)
                if not self.is_connected:
                    self.client.loop.create_task(self._connect())
            else:
                log.debug(f'WEBSOCKET | Received Payload:: <{msg.data}>')
                self.client.loop.create_task(self.process_data(msg.json()))

    async def process_data(self, data: Dict[str, Any]):
        op = data.get('op', None)
        if not op:
            return

        if op == 'stats':
            self.node.stats = Stats(self.node, data)
            return

        try:
            player: Player = self.node.get_player(self.client.get_guild(int(data['guildId'])))  # type: ignore
        except KeyError:
            return

        if op == 'event':
            event, payload = self._get_event_payload(data['type'], data)
            log.debug(f'WEBSOCKET | op: event:: {data}')
            self.dispatch(event, player, **payload)

        elif op == 'playerUpdate':
            log.debug(f'WEBSOCKET | op: playerUpdate:: {data}')
            try:
                await player.update_state(data)
            except KeyError:
                pass

    def _get_event_payload(self, name: str, data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        event = 'event'
        payload: Dict[str, Any] = {}

        if name == 'WebSocketClosedEvent':
            event = 'websocket_closed'
            payload['reason'] = data.get('reason')
            payload['code'] = data.get('code')

        if name.startswith('Track'):
            payload['track'] = data.get('track')

            if name == 'TrackEndEvent':
                event = 'track_end'
                payload['reason'] = data.get('reason')

            elif name == 'TrackStartEvent':
                event = 'track_start'

            elif name == 'TrackExceptionEvent':
                event = 'track_exception'
                payload['error'] = data.get('error')

            elif name == 'TrackStuckEvent':
                event = 'track_stuck'
                threshold = data.get('thresholdMs')
                if isinstance(threshold, str):
                    payload['threshold'] = int(threshold)

        return event, payload

    async def send(self, **data):
        if self.is_connected:
            log.debug(f'WEBSOCKET | Sending Payload:: {data}')
            await self.websocket.send_json(data)
