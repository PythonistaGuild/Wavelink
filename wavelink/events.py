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

from typing import TYPE_CHECKING, Any, ClassVar

from .exceptions import TrackException
from .tracks import Track


if TYPE_CHECKING:
    from ._lib import Guild
    from .data import StatsData
    from .node import Node
    from .types_.websocket import (
        PlayerUpdateMsgT,
        TrackEndEventT,
        TrackEndReasonT,
        TrackExceptionEventT,
        TrackStartEventT,
        TrackStuckEventT,
        WebSocketClosedEventT,
    )


__all__ = (
    "EventT",
    "NodeStatsPayload",
    "PlayerUpdatePayload",
    "TrackEndPayload",
    "TrackExceptionPayload",
    "TrackStartPayload",
    "TrackStuckPayload",
    "WebsocketClosedPayload",
    "_BasePayload",
)


type EventT = (
    TrackEndPayload
    | TrackExceptionPayload
    | TrackStartPayload
    | TrackStuckPayload
    | WebsocketClosedPayload
    | PlayerUpdatePayload
    | NodeStatsPayload
)


class _BasePayload:
    __slots__ = ()

    _event_name: ClassVar[str | None] = None
    _registry: ClassVar[dict[str, type]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        if cls._event_name is not None:
            cls._registry[cls._event_name] = cls


class _BaseTrackPayload(_BasePayload):
    __slots__ = ("guild", "node", "player", "track")

    def __init__(
        self,
        node: Node,
        *,
        data: TrackStartEventT | TrackEndEventT | TrackStuckEventT | TrackExceptionEventT,
    ) -> None:
        super().__init__()

        self.node = node
        self.track = Track(data=data["track"])
        self.player = node.get_player(int(data["guildId"]))
        self.guild: Guild | None = self.player._guild if self.player else None


class TrackStartPayload(_BaseTrackPayload):
    _event_name = "track_start"


class TrackEndPayload(_BaseTrackPayload):
    _event_name = "track_end"
    __slots__ = ("reason",)

    def __init__(self, node: Node, *, data: TrackEndEventT) -> None:
        super().__init__(node, data=data)
        self.reason: TrackEndReasonT = data["reason"]


class TrackStuckPayload(_BaseTrackPayload):
    _event_name = "track_stuck"
    __slots__ = ("threshold",)

    def __init__(self, node: Node, *, data: TrackStuckEventT) -> None:
        super().__init__(node, data=data)
        self.threshold: int = data["thresholdMs"]


class TrackExceptionPayload(_BaseTrackPayload):
    _event_name = "track_exception"
    __slots__ = ("exception",)

    def __init__(self, node: Node, *, data: TrackExceptionEventT) -> None:
        super().__init__(node, data=data)
        self.exception = TrackException(data=data["exception"])


class WebsocketClosedPayload(_BasePayload):
    _event_name = "websocket_closed"
    __slots__ = ("by_discord", "code", "guild", "node", "player", "reason")

    def __init__(self, node: Node, *, data: WebSocketClosedEventT) -> None:
        super().__init__()

        self.node = node
        self.reason: str = data["reason"]
        self.code: int = data["code"]
        self.player = node.get_player(int(data["guildId"]))
        self.guild: Guild | None = self.player._guild if self.player else None
        self.by_discord: bool = data["byRemote"]


class PlayerUpdatePayload(_BasePayload):
    _event_name = "player_update"
    __slots__ = ("connected", "guild", "node", "ping", "player", "position", "raw_state", "time")

    def __init__(self, node: Node, *, data: PlayerUpdateMsgT) -> None:
        super().__init__()
        self.node = node
        self.player = node.get_player(int(data["guildId"]))
        self.guild: Guild | None = self.player._guild if self.player else None

        state = data["state"]
        self.connected: bool = state["connected"]
        self.position: int = state["position"]
        self.ping: int = state["ping"]
        self.time: int = state["time"]
        self.raw_state = state


class NodeStatsPayload(_BasePayload):
    _event_name = "node_stats"
    __slots__ = ("node", "stats")

    def __init__(self, node: Node, *, data: StatsData) -> None:
        super().__init__()
        self.node = node
        self.stats = data
