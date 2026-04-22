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

from typing import Any, Literal, NotRequired, TypedDict


WebsocketHeadersT = TypedDict(
    "WebsocketHeadersT", {"Authorization": str, "User-Id": int, "Client-Name": str, "Session-Id": NotRequired[str]}
)

type MsgOPT = Literal["ready", "playerUpdate", "stats", "event"]
type TrackEndReasonT = Literal["finished", "loadFailed", "stopped", "replaced", "cleanup"]
type WSEventType = Literal[
    "TrackStartEvent",
    "TrackEndEvent",
    "TrackExceptionEvent",
    "TrackStuckEvent",
    "WebSocketClosedEvent",
]

type TrackExceptionSeverityT = Literal["common", "suspicious", "fault"]


class ReadyMsgT(TypedDict):
    op: Literal["ready"]
    resumed: bool
    sessionId: str


class PlayerStateT(TypedDict):
    time: int
    position: int
    connected: bool
    ping: int


class PlayerUpdateMsgT(TypedDict):
    op: Literal["playerUpdate"]
    guildId: str
    state: PlayerStateT


class StatsMemoryT(TypedDict):
    free: int
    user: int
    allocated: int
    reservable: int


class StatsCPUT(TypedDict):
    cores: int
    systemLoad: float
    lavalinkLoad: float


class StatsFrameT(TypedDict):
    sent: int
    nulled: int
    deficit: int


class StatsMsgT(TypedDict):
    op: Literal["stats"]
    players: int
    playingPlayers: int
    uptime: int
    memory: StatsMemoryT
    cpu: StatsCPUT
    frameStats: StatsFrameT | None


class EventMsgT(TypedDict):
    op: Literal["event"]
    guildId: str


class TrackInfoT(TypedDict):
    identifier: str
    isSeekable: bool
    author: str
    length: int
    isStream: bool
    position: int
    title: str
    uri: str | None
    artworkUrl: str | None
    isrc: str | None
    sourceName: str


class TrackT(TypedDict):
    encoded: str
    info: TrackInfoT
    pluginInfo: dict[Any, Any]
    userData: dict[Any, Any]


class TrackStartEventT(EventMsgT):
    type: Literal["TrackStartEvent"]
    track: TrackT


class TrackEndEventT(EventMsgT):
    type: Literal["TrackEndEvent"]
    track: TrackT
    reason: TrackEndReasonT


class TrackExceptionT(TypedDict):
    message: str | None
    severity: TrackExceptionSeverityT
    cause: str
    causeStackTrace: str


class TrackExceptionEventT(EventMsgT):
    type: Literal["TrackExceptionEvent"]
    track: TrackT
    exception: TrackExceptionT


class TrackStuckEventT(EventMsgT):
    type: Literal["TrackStuckEvent"]
    track: TrackT
    thresholdMs: int


class WebSocketClosedEventT(EventMsgT):
    type: Literal["WebSocketClosedEvent"]
    code: int
    reason: str
    byRemote: bool


class StatsDataT(TypedDict, total=False):
    players: int
    playingPlayers: int
    uptime: int
    memory: StatsMemoryT
    cpu: StatsCPUT
    frameStats: StatsFrameT | None


type WSMsgT = ReadyMsgT | PlayerUpdateMsgT | StatsMsgT | EventMsgT
type EventT = TrackStartEventT | TrackEndEventT | TrackExceptionEventT | TrackStuckEventT | WebSocketClosedEventT
