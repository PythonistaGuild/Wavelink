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
import secrets
import string
import sys
import time
import traceback
from types import MappingProxyType
from typing import Any, Dict

import aiohttp

from .backoff import ExponentialBackoff
from .errors import NodeSessionClosedError
from .events import *
from .stats import Stats

__log__ = logging.getLogger(__name__)

EventMapping = MappingProxyType(
    {
        "TrackEndEvent": ("on_track_end", TrackEnd),
        "TrackStartEvent": ("on_track_start", TrackStart),
        "TrackExceptionEvent": ("on_track_exception", TrackException),
        "TrackStuckEvent": ("on_track_stuck", TrackStuck),
        "WebSocketClosedEvent": ("on_websocket_closed", WebsocketClosed),
    }
)


class _TimedQueue(asyncio.Queue):
    def __init__(self, maxsize=0, *, loop=None, timeout):
        self._timeout = timeout
        super().__init__(maxsize, loop=loop)

    def _get(self):
        item = self._queue.popleft()
        StampDiff = time.time() - item[0]
        if StampDiff > self._timeout:
            return None
        else:
            return item[1]

    def _put(self, item):
        self._queue.append((time.time(), item))

    def clear(self):
        self._queue.clear()

class _Key:
    def __init__(self, Len: int = 32):
        self.Len: int = Len
        self.persistent: str = ""
        self.__repr__()

    def __repr__(self):
        """Generate a new key, return it and make it persistent"""
        alphabet = string.ascii_letters + string.digits + "#$%&()*+,-./:;<=>?@[]^_~!"
        key = ''.join(secrets.choice(alphabet) for i in range(self.Len))
        self.persistent = key
        return key

    def __str__(self):
        """Return the persistent key."""
        # Ensure output is not a non-string
        # Since input could be Any object.
        if not self.persistent:
            return self.__repr__()
        return str(self.persistent)

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
            # As resuming key is logged.
            self.resume_key = attrs.get('resume_key')
            if self.resume_key is None:
                self.resume_key = self._gen_key()

        self._can_resume = False
        # Dont initialze when not used.
        if self.resume_session:
            self._queue = _TimedQueue(0, loop=self.client.loop, timeout=self.payload_timeout)
        self._websocket = None
        self._last_exc = None
        self._task = None

    @property
    def headers(self) -> dict:
        base = {'Authorization': self.password,
                'Num-Shards': str(self.shard_count),
                'User-Id': str(self.user_id)}
        if not self._can_resume:
            return base
        elif self._can_resume:
            return base.update({'Resume-Key': str(self.resume_key)})

    @property
    def is_connected(self) -> bool:
        return self._websocket is not None and not self._websocket.closed

    def _gen_key(self, Len=32):
        if self.resume_key is None:
            return _Key()
        else:
            # if this is a class then it will generate a persistent key
            # We should not't check the instance since
            # we would still make 1 extra call to check, which is useless.
            self.resume_key.__repr__()
            return self.resume_key

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
                self.session_resumed = self._websocket._response.headers.get('Session-Resumed', self._can_resume)
                if not self.session_resumed and self._can_resume:
                    raise NodeSessionClosedError(f'{repr(self._node)} | Session was closed due to timeout. All Players may have been disconnected')
                elif self.session_resumed:
                    __log__.info(f"WEBSOCKET | {repr(self._node)} | Resumed Session with key: {self.resume_key}")

        except NodeSessionClosedError:
            __log__.warning(f"WEBSOCKET | {repr(self._node)} | Closed Session due to timeout.") # Error Not Fatal enough to return
            # This exception raised when we can resume hence queue is initialized.
            self._queue.clear() # Clear queue
            # Generate a new key
            self.resume_key = self._gen_key()
            self._can_resume = False
            self.client.loop.create_task(self._configure_resume())

        except Exception as error:
            self._can_resume = False
            self._last_exc = error
            self._node.available = False
            if isinstance(error, aiohttp.WSServerHandshakeError) and error.status == 401:
                __log__.critical(f'\nAuthorization Failed for Node:: {self._node}\n')
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
                # Send only on resume.
                self.client.loop.create_task(self._send_queue())

    async def _listen(self):
        backoff = ExponentialBackoff(base=7)
        # This is an approximatly the no. of seconds we have been disconnected for.
        # This is the easiest implementation, other ways are more sophisticated
        # but we shalln't add attrs to class or globals as disconnects are usually rare.
        down_time = 0.0
        while True:
            msg = await self._websocket.receive()

            if msg.type is aiohttp.WSMsgType.CLOSED:
                __log__.debug(f'WEBSOCKET | Close data: {msg.extra}')

                self._closed = True
                retry = backoff.delay()
                if self._can_resume and retry >= self.resume_timeout and down_time < self.timeout:
                    backoff._exp = 0
                    retry = backoff.delay()

                __log__.warning(f'\nWEBSOCKET | Connection closed:: Retrying connection in <{retry}> seconds\n')
                down_time += retry

                await asyncio.sleep(retry)
                if not self.is_connected:
                    self.client.loop.create_task(self._connect())
            else:
                down_time = 0.0
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

            try:
                listener, payload_type = EventMapping[data['type']]
                payload = payload_type(data)
            except KeyError:
                __log__.exception('Unknown Event received!')
                return

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

    async def close(self):
        # Lavalink server currently doesn't close session immediately on 1000 (if session resuming is enabled)
        # so we send a payload to disable resuming. It has been documented in lavalink implementation guide.
        # TODO: Remove disable payload when Lavalink adds 1000 functionality
        if self._can_resume:
            await self._send(op='configureResuming', key=None)
        await self._websocket.close(message=b'Node destroy request.')
        self._closed = True
        self._node.available = False
        # We have disabled resuming.
        self._can_resume = False
        __log__.debug("WEBSOCKET | Closed websocket connection gracefully with code 1000.")
        return

    async def reset(self):
        if isinstance(self.resume_key, str):
            pass
        elif isinstance(self.resume_key, _Key):
            self.resume_key = None
            self.resume_key = self._gen_key()
        else:
            pass

        if self.resume_session:
            self._can_resume = False
            self._queue.clear()

        try:
            self._task.cancel()
        except Exception:
            __log__.debug("Error while cancelling task", exc_info=True)
        finally:
            self._task = None
        await self.close()
        await self._connect()
