"""
MIT License

Copyright (c) 2019-Present PythonistaGuild

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

import abc
from typing import TYPE_CHECKING, ClassVar, Literal, overload

from .enums import TrackSource
from .exceptions import NoTracksError
from .node import Node, NodePool

if TYPE_CHECKING:
    from typing_extensions import Self

    from .types.track import Track as TrackPayload

__all__ = ('Playable', 'YouTubeTrack', 'GenericTrack')


_source_mapping: dict[str, TrackSource] = {
    'youtube': TrackSource.YouTube
}


class Playable(metaclass=abc.ABCMeta):

    PREFIX: ClassVar[str] = ''
    
    def __init__(self, data: TrackPayload) -> None:
        self.data: TrackPayload = data
        self.encoded: str = data['encoded']

        info = data['info']
        self.is_seekable: bool = info.get('isSeekable', False)
        self.is_stream: bool = info.get('isStream', False)
        self.length: int = info.get('length', 0)
        self.duration: int = self.length
        self.position: int = info.get('position', 0)

        self.title: str = info.get('title', 'Unknown Title')

        source: str | None = info.get('sourceName')
        self.source: TrackSource = _source_mapping.get(source, TrackSource.Unknown)

        self.uri: str | None = info.get('uri')
        self.author: str | None = info.get('author')
        self.identifier: str | None = info.get('identifier')

    def __str__(self) -> str:
        return self.title

    def __repr__(self) -> str:
        return f'Playable: source={self.source}, title={self.title}'

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Playable):
            return self.encoded == other.encoded
        return NotImplemented
    
    @overload
    @classmethod
    async def search(cls,
                     query: str,
                     /,
                     *,
                     return_first: Literal[False] = ...,
                     node: Node | None = ...
                     ) -> list[Self]:
        ...

    @overload
    @classmethod
    async def search(cls,
                     query: str,
                     /,
                     *,
                     return_first: Literal[True] = ...,
                     node: Node | None = ...
                     ) -> Self:
        ...

    @overload
    @classmethod
    async def search(cls,
                     query: str,
                     /,
                     *,
                     return_first: bool = ...,
                     node: Node | None = ...
                     ) -> Self | list[Self]:
        ...

    @classmethod
    async def search(cls,
                     query: str,
                     /,
                     *,
                     return_first: bool = False,
                     node: Node | None = None
                     ) -> Self | list[Self]:

        tracks = await NodePool.get_tracks(f'{cls.PREFIX}{query}', cls=cls, node=node)
        
        try:
            track = tracks[0]
        except IndexError:
            raise NoTracksError(f'Your search query "{query}" returned no tracks.')

        if return_first:
            return track

        return tracks


class GenericTrack(Playable):
    ...


class YouTubeTrack(Playable):

    PREFIX: str = 'ytsearch:'

    @property
    def thumbnail(self) -> str:
        """The URL to the thumbnail of this video.

        .. note::

            Due to YouTube limitations this may not always return a valid thumbnail

        Returns
        -------
        str
            The URL to the video thumbnail.
        """
        return f"https://img.youtube.com/vi/{self.identifier}/maxresdefault.jpg"

    thumb = thumbnail
