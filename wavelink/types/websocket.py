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

from typing import TYPE_CHECKING, Literal, TypeAlias, TypedDict


if TYPE_CHECKING:
    from typing_extensions import NotRequired

    from .state import PlayerState
    from .stats import CPUStats, FrameStats, MemoryStats
    from .tracks import TrackPayload


class TrackExceptionPayload(TypedDict):
    message: NotRequired[str]
    severity: str
    cause: str


class ReadyOP(TypedDict):
    op: Literal["ready"]
    resumed: bool
    sessionId: str


class PlayerUpdateOP(TypedDict):
    op: Literal["playerUpdate"]
    guildId: str
    state: PlayerState


class StatsOP(TypedDict):
    op: Literal["stats"]
    players: int
    playingPlayers: int
    uptime: int
    memory: MemoryStats
    cpu: CPUStats
    frameStats: FrameStats


class TrackStartEvent(TypedDict):
    op: Literal["event"]
    guildId: str
    type: Literal["TrackStartEvent"]
    track: TrackPayload


class TrackEndEvent(TypedDict):
    op: Literal["event"]
    guildId: str
    type: Literal["TrackEndEvent"]
    track: TrackPayload
    reason: str


class TrackExceptionEvent(TypedDict):
    op: Literal["event"]
    guildId: str
    type: Literal["TrackExceptionEvent"]
    track: TrackPayload
    exception: TrackExceptionPayload


class TrackStuckEvent(TypedDict):
    op: Literal["event"]
    guildId: str
    type: Literal["TrackStuckEvent"]
    track: TrackPayload
    thresholdMs: int


class WebsocketClosedEvent(TypedDict):
    op: Literal["event"]
    guildId: str
    type: Literal["WebSocketClosedEvent"]
    code: int
    reason: str
    byRemote: bool


WebsocketOP: TypeAlias = (
    ReadyOP
    | PlayerUpdateOP
    | StatsOP
    | TrackStartEvent
    | TrackEndEvent
    | TrackExceptionEvent
    | TrackStuckEvent
    | WebsocketClosedEvent
)
