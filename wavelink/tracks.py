"""MIT License

Copyright (c) 2019-2021 PythonistaGuild

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

from discord.ext import commands

from .abc import *
from .pool import Node, NodePool


__all__ = ("Track",
           "SearchableTrack",
           "YouTubeTrack",
           "YouTubeMusicTrack",
           "SoundCloudTrack",
           "YouTubePlaylist"
           )


class Track(Playable):
    """A Lavalink track object.

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
        The duration of the track in seconds.
    duration:
        Alias to ``length``.
    uri: Optional[str]
        The tracks URI. Could be None.
    author: Optional[str]
        The author of the track. Could be None
    """

    def __init__(self, id: str, info: dict):
        super().__init__(id, info)
        self.title = info.get('title')
        self.identifier = info.get('identifier')
        self.uri = info.get('uri')
        self.author = info.get('author')

        self._stream: bool = info.get('isStream')  # type: ignore
        self._dead = False

    def __str__(self):
        return self.title

    def is_stream(self) -> bool:
        """Indicates whether the track is a stream or not."""
        return self._stream


class SearchableTrack(Track, Searchable):

    _search_type: str = None

    @classmethod
    async def search(cls, query: str, *, node: Node = None, return_first: bool = False):
        """|coro|

        Search for tracks with the given query.

        Parameters
        ----------
        query: str
            The song to search for.
        node: Optional[:class:`wavelink.Node`]
            An optional Node to use to make the search with.
        return_first: Optional[bool]
            An optional bool which when set to True will return only the first track found. Defaults to False.

        Returns
        -------
        Union[Track, List[Track]]
        """
        node = node or NodePool.get_node()

        tracks = await node.get_tracks(cls, f'{cls._search_type}:{query}')

        if return_first:
            return tracks[0]

        return tracks

    @classmethod
    async def convert(cls, ctx: commands.Context, argument: str):
        """Converter which searches for and returns the first track.

        Used as a type hint in a discord.py command.
        """
        results = await cls.search(argument)

        if not results:
            raise commands.BadArgument('Could not find any songs matching that query.')

        return results[0]


class YouTubeTrack(SearchableTrack):
    """A track created using a search to YouTube."""

    _search_type: str = 'ytsearch'

    @property
    def thumbnail(self) -> str:
        """The URL to the thumbnail of this video."""
        return f"https://img.youtube.com/vi/{self.identifier}/maxresdefault.jpg"

    thumb = thumbnail


class YouTubeMusicTrack(SearchableTrack):
    """A track created using a search to YouTube Music."""

    _search_type: str = 'ytmsearch'


class SoundCloudTrack(SearchableTrack):
    """A track created using a search to SoundCloud."""

    _search_type: str = 'scsearch'


class YouTubePlaylist(Playlist):
    """Represents a Lavalink YouTube playlist object.

    Attributes
    ----------
    name: str
        The name of the playlist.
    tracks: :class:`YouTubeTrack`
        The list of :class:`YouTubeTrack` in the playlist.
    selected_track: Optional[int]
        The selected video in the playlist. This could be ``None``.
    """

    def __init__(self, data: dict):
        self.tracks = []
        self.name = data['playlistInfo']['name']

        self.selected_track = data['playlistInfo'].get('selectedTrack')
        if self.selected_track is not None:
            self.selected_track = int(self.selected_track)

        for track_data in data['tracks']:
            track = YouTubeTrack(track_data['track'], track_data['info'])
            self.tracks.append(track)
