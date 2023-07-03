from __future__ import annotations

from typing import Optional, TypedDict


class TrackInfo(TypedDict):
    identifier: str
    isSeekable: bool
    author: str
    length: int
    isStream: bool
    position: int
    title: str
    uri: Optional[str]
    sourceName: str
    
class Track(TypedDict):
    encoded: str
    info: TrackInfo