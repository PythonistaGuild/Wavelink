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

import inspect
import secrets
from functools import cached_property
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Never, Protocol, overload

import aiohttp

import wavelink

from ._lib import commands
from .backoff import Backoff
from .data import *
from .utils import MISSING
from .websocket import Websocket


if TYPE_CHECKING:
    from collections.abc import Mapping

    from .types_.websocket import StatsDataT


__all__ = ("MusicBot", "Node", "Pool")


class NodeStrategy(Protocol):
    def select(self, nodes: Mapping[str, Node]) -> Node | None: ...


class LoadBalancingStrategy(NodeStrategy):
    def select(self, nodes: Mapping[str, Node]) -> Node | None:
        return min(nodes.values(), key=lambda n: n.penalty(), default=None)


class NodeMapping:
    __slots__ = ("_default_strategy", "_nodes")

    def __init__(self) -> None:
        self._default_strategy = LoadBalancingStrategy()
        self._nodes: dict[str, Node] = {}

    def __setitem__(self, key: str, node: Node) -> None:
        self._nodes[key] = node

    def __getitem__(self, key: str) -> Node:
        return self._nodes[key]

    def __delitem__(self, key: str) -> None:
        del self._nodes[key]

    def proxy(self) -> MappingProxyType[str, Node]:
        return MappingProxyType(self._nodes)

    @overload
    def get(self, key: str, /) -> Node: ...

    @overload
    def get[DT](self, key: str, /, default: DT) -> Node | DT: ...

    @overload
    def get(self, key: str, /, default: None = None) -> Node | None: ...

    def get[DT](self, key: str, /, default: DT | None = None) -> Node | DT | None:
        return self._nodes.get(key, default)

    @overload
    def pop(self, key: str, /) -> Node: ...

    @overload
    def pop[DT](self, key: str, /, default: DT) -> Node | DT: ...

    @overload
    def pop(self, key: str, /, default: Never = MISSING) -> Node: ...

    def pop[DT](self, key: str, /, default: DT = MISSING) -> Node | DT:
        if default is not MISSING:
            return self._nodes.pop(key, default)

        return self._nodes.pop(key)

    def select(self, strategy: NodeStrategy | type[NodeStrategy] = MISSING) -> Node | None:
        if strategy is MISSING:
            return self._default_strategy.select(self.proxy())

        if inspect.isclass(strategy):
            inst = strategy()
            return inst.select(self.proxy())

        return strategy.select(self.proxy())


