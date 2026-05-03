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
import secrets
from functools import cached_property
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, ClassVar
from urllib.parse import urlparse

import aiohttp
from async_utils import task_cache

import wavelink
from wavelink.types_.rest import InfoRespT

from ._lib import commands
from .backoff import Backoff
from .data import *
from .enums import Source
from .events import *
from .exceptions import *
from .tracks import Search
from .utils import JSON_LOADS, MISSING, NodeMapping
from .websocket import Websocket


if TYPE_CHECKING:
    from collections.abc import Mapping, MutableMapping

    from aiohttp.client import _RequestContextManager

    from ._lib import Client
    from .helpers import NodeStrategy
    from .player import Player
    from .types_.rest import (
        HTTPMethod,
        LoadResultDataT,
        PlayerRespT,
        UpdatePlayerReqT,
        UpdateSessionReqT,
        UpdateSessionRespT,
    )
    from .types_.websocket import StatsDataT


__all__ = ("MusicBot", "Node", "Pool")


LOGGER: logging.Logger = logging.getLogger(__name__)


class Route:
    PREFIX: ClassVar[str] = "/v4"
    NO_PREFIX: ClassVar[tuple[str, ...]] = ("version", "youtube")  # Only one exists; tuple for future proofing?

    def __init__(
        self,
        uri: str,
        path: str,
        /,
        *,
        method: HTTPMethod | None = None,
        extra_headers: Mapping[str, str] | None = None,
        params: Mapping[str, Any] | None = None,
        data: Mapping[Any, Any] | None = None,
    ) -> None:
        self._uri = uri.lower().removesuffix("/")
        self._path = path.lower().removesuffix("/").removeprefix("/")
        self._method: HTTPMethod = method or "GET"
        self._extra_headers = extra_headers or {}
        self._params = params or {}
        self._data = data
        self._url = f"{self._uri}{self.PREFIX if not self._path.startswith(self.NO_PREFIX) else ''}/{self._path}"

    def request(self, client: aiohttp.ClientSession, *, headers: MutableMapping[str, str]) -> _RequestContextManager:
        headers.update(self._extra_headers)

        req = client.request(self._method, url=self._url, headers=headers, params=self._params, json=self._data or None)
        return req

    @property
    def url(self) -> str:
        return self._url

    @property
    def path(self) -> str:
        return self._path

    @property
    def method(self) -> HTTPMethod:
        return self._method

    @property
    def extra_headers(self) -> MappingProxyType[str, str]:
        return MappingProxyType(self._extra_headers)

    @extra_headers.setter
    def extra_headers(self, value: Mapping[str, str], /) -> None:
        self._extra_headers = value


