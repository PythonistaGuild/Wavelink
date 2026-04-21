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

import secrets
from functools import cached_property
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Never, Protocol, overload

from ._lib import commands
from .utils import MISSING


if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = ("MusicBot", "Node", "Pool")


class NodeStrategy(Protocol):
    def select(self, nodes: Mapping[str, Node]) -> Node | None:
        raise NotImplementedError


class LoadBalancingStrategy(NodeStrategy):
    def select(self, nodes: Mapping[str, Node]) -> Node | None: ...


class NodeMapping:
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

    def select(self, strategy: NodeStrategy = MISSING) -> Node | None:
        if strategy is MISSING:
            return self._default_strategy.select(self.proxy())

        return strategy.select(self.proxy())


class Node:
    __slots__ = ("_identifier", "_max_players_priority", "_password", "_uri")

    def __init__(
        self,
        uri: str,
        *,
        password: str,
        identifier: str = MISSING,
    ) -> None:
        self._uri = uri
        self._password = password
        self._identifier = identifier if identifier is not MISSING else secrets.token_hex(16)

    def __repr__(self) -> str: ...

    def __str__(self) -> str: ...

    @property
    def identifier(self) -> str:
        return self._identifier

    @cached_property
    def headers(self) -> MappingProxyType[str, str]:
        return MappingProxyType({"Authorization": self._password})


class Pool:
    def __init__(self, *, use_cache: bool = True, cache_ttl: float | None = None, max_cache: int | None = None) -> None:
        self._nodes: list[Node] = []
        self._node_map: dict[str, Node]

    def add_node(self) -> ...: ...

    async def create_node(self) -> Node: ...

    def get_node(self) -> Node | None: ...

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


class MusicBot(commands.Bot, Pool):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        Pool.__init__(self, *args, **kwargs)
