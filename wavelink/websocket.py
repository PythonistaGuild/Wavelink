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
import aiohttp
import asyncio
import logging
import sys
import traceback
from typing import Any, Dict

from .backoff import ExponentialBackoff
from .events import *
from .stats import Stats
from .errors import NodeSessionClosedError

__log__ = logging.getLogger(__name__)

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
        self.force_send_queue = attrs.get('force_send_queue', False) # Send queue regardless of session resume
        self.queue = []
        self.session_resumed = False # to check if the session was resumed 
        self.resume_session = attrs.get('resume_session', False)
        if self.resume_session:
            self.resume_timeout = attrs.get('resume_timeout', 60)
            # self.resume_key is casted to str to allow a Key object with __repr__ method.
            # Useful if the class implements it's own method to generate keys.
            # logger's level should be set to warning if stdout is vulnurable. eg: shared VPS
            self.resume_key = attrs.get('resume_key', None)
            if self.resume_key is None:
                import secrets # Don't import unless resuming is enabled
                import string
                alphabet = string.ascii_letters + string.digits
                self.resume_key = ''.join(secrets.choice(alphabet) for i in range(32))
        
        self._can_resume = False
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
                # Send queued messages if header not present but possibilty that session is resumed.
                # if First connect then this will be false
                self.session_resumed = self._websocket._response.headers.get('Session-Resumed', self._can_resume)
                if not self.session_resumed and self.headers.has_key('Resume-Key'):
                    raise NodeSessionClosedError(f'{repr(self._node)} | Session was closed. All Players may have been shut down')
                elif self.session_resumed:
                    __log__.info(f"WEBSOCKET | {repr(self._node)} | Resumed Session with key: {self.resume_key}")
                
        except NodeSessionClosedError:
            __log__.warning(f"WEBSOCKET | {repr(self._node)} | Closed Session due to timeout.") # Error Not Fatal enough to return
            
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
            self._task = self.bot.loop.create_task(self._listen())

        self._last_exc = None
        self._closed = False
        self._node.available = True

        if self.is_connected:
            await self.client._dispatch_listeners('on_node_ready', self._node)
            __log__.debug('WEBSOCKET | Connection established...%s', self._node.__repr__())
            self.bot.loop.create_task(self._send_queue())
            if not self._can_resume:
                self.bot.loop.create_task(self._configure_resume())

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
                    self.bot.loop.create_task(self._connect())
            else:
                __log__.debug(f'WEBSOCKET | Received Payload:: <{msg.data}>')
                self.bot.loop.create_task(self.process_data(msg.json()))

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

            listener, payload = self._get_event_payload(data['type'], data)

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

    def _get_event_payload(self, name: str, data):
        if name == 'TrackEndEvent':
            return 'on_track_end', TrackEnd(data)
        elif name == 'TrackStartEvent':
            return 'on_track_start', TrackStart(data)
        elif name == 'TrackExceptionEvent':
            return 'on_track_exception', TrackException(data)
        elif name == 'TrackStuckEvent':
            return 'on_track_stuck', TrackStuck(data)
        elif name == 'WebSocketClosedEvent':
            return 'on_websocket_closed', WebsocketClosed(data)
        
    async def _send_queue(self):
        count = 0
        for data in self.queue:
            if self.is_connected and (self.session_resumed or self.force_send_queue):
                await self._send(**data) # Don't send messages too quickly.
                count += 1
            else:
                break
        else:
            del self.queue[0:count] # delete the sent data & continue at next reconnect.
            return None
            
    async def _send(self, **data):
        if self.is_connected:
            __log__.debug(f'WEBSOCKET | Sending Payload:: {data}')
            await self._websocket.send_json(data)
        else:
            __log__.debug(f'WEBSOCKET | Queueing Payload:: {data}')
            self.queue.append(data)
