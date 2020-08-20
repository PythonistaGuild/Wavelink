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

from typing import Any, Dict, List, Type, TypeVar

from discord.ext import commands

import wavelink.abc
from .node import Node


__all__ = ('Track',
           'SearchableTrack',
           'YouTubeVideo',
           'SoundCloudTrack',
           'YouTubePlaylist')


class Track(wavelink.abc.Playable):
    """a Lavalink track object.

    Attributes
    ------------
    id: str
        The Base64 Track ID, can be used to rebuild track objects.
    info: Dict[str, Any]
        The raw track info.
    title: str
        The track title.
    identifier: Optional[str]
        The tracks identifier. could be None depending on track type.
    length:
        The duration of the track.
    duration:
        Alias to ``length``.
    uri: Optional[str]
        The tracks URI. Could be None.
    author: Optional[str]
        The author of the track. Could be None
    """

    def __init__(self, id: str, info: Dict[str, Any]):
        self.id = id
        self.info = info
        self.title = info.get('title')
        self.identifier = info.get('identifier')
        self.length = self.duration = info.get('length')
        self.uri = info.get('uri')
        self.author = info.get('author')

        self._stream: bool = info.get('isStream')  # type: ignore
        self._dead = False

    def __str__(self):
        return self.title

    def is_stream(self) -> bool:
        """Indicates whether the track is a stream or not."""
        return self._stream

    def is_dead(self) -> bool:
        """Indicates whether the track is dead or not."""
        return self._dead


T = TypeVar('T', bound='SearchableTrack')


class SearchableTrack(Track, wavelink.abc.Searchable):
    """Reperesents a Lavalink track object which type can be searched for.

    This class is a subclas of :class:`~wavelink.track.Track` and as a result
    inherits it's attributes.
    """

    _search_type: str = None  # type: ignore

    @classmethod
    async def search(cls: Type[T], node: Node, query: str) -> List[T]:
        """|coro|

        Search for tracks of this type which match a query.

        Parameters
        ----------
        node: :class:`~wavelink.node.Node`
            The :class:`~wavelink.node.Node` to use when searching.
        query: str
            The query to search for tracks which relate to.

        Returns
        -------
        List[`~wavelink.track.SearchableTrack`]
            A list of search results.
        """
        return await node.get_tracks(cls, f'{cls._search_type}:{query}')

    @classmethod
    async def convert(cls, ctx: commands.Context, argument: str):
        node = Node.get_best_node(ctx.bot)
        results = await cls.search(node, argument)  # type: ignore

        if not results:
            raise commands.BadArgument('Could not find any songs matching that query.')

        return results[0]


class YouTubeVideo(SearchableTrack):
    """Reperesents a Lavalink YouTube video object.

    This class is a subclas of :class:`~wavelink.track.SearchableTrack` and as a result
    inherits it's attributes.
    """

    _search_type = 'ytsearch'

    @property
    def thumbnail(self) -> str:
        """The URL to the thumbnail of this video."""
        return f"https://img.youtube.com/vi/{self.identifier}/maxresdefault.jpg"

    thumb = thumbnail


class SoundCloudTrack(SearchableTrack):
    """Reperesents a Lavalink SoundCloud track object.

    This class is a subclas of :class:`~wavelink.track.SearchableTrack` and as a result
    inherits it's attributes.
    """

    _search_type = 'scsearch'


class YouTubePlaylist(wavelink.abc.Playlist):
    """Reperesents a Lavalink YouTube playlist object.

    Attributes
    ----------
    name: str
        The name of the playlist.
    tracks: :class:`~wavelink.track.YouTubeVideo`
        The list of :class:`~wavelink.track.YouTubeVideo` in the playlist.
    selected_track: Optional[int]
        The selected video in the playlist. This could be ``None``.
    """

    def __init__(self, data: Dict[str, Any]):
        self.tracks: List[YouTubeVideo] = []
        self.name = data['playlistInfo']['name']
        self.selected_track = data['playlistInfo'].get('selectedTrack')
        if self.selected_track is not None:
            self.selected_track = int(self.selected_track)

        for track_data in data['tracks']:
            track = YouTubeVideo(track_data['track'], track_data['info'])
            self.tracks.append(track)
