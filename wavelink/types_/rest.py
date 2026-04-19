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
from typing import Any, Never, NotRequired, TypedDict, Literal, TYPE_CHECKING


if TYPE_CHECKING:
    from .websocket import TrackExceptionT


type LoadResultT = Literal["track", "playlist", "search", "empty", "error"]


class ErrorRespT(TypedDict):
    timestamp: int
    status: int
    error: str
    trace: NotRequired[str]
    message: str
    path: str


class TrackInfoRespT(TypedDict):
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


class TrackRespT(TypedDict):
    encoded: str
    info: TrackInfoRespT
    pluginInfo: dict[Any, Any]
    userData: dict[Any, Any]


class PlaylistInfoRespT(TypedDict):
    name: str
    selectedTrack: int


class TrackResultT(TypedDict):
    loadType: Literal["track"]
    data: TrackRespT


class PlaylistResultDataT(TypedDict):
    info: PlaylistInfoRespT
    pluginInfo: dict[Any, Any]
    tracks: list[TrackRespT]


class PlaylistResultT(TypedDict):
    loadType: Literal["playlist"]
    data: PlaylistResultDataT


class SearchResultT(TypedDict):
    loadType: Literal["search"]
    data: list[TrackRespT]


class EmptyResultT(TypedDict):
    loadType: Literal["empty"]
    data: dict[Never, Never]


class ErrorResultT(TypedDict):
    loadType: Literal["error"]
    data: TrackExceptionT


class PlayerStateT(TypedDict):
    time: int
    position: int
    connected: bool
    ping: int

class VoiceStateT(TypedDict):
    token: str
    endpoint: str
    sessionId: str
    channelId: str | None
    
class PlayerResptT(TypedDict):
    guildId: str
    track: TrackRespT | None
    volume: int
    paused: bool
    state: ...
    voice: ...
    filters: ...
    