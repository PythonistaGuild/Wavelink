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

from collections.abc import Mapping, MutableMapping
from typing import Any, Literal, Never, NotRequired, TypedDict

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
    pluginInfo: Mapping[Any, Any]
    userData: MutableMapping[Any, Any]


class PlaylistInfoRespT(TypedDict):
    name: str
    selectedTrack: int


class TrackResultT(TypedDict):
    loadType: Literal["track"]
    data: TrackRespT


class PlaylistResultDataT(TypedDict):
    info: PlaylistInfoRespT
    pluginInfo: Mapping[Any, Any]
    tracks: list[TrackRespT]


class PlaylistResultT(TypedDict):
    loadType: Literal["playlist"]
    data: PlaylistResultDataT


class SearchResultT(TypedDict):
    loadType: Literal["search"]
    data: list[TrackRespT]


class EmptyResultT(TypedDict):
    loadType: Literal["empty"]
    data: Mapping[Never, Never]


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


class PlayerRespT(TypedDict):
    guildId: str
    track: TrackRespT | None
    volume: int
    paused: bool
    state: PlayerStateT
    voice: VoiceStateT
    filters: ...


class UpdateSessionRespT(TypedDict):
    resuming: bool
    timeout: int


class VersionInfoT(TypedDict):
    semver: str
    major: int
    minor: int
    patch: int
    preRelease: str | None
    build: str | None


class GitInfoT(TypedDict):
    branch: str
    commit: str
    commitTime: str


class PluginInfoT(TypedDict):
    name: str
    version: str


class InfoRespT(TypedDict):
    version: VersionInfoT
    buildTime: int
    git: GitInfoT
    jvm: str
    lavaplayer: str
    sourceManagers: list[str]
    filters: list[str]
    plugins: list[PluginInfoT]


type HTTPMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD", "CONNECT", "TRACE"]
type LoadResultDataT = TrackResultT | PlaylistResultT | SearchResultT | EmptyResultT | ErrorResultT


# Requests
class UpdateSessionReqT(TypedDict, total=False):
    resuming: bool
    timeout: int


class UpdateTrackT(TypedDict):
    encoded: str
    identifier: NotRequired[str]
    userData: NotRequired[Mapping[Any, Any]]


class UpdatePlayerReqT(TypedDict, total=False):
    track: UpdateTrackT
    position: int
    endTime: int
    volume: int
    paused: bool
    filters: ...
    voice: VoiceStateT
