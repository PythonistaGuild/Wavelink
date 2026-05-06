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
from typing import TYPE_CHECKING, Any, ClassVar, cast, no_type_check

from picows import (
    WSAutoPingStrategy,
    WSFrame,
    WSListener,
    WSMsgType,
    WSTransport,
    ws_connect,  # type: ignore
)

from .utils import JSON_LOADS, MISSING


if TYPE_CHECKING:
    from collections.abc import Coroutine, Mapping

    from wavelink.types_.websocket import EventT

    from .node import Node
    from .types_.websocket import PlayerUpdateMsgT, ReadyMsgT, StatsMsgT, WSMsgT


# Disable Picows Logging
logging.getLogger("picows").setLevel(logging.ERROR)

LOGGER: logging.Logger = logging.getLogger(__name__)
PY_314: bool = sys.version_info >= (3, 14)


class WebsocketFrame(WSListener):
    HEARTBEAT_FAILURE: ClassVar[int] = 3008
    RECONNECT_CODES: ClassVar[tuple[int, ...]] = (1001, 1005, 1006, 1011, 1012, 1013)

    def __init__(self, socket: Websocket, /) -> None:
        self._socket = socket
        self._loop = socket._loop
        self._eager = self.has_eager()
        self._has_code: bool = False
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

    def on_ws_disconnected(self, transport: WSTransport) -> None:
        if self._has_code:
            return

        t = asyncio.create_task(self._possible_heartbeat_failure(transport))
        self._tasks.add(t)
        t.add_done_callback(self._tasks.discard)

    @no_type_check  # asyncio has bad typing for the tasks in 3.14
    def on_ws_frame(self, transport: WSTransport, frame: WSFrame) -> None:
        if frame.msg_type is WSMsgType.PING:
            transport.send_pong(frame.get_payload_as_bytes())
            return

        coro = None
        data = None
        if frame.msg_type is WSMsgType.TEXT:
            data = JSON_LOADS(frame.get_payload_as_bytes())
            coro = self._get_method(data)
        elif frame.msg_type is WSMsgType.CLOSE:
            coro = self.on_close_code(transport, frame.get_close_code().value)

        if not coro:
            LOGGER.debug("Unable to find suitable callback for Websocket message: %s", data)
            return

        t = asyncio.create_task(coro, eager_start=True) if PY_314 else asyncio.create_task(coro)
        self._tasks.add(t)
        t.add_done_callback(self._tasks.discard)

    async def _possible_heartbeat_failure(self, transport: WSTransport) -> None:
        await asyncio.sleep(1)
        if self._has_code:
            return

        await self.on_close_code(transport, code=self.HEARTBEAT_FAILURE)

    async def on_close_code(self, transport: WSTransport, code: int) -> None:
        self._has_code = True

        if code == 1000:
            LOGGER.info("%r gracefully closed. No reconnect attempt will be made.", self._socket)
            return await self._socket.close()

        if code == self.HEARTBEAT_FAILURE:
            LOGGER.warning("Heartbeat stopped responding on %r... Attempting to re-establish connection.", self._socket)
            return await self._socket._node._reconnect(resume=True)

        elif code in self.RECONNECT_CODES:
            LOGGER.warning(
                "%s has disconnected with close code %d. Attempting to reconnect if possible.",
                self._socket,
                code,
            )
            return await self._socket._node._reconnect(resume=code != 1001)

        else:
            LOGGER.error("Unhandled websocket close code %d on %s. Disconnecting...", code, self._socket)


class Websocket:
    _frame_listener: WebsocketFrame
    _transport: WSTransport

    def __init__(self, node: Node, /) -> None:
        self._node = node
        self._loop = asyncio.get_event_loop()
        self._session_id: str = MISSING
        self._connected: bool = False
        self._closing: bool = False
        self._heartbeat = node._heartbeat

    def __repr__(self) -> str:
        return f"{self._node!r}::<Websocket>"

    def listener_factory(self) -> WebsocketFrame:
        listener = WebsocketFrame(self)
        return listener

    async def connect(self, headers: Mapping[str, str]) -> None:
        LOGGER.debug("Attempting to connect %s Websocket.", self)

        uri = f"{self._node._uri.removesuffix('/')}/v4/websocket"
        uri = uri.replace("https://", "wss://").replace("http://", "ws://")
        transport, listener = await ws_connect(
            self.listener_factory,
            uri,
            extra_headers=headers,
            enable_auto_ping=True,
            enable_auto_pong=True,
            auto_ping_strategy=WSAutoPingStrategy.PING_PERIODICALLY,
            auto_ping_idle_timeout=self._heartbeat,
        )

        self._transport = transport
        self._frame_listener = cast("WebsocketFrame", listener)
        self._connected = True

        LOGGER.info("Successfully connected %s.", self)

    async def close(self) -> None:
        if self._closing:
            return

        LOGGER.debug("Attempting to gracefully close %s.", self)
        self._closing = True

        try:
            self._transport.disconnect(graceful=True)
        except Exception as e:
            LOGGER.debug("Unable to gracefully close %s connection: %s", self, e)

        try:
            async with asyncio.timeout(3):
                await self._transport.wait_disconnected()
        except TimeoutError:
            LOGGER.debug("Unable to gracefully close %s connection.", self)

        self._connected = False
        self._frame_listener = MISSING
        self._transport = MISSING

    async def ws_ready(self, data: ReadyMsgT) -> None:
        LOGGER.debug("%s received websocket READY message: %s", self, data)

        session = data["sessionId"]
        self._node._session_id = session
        self._node._session_event.set()

        resumed = data["resumed"]
        if resumed:
            return

        if not self._node._players:
            return

        await self._node._cleanup_stale()

    async def ws_player_update(self, data: PlayerUpdateMsgT) -> None:
        LOGGER.debug("%s received websocket PLAYER_UPDATE message: %s", self, data)
        player = self._node.get_player(int(data["guildId"]))
        if not player:
            return

        player._lavalink_update(data["state"])
        self._node._dispatch("player_update", data=dict(data))

    async def ws_stats(self, data: StatsMsgT) -> None:
        LOGGER.debug("%s received websocket STATS message: %s", self, data)

        data.pop("op")
        updated: Any = data

        stats = self._node._update_stats(updated)
        self._node._dispatch("node_stats", data=stats)

    async def ws_event(self, data: EventT) -> None:
        LOGGER.debug("%s received websocket EVENT message: %s", self, data)

        match data:
            case {"type": "TrackStartEvent"}:
                self._node._dispatch("track_start", data)
            case {"type": "TrackEndEvent"}:
                self._node._dispatch("track_end", data)
            case {"type": "TrackExceptionEvent"}:
                self._node._dispatch("track_exception", data)
            case {"type": "TrackStuckEvent"}:
                self._node._dispatch("track_stuck", data)
            case {"type": "WebSocketClosedEvent"}:
                self._node._dispatch("websocket_closed", data)
