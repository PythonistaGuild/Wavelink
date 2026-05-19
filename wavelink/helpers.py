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
from typing import TYPE_CHECKING, Any, Protocol

from ._lib import commands
from .enums import EventType


if TYPE_CHECKING:
    from collections.abc import Mapping

    from .node import Node, Pool
    from .player import Player


__all__ = ("Context", "DefaultInactivityStrategy", "InactivityStrategy", "LoadBalancingStrategy", "NodeStrategy")


class Context(commands.Context[Any]):
    wave: Pool


class NodeStrategy(Protocol):
    def select(self, nodes: Mapping[str, Node]) -> Node | None: ...


class LoadBalancingStrategy(NodeStrategy):
    def select(self, nodes: Mapping[str, Node]) -> Node | None:
        return min((n for n in nodes.values() if not n.is_disqualified()), key=lambda n: n.penalty(), default=None)


class InactivityStrategy(Protocol):
    async def check(self, player: Player, event: EventType) -> bool: ...

    async def action(self, player: Player, event: EventType) -> None: ...


class DefaultInactivityStrategy(InactivityStrategy):
    def __init__(self) -> None:
        self._tasks: set[asyncio.Task[None]] = set()

    async def _grace(self, player: Player, event: EventType) -> None:
        await asyncio.sleep(5)

        if await self.check(player, event):
            await player.destroy()

    async def check(self, player: Player, event: EventType) -> bool:
        if player.is_paused:
            return False

        if player.ping == -1:
            return False

        members = [m for m in player.channel.members if not m.bot]
        if len(members) > 0:
            return False

        return event in (EventType.TrackEnd, EventType.TrackException, EventType.TrackStuck)

    async def action(self, player: Player, event: EventType) -> None:
        task = asyncio.create_task(self._grace(player, event))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