class Node:
    MAX_RESUME: int = 120

    def __init__(
        self,
        uri: str,
        *,
        password: str,
        client_id: int,
        identifier: str = MISSING,
        http_session: aiohttp.ClientSession | None = None,
        max_retries: int | None = 5,
        should_resume: bool = True,
        resume_timeout: int = 60,
    ) -> None:
        self._uri = uri
        self._password = password
        self._identifier = identifier if identifier is not MISSING else secrets.token_hex(16)
        self._client_id = client_id
        self._is_connected = False
        self._http = http_session

        self._stats: StatsData = MISSING
        self._raw_stats: StatsDataT = {}
        self._penalty_compound: int = 0

        self._max_tries = max(0, max_retries or 0)
        self._ua = f"Wavelink/{wavelink.__version__} ({client_id})"
        self._session_id: str | None = None
        self._should_resume = should_resume
        self._resume_timeout = min(max(0, resume_timeout), self.MAX_RESUME)

    def __repr__(self) -> str: ...

    def __str__(self) -> str: ...

    def is_connected(self) -> bool:
        return self._is_connected

    def has_stats(self) -> bool:
        return self._stats is not MISSING

    @property
    def identifier(self) -> str:
        return self._identifier

    @cached_property
    def headers(self) -> MappingProxyType[str, str]:
        return MappingProxyType({"Authorization": self._password})

    def ws_headers(self, session_id: str | None = None) -> MappingProxyType[str, str]:
        headers = {"Authorization": self._password, "User-Id": str(self._client_id), "Client-Name": self._ua}
        if session_id:
            headers["Session-Id"] = session_id

        return MappingProxyType(headers)

    async def _setup(self) -> None:
        if not self._http:
            self._http = aiohttp.ClientSession()

        await self.setup_hook()

    async def setup_hook(self) -> None: ...

    async def connect(self, headers: Mapping[str, str] | None = None) -> ...:
        if self._is_connected:
            raise  # TODO: Exception...

        await self._setup()
        # version = await self.fetch_version()

        ws = Websocket(self)
        await ws.connect(headers or self.ws_headers())
        self._socket = ws
        self._is_connected = True

    async def _reconnect(self) -> None:
        backoff = Backoff(maximum_time=20)
        headers = self.ws_headers(session_id=self._session_id if self._should_resume else None)

        await self._socket.close()
        while True:
            ...

    def _update_stats(self, stats: StatsDataT) -> None:
        self._raw_stats = stats

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
        self._stats = data

    def cpu_penalty(self) -> float:
        # impacts the overall penalty score the highest...
        # Audio processing is a CPU intensive task; adding a player to an already highly loaded CPU is going to impact
        # experience much greater than adding a player to a node
        # ...experiencing some network stutter with lower CPU usage for example.
        # lavalink cpu usage is considered much more impactful than overall CPU usage
        if self._stats is MISSING:
            return 0

        system = self._stats.cpu.system**2 * 10
        lavalink = self._stats.cpu.lavalink**2 * 125
        penalty = system + lavalink

        return penalty

    def memory_penalty(self) -> float:
        # impacts overall penalty lightly-moderately using a gentle superlinear curve...
        if self._stats is MISSING:
            return 0

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
            return 0

        nulled = (self._stats.frames.nulled / 3000) * 300
        deficit = (abs(self._stats.frames.deficit) / 3000) * 600
        penalty = nulled + deficit

        return penalty

    def player_penalty(self) -> float:
        if self._stats is MISSING:
            return 0
        # impacts the overall penalty lightly
        # Resource stats are much more important than overall player counts (playing or not)
        # This penalty score is mostly going to impact decisions on nodes that have close scores to prevent
        # any one healthy node consuming more players than it should...
        return self._stats.playing * 0.1

    def penalty(self) -> float:
        if self._stats is MISSING:
            return 0.0

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
        # Even with penalty scores, it's possible to have nodes that are too close to resource thresholds...
        # E.g. It's unrealistic to add a player to a node with > ~95% Lavalink CPU load or near consuming it's
        # allocated memory...
        # This check allows us to in such instances completely disqualify a node from player consideration...
        ...

    async def request(self) -> ...: ...

    async def request_json(self) -> ...: ...

    # GET /loadtracks
    async def load_tracks(self, identifier: str) -> ...: ...

    search = load_tracks

    # GET /decodetrack
    async def decode_track(self, encoded: str) -> ...: ...

    # POST /decodetracks
    async def decode_tracks(self, encoded: list[str]) -> ...: ...

    # GET /sessions/{sessionId}/players/{guildId}
    async def fetch_player(self) -> ...: ...

    # GET /sessions/{sessionId}/players
    async def fetch_players(self) -> ...: ...

    # PATCH /sessions/{sessionId}/players/{guildId}
    async def update_player(self) -> ...: ...

    # DELETE /sessions/{sessionId}/players/{guildId}
    async def destroy_player(self) -> ...: ...

    # PATCH /v4/sessions/{sessionId}
    async def update_session(self) -> ...: ...

    # GET /info
    async def fetch_info(self) -> ...: ...

    # GET /version (no /v4/)
    async def fetch_version(self) -> ...: ...

    # GET /stats
    async def fetch_stats(self) -> ...: ...

    # GET /routeplanner/status
    async def fetch_route_planner_status(self) -> ...: ...

    # POST /routeplanner/free/address
    async def free_address(self) -> ...: ...

    # POST /routeplanner/free/all
    async def free_all_addresses(self) -> ...: ...


# TODO: Correct arg typings...
class Pool:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._nodes: NodeMapping = NodeMapping()

    def add_node(self, node: Node) -> None:
        # TODO: Exception...
        if not node.is_connected():
            raise

        self._nodes[node.identifier] = node

    async def create_node(self) -> Node: ...

    def get_node(self, identifier: str, /) -> Node | None:
        return self._nodes.get(identifier)

    def get_best_node(self, strategy: NodeStrategy | type[NodeStrategy] = MISSING, /) -> Node | None:
        return self._nodes.select(strategy)


class MusicBot(commands.Bot, Pool):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        Pool.__init__(self, *args, **kwargs)
