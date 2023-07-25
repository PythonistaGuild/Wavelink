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

from typing import TYPE_CHECKING, Any, TypeAlias, Union, overload

import yarl

import wavelink

from .enums import TrackSource

if TYPE_CHECKING:
    from .types.tracks import (
        PlaylistInfoPayload,
        PlaylistPayload,
        TrackInfoPayload,
        TrackPayload,
    )


_source_mapping: dict[TrackSource | str | None, str] = {
    TrackSource.YouTube: "ytsearch",
    TrackSource.SoundCloud: "scsearch",
    TrackSource.YouTubeMusic: "ytmsearch",
}


Search: TypeAlias = "list[Playable] | list[Playlist]"


class Album:
    def __init__(self, *, data: dict[Any, Any]) -> None:
        self.name: str | None = data.get("albumName")
        self.url: str | None = data.get("albumUrl")


class Artist:
    def __init__(self, *, data: dict[Any, Any]) -> None:
        self.url: str | None = data.get("artistUrl")
        self.artwork: str | None = data.get("artistArtworkUrl")


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

        plugin: dict[Any, Any] = data["pluginInfo"]
        self.album: Album = Album(data=plugin)
        self.artist: Artist = Artist(data=plugin)

        self.preview_url: str | None = plugin.get("previewUrl")
        self.is_preview: bool | None = plugin.get("isPreview")

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

    @classmethod
    async def search(cls, query: str, /, *, source: TrackSource | str | None = TrackSource.YouTube) -> Search:
        prefix: TrackSource | str | None = _source_mapping.get(source, source)
        check = yarl.URL(query)

        if check.host:
            tracks: Search = await wavelink.Pool.fetch_tracks(query)
            return tracks

        if not prefix:
            term: str = query
        else:
            assert not isinstance(prefix, TrackSource)
            term: str = f"{prefix.removesuffix(':')}:{query}"

        tracks: Search = await wavelink.Pool.fetch_tracks(term)
        return tracks


class Playlist:
    def __init__(self, data: PlaylistPayload) -> None:
        info: PlaylistInfoPayload = data["info"]
        self.name: str = info["name"]
        self.selected: int = info["selectedTrack"]

        self.tracks: list[Playable] = [Playable(data=track) for track in data["tracks"]]

        plugin: dict[Any, Any] = data["pluginInfo"]
        self.type: str | None = plugin.get("type")
        self.url: str | None = plugin.get("url")
        self.artwork: str | None = plugin.get("artworkUrl")
        self.author: str | None = plugin.get("author")

    def __str__(self) -> str:
        return self.name
