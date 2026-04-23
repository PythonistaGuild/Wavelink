"""Copyright 2026 Evie. P. <evieepy@gmail.com>, PythonistaGuild

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from typing import TYPE_CHECKING, Any, cast, no_type_check

from picows import (
    WSCloseCode,
    WSFrame,
    WSListener,
    WSMsgType,
    WSTransport,
    ws_connect,  # type: ignore
)

from .utils import JSON_LOADS, MISSING


if TYPE_CHECKING:
    from collections.abc import Coroutine, Mapping

    from .node import Node
    from .types_.websocket import EventMsgT, PlayerUpdateMsgT, ReadyMsgT, StatsMsgT, WSMsgT


LOGGER: logging.Logger = logging.Logger(__name__)
PY_314: bool = sys.version_info >= (3, 14)


class WebsocketFrame(WSListener):
    def __init__(self, socket: Websocket, /) -> None:
        self._socket = socket
        self._loop = socket._loop
        self._eager = self.has_eager()

        self._tasks: set[asyncio.Task[None]] = set()

    def has_eager(self) -> bool:
        if PY_314:
            return True

        return self._loop.get_task_factory() == asyncio.eager_task_factory

    def _get_method(self, data: WSMsgT) -> Coroutine[Any, Any, None] | None:
        coro: Coroutine[Any, Any, None] | None = None

        match data:
            case {"op": "ready"}:
                coro = self._socket.ws_ready(data)
            case {"op": "playerUpdate"}:
                coro = self._socket.ws_player_update(data)
            case {"op": "stats"}:
                coro = self._socket.ws_stats(data)
            case {"op": "event"}:
                coro = self._socket.ws_event(data)
            case _:
                LOGGER.debug("Unable to process unknown websocket message: %s", data)

        return coro

    @no_type_check  # asyncio has bad typing for the tasks in 3.14
    def on_ws_frame(self, transport: WSTransport, frame: WSFrame) -> None:
        if frame.msg_type is WSMsgType.PING:
            transport.send_pong(frame.get_payload_as_bytes())
            return

        coro = None
        if frame.msg_type is WSMsgType.TEXT:
            data = JSON_LOADS(frame.get_payload_as_bytes())
            coro = self._get_method(data)
        elif frame.msg_type is WSMsgType.CLOSE:
            coro = self.on_close_code(transport, frame.get_close_code())

        if not coro:
            return

        t = asyncio.create_task(coro, eager_start=True) if PY_314 else asyncio.create_task(coro)
        self._tasks.add(t)
        t.add_done_callback(self._tasks.discard)

    async def on_close_code(self, transport: WSTransport, code: WSCloseCode) -> ...:
        # TODO: ...
        print(code.value)


class Websocket:
    _frame_listener: WebsocketFrame
    _transport: WSTransport

    def __init__(self, node: Node, /) -> None:
        self._node = node
        self._loop = asyncio.get_event_loop()
        self._session_id: str = MISSING
        self._connected: bool = False
        self._closing: bool = False

    def listener_factory(self) -> WebsocketFrame:
        listener = WebsocketFrame(self)
        return listener

    async def connect(self, headers: Mapping[str, str]) -> ...:
        uri = f"{self._node._uri.removesuffix('/')}/v4/websocket"
        uri = uri.replace("https://", "wss://").replace("http://", "ws://")
        transport, listener = await ws_connect(self.listener_factory, uri, extra_headers=headers)

        self._transport = transport
        self._frame_listener = cast("WebsocketFrame", listener)
        self._connected = True

    async def close(self) -> ...:
        if self._closing:
            return

        self._closing = True
        self._transport.disconnect(graceful=True)

        try:
            async with asyncio.Timeout(3):
                await self._transport.wait_disconnected()
        except TimeoutError:
            # TODO: Logging...
            ...

        self._connected = False
        self._frame_listener = MISSING
        self._transport = MISSING

    async def ws_ready(self, data: ReadyMsgT) -> None:
        session = data["sessionId"]
        self._node._session_id = session

    async def ws_player_update(self, data: PlayerUpdateMsgT) -> None: ...

    async def ws_stats(self, data: StatsMsgT) -> None:
        data.pop("op")
        updated: Any = data
        self._node._update_stats(updated)

    async def ws_event(self, data: EventMsgT) -> None: ...
