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

from typing import Literal, TypedDict

from typing_extensions import Never, NotRequired

from .filters import FilterPayload
from .state import PlayerState
from .stats import CPUStats, FrameStats, MemoryStats
from .tracks import PlaylistPayload, TrackPayload


class ErrorResponse(TypedDict):
    timestamp: int
    status: int
    error: str
    trace: NotRequired[str]
    message: str
    path: str


class LoadedErrorPayload(TypedDict):
    message: str
    severity: str
    cause: str


class VoiceStateResponse(TypedDict, total=False):
    token: str
    endpoint: str | None
    sessionId: str


class PlayerResponse(TypedDict):
    guildId: str
    track: NotRequired[TrackPayload]
    volume: int
    paused: bool
    state: PlayerState
    voice: VoiceStateResponse
    filters: FilterPayload


class UpdateResponse(TypedDict):
    resuming: bool
    timeout: int


class TrackLoadedResponse(TypedDict):
    loadType: Literal["track"]
    data: TrackPayload


class PlaylistLoadedResponse(TypedDict):
    loadType: Literal["playlist"]
    data: PlaylistPayload


class SearchLoadedResponse(TypedDict):
    loadType: Literal["search"]
    data: list[TrackPayload]


class EmptyLoadedResponse(TypedDict):
    loadType: Literal["empty"]
    data: dict[Never, Never]


class ErrorLoadedResponse(TypedDict):
    loadType: Literal["error"]
    data: LoadedErrorPayload


class VersionPayload(TypedDict):
    semver: str
    major: int
    minor: int
    patch: int
    preRelease: NotRequired[str]
    build: NotRequired[str]


class GitPayload(TypedDict):
    branch: str
    commit: str
    commitTime: int


class PluginPayload(TypedDict):
    name: str
    version: str


class InfoResponse(TypedDict):
    version: VersionPayload
    buildTime: int
    git: GitPayload
    jvm: str
    lavaplayer: str
    sourceManagers: list[str]
    filters: list[str]
    plugins: list[PluginPayload]


class StatsResponse(TypedDict):
    players: int
    playingPlayers: int
    uptime: int
    memory: MemoryStats
    cpu: CPUStats
    frameStats: NotRequired[FrameStats]
