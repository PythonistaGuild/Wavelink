"""MIT License
Copyright (c) 2019-2020 PythonistaGuild
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

from typing import Any, Dict, List, Type, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from .node import Node


__all__ = ('Playable',
           'Searchable',
           'Track',
           'Playlist',
           'YouTubeVideo',
           'SoundCloudTrack',
           'YouTubePlaylist')


class Playable:
    def __init__(self, id: str, data: Dict[str, Any]):
        self.id = id


T = TypeVar('T', bound='Searchable')


class Searchable(Playable):
    _search_type: str = None  # type: ignore

    @classmethod
    async def search(cls: Type[T], node: Node, query: str) -> List[T]:
        return await node.get_tracks(f'{cls._search_type}:{query}', cls=cls)


class Playlist:
    def __init__(self, data: Dict[str, Any]):
        raise NotImplementedError


class Track(Playable):

    def __init__(self, id: str, data: Dict[str, Any]):
        super().__init__(id, data)

        self.title = data.get('title')
        self.identifier = data.get('identifier')
        self.length = self.duration = data.get('length')
        self.uri = data.get('uri')
        self.author = data.get('author')

        self._stream = data.get('isStream')
        self._dead = False

    def __str__(self):
        return self.title

    def is_stream(self):
        return self._stream

    def is_dead(self):
        return self._dead


class YouTubeVideo(Track, Searchable):
    _search_type = 'ytsearch'

    @property
    def thumbnail(self):
        return f"https://img.youtube.com/vi/{self.identifier}/maxresdefault.jpg"

    thumb = thumbnail


class SoundCloudTrack(Track, Searchable):
    _search_type = 'scsearch'


class YouTubePlaylist(Playlist):

    def __init__(self, data: Dict[str, Any]):
        self.tracks: List[YouTubeVideo] = []
        self.name = data['playlistInfo']['name']
        self.selected_track = int(data['playlistInfo']['selectedTrack'])

        for track_data in data['tracks']:
            track = YouTubeVideo(track_data['track'], track_data['info'])
            self.tracks.append(track)
