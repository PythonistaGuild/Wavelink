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
import abc
from typing import Any, Optional, TYPE_CHECKING, TypeVar

from .enums import TrackSource
from .exceptions import NoTracksError
from .node import Node, NodePool


__all__ = ('Playable', 'YouTubeTrack')


_source_mapping: dict[str, TrackSource] = {
    'youtube': TrackSource.YouTube
}


P = TypeVar('P', bound='Playable')


class Playable(metaclass=abc.ABCMeta):

    def __init__(self, data: dict[str, Any]):
        self.data: dict[str, Any] = data
        self.encoded: str = data['encoded']

        data: dict[str, Any] = data['info']
        self.is_seekable: bool = data.get('isSeekable', False)
        self.is_stream: bool = data.get('isStream', False)
        self.length: int = data.get('length', 0)
        self.duration: int = self.length
        self.position: int = data.get('position', 0)

        self.title: str = data.get('title', 'Unknown Title')

        source: str | None = data.get('sourceName')
        self.source: TrackSource = _source_mapping.get(source, TrackSource.Unknown)

        self.uri: str | None = data.get('uri')
        self.author: str | None = data.get('author')
        self.identifier: str | None = data.get('identifier')

    def __str__(self) -> str:
        return self.title

    def __repr__(self) -> str:
        return f'Playable: source={self.source}, title={self.title}'

    def __eq__(self, other: P) -> bool:
        return other.encoded == self.encoded

    @classmethod
    @abc.abstractmethod
    async def search(cls,
                     query: str,
                     /,
                     *,
                     return_first: bool = False,
                     node: Node | None = None
                     ) -> P | list[P] | None:
        raise NotImplementedError


class YouTubeTrack(Playable):

    PREFIX: str = 'ytsearch:'

    def __init__(self, data: dict[str, Any]):
        super().__init__(data=data)

    @classmethod
    async def search(cls,
                     query: str,
                     /,
                     *,
                     return_first: bool = False,
                     node: Node | None = None
                     ) -> P | list[P] | None:

        query_: str = f'{cls.PREFIX}{query}'
        tracks: list[cls] = await NodePool.get_tracks(query_, cls=cls)

        if return_first:
            try:
                return tracks[0]
            except IndexError:
                raise NoTracksError(f'Your search query "{query}" returned no tracks.')

        return tracks
