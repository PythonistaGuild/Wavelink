"""MIT License

Copyright (c) 2019-2021 PythonistaGuild

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
from typing import Any, Dict, TYPE_CHECKING, Tuple, Optional

import aiohttp

import wavelink
from .utils import MISSING

if TYPE_CHECKING:
    from .pool import Node

__all__ = ("Websocket",)

logger: logging.Logger = logging.getLogger(__name__)


class Websocket:
    def __init__(self, *, node: Node, session: aiohttp.ClientSession = MISSING):
        self.node: Node = node

        self.websocket: Optional[aiohttp.ClientWebSocketResponse] = None
        if session is MISSING:
            session = aiohttp.ClientSession()
        self.session: aiohttp.ClientSession = session
        self.listener: Optional[asyncio.Task] = None

        self.host: str = f'{"https://" if self.node._https else "http://"}{self.node.host}:{self.node.port}'
        self.ws_host: str = f"ws://{self.node.host}:{self.node.port}"

    @property
    def headers(self) -> Dict[str, Any]:
        return {
            "Authorization": self.node._password,
            "User-Id": str(self.node.bot.user.id),
            "Client-Name": "WaveLink",
            'Resume-Key': self.node.resume_key
        }

    def is_connected(self) -> bool:
        return self.websocket is not None and not self.websocket.closed

    async def connect(self) -> None:
        if self.is_connected():
            assert isinstance(self.websocket, aiohttp.ClientWebSocketResponse)
            await self.websocket.close(
                code=1006, message=b"WaveLink: Attempting reconnection."
            )

        host = self.host if self.node._https else self.ws_host

        try:
            self.websocket = await self.session.ws_connect(
                host, headers=self.headers, heartbeat=self.node._heartbeat
            )
        except Exception as error:
            if (
                isinstance(error, aiohttp.WSServerHandshakeError)
                and error.status == 401
            ):
                logger.error(f"\nAuthorization Failed for Node: {self.node}\n")
            else:
                logger.error(f"Connection Failure: {error}")

            return

        if self.listener is None:
            self.listener = asyncio.create_task(self.listen())

        if self.is_connected():
            self.dispatch("node_ready", self.node)
            logger.debug(f"Connection established...{self.node.__repr__()}")

            resume = {
                "op": "configureResuming",
                "key": f"{self.node.resume_key}",
                "timeout": 60
            }
            await self.send(**resume)

    async def listen(self) -> None:
        backoff = wavelink.Backoff(base=1, maximum_time=60, maximum_tries=None)

        while True:
            assert isinstance(self.websocket, aiohttp.ClientWebSocketResponse)
            msg = await self.websocket.receive()

            if msg.type is aiohttp.WSMsgType.CLOSED:
                logger.debug(f"Websocket Closed: {msg.extra}")

                retry = backoff.calculate()

                logger.warning(f"\nRetrying connection in <{retry}> seconds...\n")

                await asyncio.sleep(retry)

                if not self.is_connected():
                    await self.connect()
            else:
                logger.debug(f"Received Payload:: <{msg.data}>")

                if msg.data == 1011:
                    # Lavalink encountered an internal error which can not be fixed...
                    # Consider updating Lavalink...
                    logger.error('Internal Lavalink Error encountered. Terminating WaveLink without retries.'
                                 'Consider updating your Lavalink Server.')

                    self.listener.cancel()
                    return

                asyncio.create_task(self.process_data(msg.json()))

    async def process_data(self, data: Dict[str, Any]) -> None:
        op = data.get("op", None)
        if not op:
            return

        if op == "stats":
            self.node.stats = wavelink.Stats(self.node, data)
            return

        try:
            player = self.node.get_player(self.node.bot.get_guild(
                int(data["guildId"])))  # type: ignore
        except KeyError:
            return

        if player is None:
            return

        if op == 'event':
            event, payload = await self._get_event_payload(data['type'], data)
            logger.debug(f'op: event:: {data}')
            
            if event == 'track_end' and payload.get('reason') != 'REPLACED':
                player._source = None

            self.dispatch(event, player, **payload)

        elif op == "playerUpdate":
            logger.debug(f"op: playerUpdate:: {data}")
            try:
                await player.update_state(data)
            except KeyError:
                pass

    async def _get_event_payload(
        self, name: str, data: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        event = "event"
        payload = {}

        if name == "WebSocketClosedEvent":
            event = "websocket_closed"
            payload["reason"] = data.get("reason")
            payload["code"] = data.get("code")

        if name.startswith("Track"):
            base64_ = data.get('track')
            track = await self.node.build_track(cls=wavelink.Track, identifier=base64_)

            payload["track"] = track

            if name == "TrackEndEvent":
                event = "track_end"
                payload["reason"] = data.get("reason")

            elif name == "TrackStartEvent":
                event = "track_start"

            elif name == "TrackExceptionEvent":
                event = "track_exception"
                payload["error"] = data.get("error")

            elif name == "TrackStuckEvent":
                event = "track_stuck"
                threshold = data.get("thresholdMs")
                if isinstance(threshold, str):
                    payload["threshold"] = int(threshold)

        return event, payload

    def dispatch(self, event, *args: Any, **kwargs: Any) -> None:
        self.node.bot.dispatch(f"wavelink_{event}", *args, **kwargs)

    async def send(self, **data: Any) -> None:
        if self.is_connected():
            assert isinstance(self.websocket, aiohttp.ClientWebSocketResponse)
            logger.debug(f"Sending Payload:: {data}")

            data_str = self.node._dumps(data)
            if isinstance(data_str, bytes):
                # Some JSON libraries serialize to bytes
                # Yet Lavalink does not support binary websockets
                # So we need to decode. In the future, maybe
                # self._websocket.send_bytes could be used
                # if Lavalink ever implements it
                data_str = data_str.decode("utf-8")

            await self.websocket.send_str(data_str)