class Node:
    MAX_RESUME: ClassVar[int] = 120

    def __init__(
        self,
        uri: str,
        *,
        password: str,
        client_id: int,
        client: Client | commands.Bot = MISSING,
        identifier: str = MISSING,
        http_session: aiohttp.ClientSession | None = None,
        reconnect: bool = True,
        max_reconnects: int | None = 5,
        resume: bool = True,
        resume_timeout: int = 60,
    ) -> None:
        self._players: MutableMapping[int, Player] = {}
        self._uri = uri
        self._password = password
        self._identifier = identifier if identifier is not MISSING else secrets.token_hex(8)
        self._client_id = client_id
        self._client = client
        self._is_connected = False
        self._http = http_session

        self._stats: StatsData = MISSING
        self._raw_stats: StatsDataT = {}
        self._penalty_compound: int = 0

        self._should_reconnect = reconnect
        self._max_reconnects: int | None = max(0, max_reconnects) if max_reconnects else None
        self._ua = f"Wavelink/{wavelink.__version__} ({client_id})"
        self._session_id: str | None = None
        self._should_resume = resume
        self._resume_timeout = min(max(1, resume_timeout), self.MAX_RESUME)
        self._is_closing: bool = False

        self._tasks: set[asyncio.Task[None]] = set()

    def __repr__(self) -> str:
        return f"Node(identifier={self._identifier!r}, session_id={self._session_id!r}, players={len(self._players)})"

    def __hash__(self) -> int:
        return hash(self._identifier)

    def _is_url(self, value: str, /) -> bool:
        try:
            result = urlparse(value)
            return all((result.scheme, result.netloc))
        except Exception:
            return False

    def is_connected(self) -> bool:
        return self._is_connected

    def has_stats(self) -> bool:
        return self._stats is not MISSING

    @property
    def identifier(self) -> str:
        return self._identifier

    @cached_property
    def headers(self) -> MutableMapping[str, str]:
        return {"Authorization": self._password}

    def ws_headers(self, session_id: str | None = None) -> MappingProxyType[str, str]:
        headers = {"Authorization": self._password, "User-Id": str(self._client_id), "Client-Name": self._ua}
        if session_id:
            headers["Session-Id"] = session_id

        return MappingProxyType(headers)

    async def _setup(self) -> None:
        if not self._http:
            self._http = aiohttp.ClientSession()

        version = await self.fetch_version()
        splat = version.split(".")
        major = splat[0]

        if major != "4":
            LOGGER.warning(
                "Potentially unsupported version of Lavalink found. Wavelink supports Lavalink >= 4.0.0. Found: %s",
                version,
            )

        await self.setup_hook()

    async def setup_hook(self) -> None: ...

    async def connect(self, headers: Mapping[str, str] | None = None, *, soft: bool = False) -> ...:
        if self._is_connected:
            raise  # TODO: Exception...

        if not soft:
            await self._setup()

        ws = Websocket(self)
        await ws.connect(headers or self.ws_headers())
        self._socket = ws
        self._is_connected = True

    async def _reconnect(self) -> None:
        backoff = Backoff(maximum_time=20)
        headers = self.ws_headers(session_id=self._session_id if self._should_resume else None)

        if self._socket:
            await self._socket.close()
            self._socket = None

        self._is_connected = False

        tries = self._max_reconnects
        while tries is None or tries != 0:
            try:
                await self.connect(headers, soft=True)
            except Exception:
                # TODO: Catch proper exceptions...
                ...
            else:
                break

            if tries is not None:
                tries -= 1

            delay = backoff.calculate()
            await asyncio.sleep(delay)

        if not self._is_connected:
            # TODO: Proper exception...
            raise

    async def close(self) -> None:
        if self._is_closing or not self._is_connected:
            return

        self._is_closing = True

        if self._http:
            try:
                await self._http.close()
            except Exception as e:
                LOGGER.debug("Unable to gracefully close 'aiohttp.ClientSession' on %s: %s", self, e)

        if self._socket:
            try:
                await self._socket.close()
            except Exception as e:
                LOGGER.debug("Unable to gracefully close 'Websocket' on %s: %s", self, e)

        self._stats = MISSING
        self._raw_stats = {}
        self._session_id = None
        self._is_connected = False
        self._is_closing = False

    def _update_stats(self, stats: StatsDataT, *, update: bool = True) -> StatsData:
        # General
        players = stats.get("players", 0)
        playing = stats.get("playingPlayers", 0)
        uptime = stats.get("uptime", 0)
        frames = stats.get("frameStats", None)

        # CPU
        cpu = stats.pop("cpu")
        cores = cpu.get("cores")
        system = cpu.get("systemLoad")
        lavalink = cpu.get("lavalinkLoad")

        # Memory
        mem = stats.pop("memory")

        # Dataclasses
        cpu_stats = CPUData(cores=cores, system=system, lavalink=lavalink)
        mem_stats = MemoryData(**mem)
        frame_stats = FrameData(**frames) if frames else None

        data = StatsData(
            players=players,
            playing=playing,
            uptime=uptime,
            memory=mem_stats,
            cpu=cpu_stats,
            frames=frame_stats,
        )

        if update:
            self._raw_stats = stats
            self._stats = data

        return data

    def cpu_penalty(self) -> float:
        # impacts the overall penalty score the highest...
        # Audio processing is a CPU intensive task; adding a player to an already highly loaded CPU is going to impact
        # experience much greater than adding a player to a node
        # ...experiencing some network stutter with lower CPU usage for example.
        # lavalink cpu usage is considered much more impactful than overall CPU usage
        if self._stats is MISSING:
            return float("inf")

        system = self._stats.cpu.system**2 * 10
        lavalink = self._stats.cpu.lavalink**2 * 125
        penalty = system + lavalink

        return penalty

    def memory_penalty(self) -> float:
        # impacts overall penalty lightly-moderately using a gentle superlinear curve...
        if self._stats is MISSING:
            return float("inf")

        ratio = self._stats.memory.free / self._stats.memory.allocated
        penalty = (1 - ratio) ** 1.5 * 5

        return penalty

    def frame_penalty(self) -> float:
        # impacts overall penalty lightly-highly based on deficit and nulled frames...
        # nulled frames are usually considered less impactful as they *usually* correlate to transient issues
        # ... (e.g network issues, small cpu buffering, YouTube issues, etc...)
        # deficit frames are weighted stronger as they can indicate longer term issues with the node
        # ...being able to keep up.
        if self._stats is MISSING or not self._stats.frames:
            return float("inf")

        nulled = (self._stats.frames.nulled / 3000) * 300
        deficit = (abs(self._stats.frames.deficit) / 3000) * 600
        penalty = nulled + deficit

        return penalty

    def player_penalty(self) -> float:
        if self._stats is MISSING:
            return float("inf")
        # impacts the overall penalty lightly
        # Resource stats are much more important than overall player counts (playing or not)
        # This penalty score is mostly going to impact decisions on nodes that have close scores to prevent
        # any one healthy node consuming more players than it should...
        return self._stats.playing * 0.1

    def penalty(self) -> float:
        if self._stats is MISSING:
            return float("inf")

        return self.cpu_penalty() + self.memory_penalty() + self.frame_penalty() + self.player_penalty()

    @property
    def penalty_compound(self) -> int:
        return self._penalty_compound

    @penalty_compound.setter
    def penalty_compound(self, value: int, /) -> None:
        # Min 0
        self._penalty_compound = max(0, value)

    def composite_penalty(self) -> float:
        return self.penalty() + self._penalty_compound

    def is_disqualified(self) -> bool:
        return False

    async def request(self, route: Route) -> bytes | None:
        assert self._http
        data: bytes | None = None

        async with route.request(self._http, headers=self.headers) as resp:
            status = resp.status

            if status == 204:
                return
            elif status >= 500:
                raise HTTPException(status=status)

            try:
                data = await resp.read()
            except Exception as e:
                raise WavelinkException("%r error processing data in request %r: %s", self, route, e)

            if status >= 300:
                if data:
                    raise LavalinkError(data=JSON_LOADS(data))

                else:
                    raise HTTPException(status=status)

        return data

    async def request_json(self, route: Route) -> Any:
        bites = await self.request(route)

        if not bites:
            return {}

        return JSON_LOADS(bites)

    # GET /loadtracks
    async def raw_load_tracks(self, identifier: str, /) -> LoadResultDataT:
        if not identifier:
            raise ValueError("The 'identifier' parameter cannot be empty.")

        route = Route(self._uri, "/loadtracks", params={"identifier": identifier})
        data: LoadResultDataT = await self.request_json(route=route)
        return data

    @task_cache.taskcache(ttl=60 * 60)
    async def load_tracks(self, identifier: str, /) -> Search:
        data: LoadResultDataT = await self.raw_load_tracks(identifier)

        if data["loadType"] == "error":
            inner = data["data"]
            cause = inner["cause"]
            raise TrackException(f"Unable to load tracks with search: {identifier!r}: {cause}", data=inner)

        return Search(identifier, data=data)

    async def search(self, search: str, /, *, source: Source | str = Source.youtube_music) -> Search:
        if self._is_url(search) or source is Source.local:
            return await self.load_tracks(search)

        identifier = f"{source.removesuffix(':')}:{search}"
        return await self.load_tracks(identifier)

    # GET /decodetrack
    async def raw_decode_track(self, encoded: str) -> ...: ...

    # POST /decodetracks
    async def raw_decode_tracks(self, encoded: list[str]) -> ...: ...

    # GET /sessions/{sessionId}/players/{guildId}
    async def raw_fetch_player(self, guild_id: str | int, /) -> PlayerRespT:
        route = Route(self._uri, f"/sessions/{self._session_id}/players/{guild_id}")
        return await self.request_json(route)

    # GET /sessions/{sessionId}/players
    async def raw_fetch_players(self) -> list[PlayerRespT]:
        route = Route(self._uri, f"/sessions/{self._session_id}/players")
        return await self.request_json(route)

    # PATCH /sessions/{sessionId}/players/{guildId}
    async def update_player(self, guild_id: str | int, /, *, data: UpdatePlayerReqT, no_replace: bool = True) -> PlayerRespT:
        path = f"/sessions/{self._session_id}/players/{guild_id}"
        route = Route(self._uri, path, method="PATCH", params={"noReplace": str(no_replace).lower()}, data=data)

        result = await self.request_json(route)
        return result

    # DELETE /sessions/{sessionId}/players/{guildId}
    async def destroy_player(self, guild_id: str | int, /) -> None:
        route = Route(self._uri, f"sessions/{self._session_id}/players/{guild_id}")
        await self.request(route)

    # PATCH /sessions/{sessionId}
    async def update_session(self, data: UpdateSessionReqT) -> UpdateSessionRespT:
        route = Route(self._uri, f"/sessions/{self._session_id}", method="PATCH", data=data)

        result = await self.request_json(route)
        return result

    # GET /info
    async def raw_fetch_info(self) -> InfoRespT:
        route = Route(self._uri, "/info", method="GET")
        return await self.request_json(route)

    # GET /version (no /v4/)
    async def fetch_version(self) -> str:
        route = Route(self._uri, "/version", method="GET")
        return (await self.request(route) or b"").decode("UTF-8")

    # GET /stats
    async def raw_fetch_stats(self) -> StatsDataT:
        route = Route(self._uri, f"/stats", method="GET")
        return await self.request_json(route)

    async def fetch_stats(self, *, update: bool = False) -> StatsData:
        raw = await self.raw_fetch_stats()
        return self._update_stats(raw, update=update)

    # GET /routeplanner/status
    async def raw_fetch_route_planner_status(self) -> ...: ...

    # POST /routeplanner/free/address
    async def free_address(self) -> ...: ...

    # POST /routeplanner/free/all
    async def free_all_addresses(self) -> ...: ...

    def _event_factory(self, name: str, data: Any) -> type | None:
        cls = _BasePayload._registry.get(name)
        if not cls:
            return

        return cls(self, data=data)

    def _dispatch(self, name: str, data: Any) -> None:
        payload = self._event_factory(name, data)

        if self._client is not MISSING:
            event = f"wavelink_{name}"
            self._client.dispatch(event, payload) if payload else self._client.dispatch(event)

        func = getattr(self, f"on_{name}", None)
        if not func:
            return

        coro = func(payload) if payload else func()
        t = asyncio.create_task(coro, name=f"Wavelink:NodeEvent-{name}")

        self._tasks.add(t)
        t.add_done_callback(self._tasks.discard)

    def get_player(self, guild_id: int, /) -> Player | None:
        return self._players.get(guild_id)

    async def on_track_start(self, payload: TrackStartPayload) -> None: ...

    async def on_track_end(self, payload: TrackEndPayload) -> None: ...

    async def on_track_stuck(self, payload: TrackStuckPayload) -> None: ...

    async def on_track_exception(self, payload: TrackExceptionPayload) -> None: ...

    async def on_websocket_closed(self, payload: WebsocketClosedPayload) -> None: ...


