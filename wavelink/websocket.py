"""
MIT License

Copyright (c) 2019-Present PythonistaGuild

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

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Optional

import aiohttp

import wavelink

from . import __version__
from .backoff import Backoff
from .enums import NodeStatus, TrackEventType
from .exceptions import *
from .payloads import TrackEventPayload, WebsocketClosedPayload

if TYPE_CHECKING:
    from .node import Node
    from .player import Player


logger: logging.Logger = logging.getLogger(__name__)


class Websocket:

    __slots__ = (
        'node',
        'socket',
        'retries',
        'retry',
        '_original_attempts',
        'backoff',
        '_listener_task',
        '_reconnect_task'
    )

    def __init__(self, *, node: Node) -> None:
        self.node: Node = node
        self.socket: aiohttp.ClientWebSocketResponse | None = None

        self.retries: int | None = node._retries
        self.retry: float = 1
        self._original_attempts: int | None = node._retries

        self.backoff: Backoff = Backoff()

        self._listener_task: asyncio.Task | None = None
        self._reconnect_task: asyncio.Task | None = None

    @property
    def headers(self) -> dict[str, str]:
        assert self.node.client is not None
        assert self.node.client.user is not None

        return {
            'Authorization': self.node.password,
            'User-Id': str(self.node.client.user.id),
            'Client-Name': f'Wavelink/{__version__}'
        }

    def is_connected(self) -> bool:
        return self.socket is not None and not self.socket.closed

    async def connect(self) -> None:
        if self.node.status is NodeStatus.CONNECTED:
            logger.error(f'Node {self.node} websocket tried connecting in an already connected state. '
                         f'Disregarding.')
            return

        self.node._status = NodeStatus.CONNECTING

        if self._listener_task:
            try:
                self._listener_task.cancel()
            except Exception as e:
                logger.debug(f'Node {self.node} encountered an error while cancelling the websocket listener: {e}. '
                             f'This is likely not an issue and will not affect connection.')

        uri: str = self.node._host.removeprefix('https://').removeprefix('http://')

        if self.node._use_http:
            uri: str = f'{"https://" if self.node._secure else "http://"}{uri}'
        else:
            uri: str = f'{"wss://" if self.node._secure else "ws://"}{uri}'

        heartbeat: float = self.node.heartbeat

        try:
            self.socket = await self.node._session.ws_connect(url=uri, heartbeat=heartbeat, headers=self.headers)
        except Exception as e:
            if isinstance(e, aiohttp.WSServerHandshakeError) and e.status == 401:
                raise AuthorizationFailed from e
            else:
                logger.error(f'An error occurred connecting to node: "{self.node}". {e}')

        if self.is_connected():
            self.retries = self._original_attempts
            self._reconnect_task = None
            # TODO - Configure Resuming...
        else:
            await self._reconnect()
            return

        self._listener_task = asyncio.create_task(self._listen())

    async def _reconnect(self) -> None:
        self.node._status = NodeStatus.CONNECTING
        self.retry = self.backoff.calculate()

        if self.retries == 0:
            logger.error(f'Node {self.node} websocket was unable to connect, '
                         f'and has exhausted the reconnection attempt limit. '
                         'Please check your Lavalink Node is started and your connection details are correct.')

            await self.cleanup()
            return

        retries = f'{self.retries} attempt(s) remaining.' if self.retries else ''
        logger.error(f'Node {self.node} websocket was unable to connect, retrying connection in: '
                     f'"{self.retry}" seconds. {retries}')

        if self.retries:
            self.retries -= 1

        await asyncio.sleep(self.retry)
        await self.connect()

    async def _listen(self) -> None:
        while True:
            message = await self.socket.receive()

            if message.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSING):

                for player in self.node.players.copy().values():
                    await player._update_event(data=None)

                self._reconnect_task = asyncio.create_task(self._reconnect())
                return

            if message.data == 1011:
                logger.error(f'Node {self.node} websocket encountered an internal error which can not be resolved. '
                             'Make sure your Lavalink sever is up to date, and try restarting.')

                await self.cleanup()
                return

            if message.data is None:
                logger.info(f'Node {self.node} websocket received a message from Lavalink with empty data. '
                            f'Disregarding.')
                continue

            data = message.json()
            logger.debug(f'Node {self.node} websocket received a message from Lavalink: {data}')

            op = data.get('op', None)
            if not op:
                logger.info(f'Node {self.node} websocket payload "op" from Lavalink was None. Disregarding.')
                continue

            if op == 'ready':
                self.node._status = NodeStatus.CONNECTED
                self.node._session_id = data['sessionId']

                self.dispatch('node_ready', self.node)

            elif op == 'stats':
                payload = ...
                logger.debug(f'Node {self.node} websocket received a Stats Update payload: {data}')
                self.dispatch('stats_update', data)

            elif op == 'event':
                logger.debug(f'Node {self.node} websocket received an event payload: {data}')
                player = self.get_player(data)

                if data['type'] == 'WebSocketClosedEvent':
                    player = player or self.node._invalidated.get(int(data['guildId']), None)

                    if not player:
                        logger.debug(f'Node {self.node} received a WebsocketClosedEvent in an "unknown" state. '
                                     f'Disregarding.')
                        continue

                    if self.node._invalidated.get(player.guild.id):
                        await player._destroy()

                    logger.debug(f'Node {self.node} websocket acknowledged "WebsocketClosedEvent": '
                                 f'<code: {data["code"]}, reason: {data["reason"]}, by_discord: {data["byRemote"]}>. '
                                 f'Cleanup on player {player.guild.id} has been completed.')

                    payload: WebsocketClosedPayload = WebsocketClosedPayload(data=data, player=player)

                    self.dispatch('websocket_closed', payload)
                    continue

                if player is None:
                    logger.debug(f'Node {self.node} received a payload from Lavalink without an attached player. '
                                 f'Disregarding.')
                    continue

                track = await self.node.build_track(cls=wavelink.GenericTrack, encoded=data['encodedTrack'])
                payload: TrackEventPayload = TrackEventPayload(
                    data=data,
                    track=track,
                    player=player,
                    original=player._original
                )

                if payload.event is TrackEventType.END and payload.reason != 'REPLACED':
                    player._current = None

                self.dispatch('track_event', payload)

                if payload.event is TrackEventType.END:
                    self.dispatch('track_end', payload)
                    asyncio.create_task(player._auto_play_event(payload))

                elif payload.event is TrackEventType.START:
                    self.dispatch('track_start', payload)

            elif op == 'playerUpdate':
                player = self.get_player(data)
                if player is None:
                    logger.debug(f'Node {self.node} received a payload from Lavalink without an attached player. '
                                 f'Disregarding.')
                    continue

                await player._update_event(data)
                self.dispatch("player_update", data)
                logger.debug(f'Node {self.node} websocket received Player Update payload: {data}')

            else:
                logger.warning(f'Received unknown payload from Lavalink: <{data}>. '
                               f'If this continues consider making a ticket on the Wavelink GitHub. '
                               f'https://github.com/PythonistaGuild/Wavelink')

    def get_player(self, payload: dict[str, Any]) -> Optional['Player']:
        return self.node.players.get(int(payload['guildId']), None)

    def dispatch(self, event, *args: Any, **kwargs: Any) -> None:
        self.node.client.dispatch(f"wavelink_{event}", *args, **kwargs)
        logger.debug(f'Node {self.node} is dispatching an event: "on_wavelink_{event}".')

    # noinspection PyBroadException
    async def cleanup(self) -> None:
        try:
            await self.socket.close()
        except AttributeError:
            pass

        try:
            self._listener_task.cancel()
        except Exception:
            pass

        self.node._status = NodeStatus.DISCONNECTED

        logger.debug(f'Successfully cleaned up websocket for node: {self.node}')
