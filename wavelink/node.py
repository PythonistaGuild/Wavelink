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

from typing import Any

from wavelink._lib import commands


__all__ = ("MusicBot", "Node", "Pool")


class Node: ...


# @cached_property
# def headers(self) -> MappingProxyType[str, str]:
#     return MappingProxyType({"Authorization": self._password})


class Pool:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._thing = 123
        super().__init__()

    def add_node(self) -> ...: ...

    async def create_node(self) -> Node: ...

    # GET /loadtracks
    async def load_tracks(self, identifier: str) -> ...: ...

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