# TODO: Correct arg typings...
class Pool:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._nodes: NodeMapping = NodeMapping()
        self._is_closing: bool = False

    def add_node(self, node: Node) -> None:
        # TODO: Exception...
        if self._is_closing:
            raise

        if not node.is_connected():
            raise NodeDisconnectedError(f"{node!r} is not currently connected. Please connect the Node before adding.")

        self._nodes[node.identifier] = node

    async def create_node(self) -> ...:
        # TODO: Exception...
        if self._is_closing:
            raise

    def get_node(
        self,
        identifier: str | None = None,
        /,
        *,
        strategy: NodeStrategy | type[NodeStrategy] = MISSING,
    ) -> Node | None:
        if identifier:
            return self._nodes.get(identifier)

        return self._nodes.select(strategy)

    async def shutdown(self) -> None:
        if self._is_closing:
            return

        self._is_closing = True

        for node in self._nodes.values():
            await node.close()

    async def search(
        self,
        search: str,
        /,
        *,
        source: Source | str = Source.youtube_music,
        node: Node | None = None,
    ) -> Search:
        # TODO: Exception...
        node = node or self.get_node()
        if not node:
            # TODO: Exception...
            raise

        return await node.search(search, source=source)


class MusicBot(commands.Bot, Pool):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        Pool.__init__(self, *args, **kwargs)

    async def close(self) -> None:
        await self.shutdown()
        await super().close()
