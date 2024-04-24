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

from typing import Any, TypedDict

from typing_extensions import NotRequired


class TrackInfoPayload(TypedDict):
    identifier: str
    isSeekable: bool
    author: str
    length: int
    isStream: bool
    position: int
    title: str
    uri: NotRequired[str]
    artworkUrl: NotRequired[str]
    isrc: NotRequired[str]
    sourceName: str


class PlaylistInfoPayload(TypedDict):
    name: str
    selectedTrack: int


class TrackPayload(TypedDict):
    encoded: str
    info: TrackInfoPayload
    pluginInfo: dict[Any, Any]
    userData: dict[str, Any]


class PlaylistPayload(TypedDict):
    info: PlaylistInfoPayload
    tracks: list[TrackPayload]
    pluginInfo: dict[Any, Any]
