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
import logging
import sys
import time
import traceback
from json import loads
from typing import Any, Dict

import aiohttp

from .backoff import ExponentialBackoff
from .errors import NodeSessionClosedError
from .events import *
from .stats import Stats

__log__ = logging.getLogger(__name__)

class _Payload:
    def __init__(self, data, StampDiff, timeout):
        self._data = data
        self._stampdiff = StampDiff
        self._timeout = timeout

    @property
    def payload(self):
        if self._stampdiff > self._timeout:
            return None
        else:
            return self._data

class _TimedQueue(asyncio.Queue):
    def __init__(self, maxsize=0, *, loop=None, timeout):
        self._timeout = timeout
        super().__init__(maxsize, loop=loop)

    def _get(self):
        item = self._queue.popleft()
        StampDiff = time.time() - item[0]
        return _Payload(item[1], StampDiff, self._timeout).payload

    def _put(self, item):
        self._queue.append((time.time(), item))

    def clear(self):
        self._queue.clear()

class WebSocket:

    def __init__(self, **attrs):
        self._node = attrs.get('node')
        self.client = self._node._client
        self.bot = self.client.bot
        self.host = attrs.get('host')
        self.port = attrs.get('port')
        self.password = attrs.get('password')
        self.shard_count = attrs.get('shard_count')
        self.user_id = attrs.get('user_id')
        self.secure = attrs.get('secure')
        # Send queue regardless of session resume.
        # Operations take 20 to 1 ms
        self.payload_timeout = attrs.get('payload_timeout')
        self.session_resumed = False # To check if the session was resumed.
        self.resume_session = attrs.get('resume_session')
        if self.resume_session:
            self.resume_timeout = attrs.get('resume_timeout')
            # self.resume_key is casted to str to allow a Key object with __repr__ method.
            # Useful if the class implements it's own method to generate keys.
            # logger's level should be set to warning if stdout is vulnurable. eg: shared VPS
            self.resume_key = attrs.get('resume_key')
            if self.resume_key is None:
                import secrets # Don't import unless resuming is enabled
                import string
                alphabet = string.ascii_letters + string.digits
                self.resume_key = ''.join(secrets.choice(alphabet) for i in range(32))

        self._can_resume = False
        # Dont initialze when not used.
        if self.resume_session:
            self._queue = _TimedQueue(0, loop=self.client.loop, timeout=self.payload_timeout)
        self._websocket = None
        self._last_exc = None
        self._task = None

    @property
    def headers(self) -> dict:
        if not self._can_resume: # can't resume
            return {'Authorization': self.password,
                    'Num-Shards': str(self.shard_count),
                    'User-Id': str(self.user_id)}
        elif self._can_resume:
            return {'Authorization': self.password,
                    'Num-Shards': str(self.shard_count),
                    'User-Id': str(self.user_id),
                    'Resume-Key': str(self.resume_key)}

    @property
    def is_connected(self) -> bool:
        return self._websocket is not None and not self._websocket.closed

    async def _configure_resume(self) -> None:
        if self._can_resume:
            return
        elif self.resume_session:
            await self._send(op='configureResuming', key=str(self.resume_key), timeout=self.resume_timeout)
            __log__.info(f"WEBSOCKET | {repr(self._node)} | Resuming configured with Key {self.resume_key}")
            self._can_resume = True
            return

    async def _connect(self):
        await self.bot.wait_until_ready()

        try:
            if self.secure is True:
                uri = f'wss://{self.host}:{self.port}'
            else:
                uri = f'ws://{self.host}:{self.port}'

            if not self.is_connected:
                self._websocket = await self._node.session.ws_connect(uri, headers=self.headers, heartbeat=self._node.heartbeat)
                # If header not present then account for possibilty that session is resumed.
                # if First connect then this will be false.
                self.session_resumed = loads(self._websocket._response.headers.get('Session-Resumed', self._can_resume))
                if not self.session_resumed and self._can_resume:
                    raise NodeSessionClosedError(f'{repr(self._node)} | Session was closed. All Players may have been shut down')
                elif self.session_resumed:
                    __log__.info(f"WEBSOCKET | {repr(self._node)} | Resumed Session with key: {self.resume_key}")

        except NodeSessionClosedError:
            __log__.warning(f"WEBSOCKET | {repr(self._node)} | Closed Session due to timeout.") # Error Not Fatal enough to return
            self._queue.clear() # Clear queue
        except Exception as error:
            self._last_exc = error
            self._node.available = False
            if isinstance(error, aiohttp.WSServerHandshakeError) and error.status == 401:
                print(f'\nAuthorization Failed for Node:: {self._node}\n', file=sys.stderr)
            else:
                __log__.error(f'WEBSOCKET | Connection Failure:: {error}')
                traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            return

        if not self._task:
            self._task = self.client.loop.create_task(self._listen())

        self._last_exc = None
        self._closed = False
        self._node.available = True

        if self.is_connected:
            await self.client._dispatch_listeners('on_node_ready', self._node)
            __log__.debug('WEBSOCKET | Connection established...%s', self._node.__repr__())
            if not self._can_resume:
                self.client.loop.create_task(self._configure_resume())
            if self.session_resumed:
                # Send only on resume or when forced.
                self.client.loop.create_task(self._send_queue())

    async def _listen(self):
        backoff = ExponentialBackoff(base=7)
        tries = 0
        while True:
            msg = await self._websocket.receive()

            if msg.type is aiohttp.WSMsgType.CLOSED:
                __log__.debug(f'WEBSOCKET | Close data: {msg.extra}')

                self._closed = True
                if not self._can_resume:
                    retry = backoff.delay()
                elif self._can_resume and tries < 2: # hand off to Exponential backoff after atleast 2 tries
                    if self.resume_timeout <= 70:
                        retry = (self.resume_timeout / 2.0) - 1.0 # Account for latency.
                    else: # try_after 30 seconds 2 times and then hand over to exponential backoff.
                        retry = 30.0

                __log__.warning(f'\nWEBSOCKET | Connection closed:: Retrying connection in <{retry}> seconds\n')

                await asyncio.sleep(retry)
                if not self.is_connected:
                    self.client.loop.create_task(self._connect())
            else:
                __log__.debug(f'WEBSOCKET | Received Payload:: <{msg.data}>')
                self.client.loop.create_task(self.process_data(msg.json()))

    async def process_data(self, data: Dict[str, Any]):
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

            name = data['type']
            if name == 'TrackEndEvent':
                listener, payload = 'on_track_end', TrackEnd(data)
            elif name == 'TrackStartEvent':
                listener, payload = 'on_track_start', TrackStart(data)
            elif name == 'TrackExceptionEvent':
                listener, payload = 'on_track_exception', TrackException(data)
            elif name == 'TrackStuckEvent':
                listener, payload = 'on_track_stuck', TrackStuck(data)
            elif name == 'WebSocketClosedEvent':
                listener, payload = 'on_websocket_closed', WebsocketClosed(data)
            __log__.debug(f'WEBSOCKET | op: event:: {data}')

            # Dispatch node event/player hooks
            try:
                await self._node.on_event(payload)
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__, file=sys.stderr)

            # Dispatch listeners
            await self.client._dispatch_listeners(listener, self._node, payload)

        elif op == 'playerUpdate':
            __log__.debug(f'WEBSOCKET | op: playerUpdate:: {data}')
            try:
                await self._node.players[int(data['guildId'])].update_state(data)
            except KeyError:
                pass

    async def _send_queue(self):
        # send while connected, resume on reconnect
        while self.is_connected:
            try:
                data = self._queue.get_nowait()
            except asyncio.QueueEmpty:
                return
            if data is not None:
                await self._send(**data.payload)
            else:
                pass

    async def _send(self, **data):
        if self.is_connected:
            __log__.debug(f'WEBSOCKET | Sending Payload:: {data}')
            await self._websocket.send_json(data)
        elif self.resume_session:
            __log__.debug(f'WEBSOCKET | Queueing Payload:: {data}')
            # we don't need to catch QueueFull as maxsize is 0
            self._queue.put_nowait(data)
