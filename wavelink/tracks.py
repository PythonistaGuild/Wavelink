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

from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Self

from .enums import LoadResult


# from types import SimpleNamespace


if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

    from .types_.rest import LoadResultDataT, PlaylistResultDataT, TrackInfoRespT, TrackRespT
    from .types_.websocket import TrackT


class Track:
    def __init__(self, data: TrackRespT | TrackT, *, playlist: Playlist | None = None) -> None:
        self._encoded: str = data["encoded"]

        info: TrackInfoRespT = data["info"]
        self._identifier = info["identifier"]
        self._seekable = info["isSeekable"]
        self._author = info["author"]
        self._length = info["length"]
        self._stream = info["isStream"]
        self._position = info["position"]
        self._title = info["title"]
        self._uri = info["uri"]
        self._artwork_url = info["artworkUrl"]
        self._isrc = info["isrc"]
        self._source_name = info["sourceName"]
        self._start = self._position
        self._end: int = self._length
        self._user_data = data["userData"]
        self._playlist = playlist

        # TODO: Plugin stuff...

    def __repr__(self) -> str:
        return f"Track(identifier={self._identifier!r}, source={self._source_name!r}, stream={self._stream})"

    def __str__(self) -> str:
        return self._title

    def __bytes__(self) -> bytes:
        return self._encoded.encode("UTF-8")

    def __hash__(self) -> int:
        return hash(self._encoded)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Track):
            return NotImplemented

        return other._encoded == self._encoded

    def __len__(self) -> int:
        return self._length

    def __int__(self) -> int:
        return self._position

    def __format__(self, spec: str, /) -> str:
        if spec == "id":
            return self._identifier

        if spec in ("uri", "url"):
            return self._uri or ""

        if spec == "b64":
            return self._encoded

        if spec == "time":
            return self.clock_length()

        if spec == "pos":
            return self.clock_position()

        return self._title

    def __iadd__(self, other: int) -> Self:
        self._start = min(self._length, self._start + other)
        return self

    def __isub__(self, other: int) -> Self:
        self._start = max(0, self._start - other)
        return self

    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    def encoded(self) -> str:
        return self._encoded

    @property
    def start(self) -> int:
        return self._start

    @start.setter
    def start(self, value: int) -> None:
        self._start = max(0, min(self._length, value))

    @property
    def end(self) -> int:
        return self._end

    @end.setter
    def end(self, value: int | None) -> None:
        self._end = max(1, min(self._length, value)) if value is not None else self._length

    def hms(self, ms: int) -> tuple[int, int, int]:
        seconds, _ = divmod(ms, 1000)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)

        return (hours, minutes, seconds)

    def clock_length(self) -> str:
        h, m, s = self.hms(self._length)
        return f"{h:02}:{m:02}:{s:02}"

    def clock_position(self) -> str:
        h, m, s = self.hms(self._position)
        return f"{h:02}:{m:02}:{s:02}"


class Search:
    __slots__ = ("_first", "_playlist_info", "_query", "_result", "_tracks")

    def __init__(self, query: str | None = None, *, data: LoadResultDataT) -> None:
        self._query = query
        self._result: LoadResult = LoadResult(data["loadType"])
        self._first: Track | None = None
        self._tracks: list[Track] = []
        self._playlist_info: Playlist | None = None

        match data:
            case {"loadType": "track"}:
                track = Track(data=data["data"])
                self._tracks = [track]
                self._first = track
            case {"loadType": "search"}:
                self._tracks = [Track(data=d) for d in data["data"]]
                self._first = self._tracks[0]
            case {"loadType": "playlist"}:
                playlist = Playlist(data["data"])
                self._first = playlist.first
                self._tracks = playlist.tracks
                self._playlist_info = playlist
            case _:
                # NOTE: Covered at request + defaults
                pass

    def __repr__(self) -> str:
        return f"Search(query={self._query!r}, tracks={len(self._tracks)}, first={self._first})"

    def __iter__(self) -> Iterator[Track]:
        return iter(self._tracks)

    def __len__(self) -> int:
        return len(self._tracks)

    def __bool__(self) -> bool:
        return bool(self._tracks)

    @property
    def result(self) -> LoadResult:
        return self._result

    @property
    def tracks(self) -> list[Track]:
        return self._tracks

    @property
    def first(self) -> Track | None:
        return self._first


class PlaylistInfo:
    __slots__ = ("_info", "_raw", "artwork", "author", "name", "selected", "type", "url")

    def __init__(self, data: PlaylistResultDataT) -> None:
        self._raw = data
        self._info = data["info"]
        self.name: str = self._info["name"]
        self.selected: int = self._info["selectedTrack"]

        plugin: Mapping[Any, Any] = data["pluginInfo"]
        self.type: str | None = plugin.get("type")
        self.url: str | None = plugin.get("url")
        self.artwork: str | None = plugin.get("artworkUrl")
        self.author: str | None = plugin.get("author")

    @property
    def info(self) -> Mapping[str, object]:
        return MappingProxyType(self._info)


class Playlist(PlaylistInfo):
    __slots__ = ("first", "tracks")

    def __init__(self, data: PlaylistResultDataT) -> None:
        super().__init__(data)
        self.tracks: list[Track] = [Track(d, playlist=self) for d in data["tracks"]]
        self.first = self.tracks[self.selected]
