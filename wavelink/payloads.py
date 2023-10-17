"""
MIT License

Copyright (c) 2019-Current PythonistaGuild, EvieePy

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

from typing import TYPE_CHECKING, cast

import wavelink

from .enums import DiscordVoiceCloseType

if TYPE_CHECKING:
    from .node import Node
    from .player import Player
    from .tracks import Playable
    from .types.state import PlayerState
    from .types.stats import CPUStats, FrameStats, MemoryStats
    from .types.websocket import StatsOP, TrackExceptionPayload


__all__ = (
    "TrackStartEventPayload",
    "TrackEndEventPayload",
    "TrackExceptionEventPayload",
    "TrackStuckEventPayload",
    "WebsocketClosedEventPayload",
    "PlayerUpdateEventPayload",
    "StatsEventPayload",
    "NodeReadyEventPayload",
)


class NodeReadyEventPayload:
    def __init__(self, node: Node, resumed: bool, session_id: str) -> None:
        self.node = node
        self.resumed = resumed
        self.session_id = session_id


class TrackStartEventPayload:
    def __init__(self, player: Player | None, track: Playable) -> None:
        self.player = player
        self.track = track
        self.original: Playable | None = None

        if player:
            self.original = player._original


class TrackEndEventPayload:
    def __init__(self, player: Player | None, track: Playable, reason: str) -> None:
        self.player = player
        self.track = track
        self.reason = reason
        self.original: Playable | None = None

        if player:
            self.original = player._previous


class TrackExceptionEventPayload:
    def __init__(self, player: Player | None, track: Playable, exception: TrackExceptionPayload) -> None:
        self.player = cast(wavelink.Player, player)
        self.track = track
        self.exception = exception


class TrackStuckEventPayload:
    def __init__(self, player: Player | None, track: Playable, threshold: int) -> None:
        self.player = cast(wavelink.Player, player)
        self.track = track
        self.threshold = threshold


class WebsocketClosedEventPayload:
    def __init__(self, player: Player | None, code: int, reason: str, by_remote: bool) -> None:
        self.player = player
        self.code: DiscordVoiceCloseType = DiscordVoiceCloseType(code)
        self.reason = reason
        self.by_remote = by_remote


class PlayerUpdateEventPayload:
    def __init__(self, player: Player | None, state: PlayerState) -> None:
        self.player = cast(wavelink.Player, player)
        self.time: int = state["time"]
        self.position: int = state["position"]
        self.connected: bool = state["connected"]
        self.ping: int = state["ping"]


class StatsEventMemory:
    def __init__(self, data: MemoryStats) -> None:
        self.free: int = data["free"]
        self.used: int = data["used"]
        self.allocated: int = data["allocated"]
        self.reservable: int = data["reservable"]


class StatsEventCPU:
    def __init__(self, data: CPUStats) -> None:
        self.cores: int = data["cores"]
        self.system_load: float = data["systemLoad"]
        self.lavalink_load: float = data["lavalinkLoad"]


class StatsEventFrames:
    def __init__(self, data: FrameStats) -> None:
        self.sent: int = data["sent"]
        self.nulled: int = data["nulled"]
        self.deficit: int = data["deficit"]


class StatsEventPayload:
    def __init__(self, data: StatsOP) -> None:
        self.players: int = data["players"]
        self.playing: int = data["playingPlayers"]
        self.uptime: int = data["uptime"]

        self.memory: StatsEventMemory = StatsEventMemory(data=data["memory"])
        self.cpu: StatsEventCPU = StatsEventCPU(data=data["cpu"])
        self.frames: StatsEventFrames | None = None

        if data["frameStats"]:
            self.frames = StatsEventFrames(data=data["frameStats"])
