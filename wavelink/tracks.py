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

from typing import TYPE_CHECKING, overload

import yarl

from .enums import TrackSource
from .node import Node, Pool

if TYPE_CHECKING:
    from .types.tracks import TrackInfoPayload, TrackPayload


_source_mapping: dict[TrackSource | str | None, str] = {
    TrackSource.YouTube: "ytsearch:",
    TrackSource.SoundCloud: "scsearch:",
    TrackSource.YouTubeMusic: "ytmsearch:",
}


class Playable:
    def __init__(self, data: TrackPayload) -> None:
        info: TrackInfoPayload = data["info"]

        self.encoded: str = data["encoded"]
        self.identifier: str = info["identifier"]
        self.is_seekable: bool = info["isSeekable"]
        self.author: str = info["author"]
        self.length: int = info["length"]
        self.is_stream: bool = info["isStream"]
        self.position: int = info["position"]
        self.title: str = info["title"]
        self.uri: str | None = info.get("uri")
        self.artwork: str | None = info.get("artworkUrl")
        self.isrc: str | None = info.get("isrc")
        self.source: str = info["sourceName"]

    def __hash__(self) -> int:
        return hash(self.encoded)

    def __str__(self) -> str:
        return self.title

    def __repr__(self) -> str:
        return f"Playable(source={self.source}, title={self.title}, identifier={self.identifier})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Playable):
            raise NotImplemented

        return self.encoded == other.encoded

    @overload
    async def search(self, query: str, /, source: TrackSource | str | None) -> list[Playable]:
        ...

    @overload
    async def search(self, query: str, /, source: TrackSource | str | None) -> Playlist:
        ...

    async def search(self, query: str, /, source: TrackSource | str | None):
        prefix: TrackSource | str | None = _source_mapping.get(source, source)
        check = yarl.URL(query)

        if str(check.host) == "youtube.com" or str(check.host) == "www.youtube.com" and check.query.get("list"):
            ytplay: Playlist = await Pool._fetch_playlist(query, cls_=Playlist)
            return ytplay

        elif str(check.host) == "soundcloud.com" or str(check.host) == "www.soundcloud.com" and "sets" in check.parts:
            scplay: Playlist = await Pool._fetch_playlist(query, cls_=Playlist)
            return scplay

        elif check.host:
            tracks: list[Playable] = await Pool._fetch_tracks(query, cls_=Playable)
            return tracks

        else:
            if isinstance(prefix, TrackSource) or not prefix:
                term: str = query
            else:
                term: str = f"{prefix}{query}"

            tracks: list[Playable] = await Pool._fetch_tracks(term, cls_=Playable)

            return tracks


class Playlist:
    ...
