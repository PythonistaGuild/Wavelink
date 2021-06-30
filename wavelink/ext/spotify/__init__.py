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

import asyncio
import base64
import enum
import re
import time
from typing import List, Optional, Type, TypeVar, Union

import aiohttp
from discord.ext import commands

import wavelink
from wavelink import Node, NodePool, PartialTrack, YouTubeTrack
from wavelink.utils import MISSING


__all__ = ('SpotifySearchType',
           'SpotifyClient',
           'SpotifyTrack',
           'SpotifyRequestError',
           'decode_url')


GRANTURL = 'https://accounts.spotify.com/api/token?grant_type=client_credentials'
URLREGEX = re.compile(r'https://open\.spotify\.com/(?P<entity>.+)/(?P<identifier>.+)\?')
BASEURL = 'https://api.spotify.com/v1/{entity}s/{identifier}'

ST = TypeVar("ST", bound="SearchableTrack")


def decode_url(url: str) -> Optional[dict]:
    """Check whether the given URL is a valid Spotify URL and return it's type and ID.

    Parameters
    ----------
    url: str
        The URL to check.

    Returns
    -------
    Optional[dict]
        An mapping of :class:`SpotifySearchType` and Spotify ID. Type will be either track, album or playlist.
        If type is not track, album or playlist, a special unusable type is returned.

        Could return None if the URL is invalid.

    Examples
    --------

    .. code:: python3

        from wavelink.ext import spotify

        ...

        decoded = spotify.decode_url("https://open.spotify.com/track/6BDLcvvtyJD2vnXRDi1IjQ?si=e2e5bd7aaf3d4a2a")

        if decoded and decoded['type'] is spotify.SpotifySearchType.track:
            track = await spotify.SpotifyTrack.search(query=decoded["id"], type=decoded["type"])
    """
    match = URLREGEX.match(url)
    if match:
        try:
            type_ = SpotifySearchType[match['entity']]
        except KeyError:
            type_ = SpotifySearchType.unusable

        return {'type': type_, 'id': match['identifier']}

    return None


class SpotifySearchType(enum.Enum):
    """An enum specifying which type to search for with a given Spotify ID.

    track
        Default search type. Unless specified otherwise this will always be the search type.
    album
        Search for an album.
    playlist
        Search for a playlist.
    """
    track = 0
    album = 1
    playlist = 2
    unusable = 3


class SpotifyAsyncIterator:

    def __init__(self, *, query: str, limit: int, type: SpotifySearchType, node: Node, partial: bool):
        self._query = query
        self._limit = limit
        self._type = type
        self._node = node

        self._partial = partial

        self._first = True
        self._count = 0
        self._queue = asyncio.Queue()

    def __aiter__(self):
        return self

    async def fill_queue(self):
        tracks = await self._node._spotify._search(query=self._query, iterator=True, type=self._type)

        for track in tracks:
            await self._queue.put(track)

    async def __anext__(self):
        if self._first:
            await self.fill_queue()
            self._first = False

        if self._limit is not None and self._count == self._limit:
            raise StopAsyncIteration

        try:
            track = self._queue.get_nowait()
        except asyncio.QueueEmpty:
            raise StopAsyncIteration

        if self._partial:
            track = PartialTrack(query=f'{track["name"]} - {track["artists"][0]["name"]}')
        else:
            track = (await wavelink.YouTubeTrack.search(query=f'{track["name"]} -'
                                                              f' {track["artists"][0]["name"]}'))[0]

        self._count += 1
        return track


class SpotifyRequestError(Exception):
    """Base error for Spotify requests.

    Attributes
    ----------
    status: int
        The status code returned from the request.
    reason: Optional[str]
        The reason the request failed. Could be None.
    """

    def __init__(self, status: int, reason: str = None):
        self.status = status
        self.reason = reason


class SpotifyClient:
    """Spotify client passed to Nodes for searching via Spotify.

    Parameters
    ----------
    client_id: str
        Your spotify application client ID.
    client_secret: str
        Your spotify application secret.
    """

    def __init__(self, *, client_id: str, client_secret: str):
        self._client_id = client_id
        self._client_secret = client_secret

        self.session = aiohttp.ClientSession()

        self._bearer_token: str = None  # type: ignore
        self._expiry: int = 0

    @property
    def grant_headers(self) -> dict:
        authbytes = f'{self._client_id}:{self._client_secret}'.encode()
        return {'Authorization': f'Basic {base64.b64encode(authbytes).decode()}',
                'Content-Type': 'application/x-www-form-urlencoded'}

    @property
    def bearer_headers(self) -> dict:
        return {'Authorization': f'Bearer {self._bearer_token}'}

    async def _get_bearer_token(self) -> None:
        async with self.session.post(GRANTURL, headers=self.grant_headers) as resp:
            if resp.status != 200:
                raise SpotifyRequestError(resp.status, resp.reason)

            data = await resp.json()
            self._bearer_token = data['access_token']
            self._expiry = time.time() + (int(data['expires_in']) - 10)

    async def _search(self,
                      query: str,
                      type: SpotifySearchType = SpotifySearchType.track,
                      iterator: bool = False,
                      ) -> Optional[List[YouTubeTrack]]:

        if not self._bearer_token or time.time() >= self._expiry:
            await self._get_bearer_token()

        regex_result = URLREGEX.match(query)

        if not regex_result:
            url = BASEURL.format(entity=type.name, identifier=query)
        else:
            url = BASEURL.format(entity=regex_result['entity'], identifier=regex_result['identifier'])

        async with self.session.get(url, headers=self.bearer_headers) as resp:
            if resp.status != 200:
                raise SpotifyRequestError(resp.status, resp.reason)

            data = await resp.json()

            if data['type'] == 'track':
                return await wavelink.YouTubeTrack.search(f'{data["name"]} - {data["artists"][0]["name"]}')

            elif data['type'] == 'album' and iterator is False:
                tracks = data['tracks']['items']
                return [(await wavelink.YouTubeTrack.search(f'{t["name"]} - {t["artists"][0]["name"]}'))[0]
                        for t in tracks]

            elif data['type'] == 'playlist' and iterator is False:
                ret = []
                tracks = data['tracks']['items']

                for track in tracks:
                    t = track['track']
                    ret.append((await wavelink.YouTubeTrack.search(f'{t["name"]} - {t["artists"][0]["name"]}'))[0])

                return ret

        if iterator is True:
            if data['type'] == 'playlist':
                if data['tracks']['next']:
                    url = data['tracks']['next']

                    items = [t['track'] for t in data['tracks']['items']]
                    while True:
                        async with self.session.get(url, headers=self.bearer_headers) as resp:
                            data = await resp.json()

                            items.extend([t['track'] for t in data['items']])
                            if not data['next']:
                                return items

                            url = data['next']
                else:
                    return [t['track'] for t in data['tracks']['items']]

            return data['tracks']['items']


class SpotifyTrack(YouTubeTrack):
    """A track retrieved via YouTube with a Spotify URL/ID."""

    @classmethod
    async def search(
        cls: Type[ST],
            query: str,
            *,
            type: SpotifySearchType = SpotifySearchType.track,
            node: Node = MISSING,
            return_first: bool = False
    ) -> Union[Optional[ST], List[ST]]:
        """|coro|

        Search for tracks with the given query.

        Parameters
        ----------
        query: str
            The song to search for.
        type: Optional[:class:`spotify.SpotifySearchType`]
            An optional enum value to use when searching with Spotify. Defaults to track.
        node: Optional[:class:`wavelink.Node`]
            An optional Node to use to make the search with.
        return_first: Optional[bool]
            An optional bool which when set to True will return only the first track found. Defaults to False.

        Returns
        -------
        Union[Optional[Track], List[Track]]
        """
        if node is MISSING:
            node = NodePool.get_node()

        if type == SpotifySearchType.track:
            tracks = await node._spotify._search(query=query, type=type)

            if return_first:
                return tracks[0]

            return tracks

        return await node._spotify._search(query=query, type=type)

    @classmethod
    def iterator(cls,
                 *,
                 query: str,
                 limit: Optional[int] = None,
                 type: SpotifySearchType = SpotifySearchType.playlist,
                 node: Optional[Node] = MISSING,
                 partial_tracks: bool = False
                 ):
        """An async iterator version of search.

        This can be useful when searching for large playlists or albums with Spotify.

        Parameters
        ----------
        query: str
            The Spotify URL or ID to search for. Must be of type Playlist or Album.
        limit: Optional[int]
            Limit the amount of tracks returned.
        type: :class:`SpotifySearchType`
            The type of search. Must be either playlist or album. Defaults to playlist.
        node: Optional[:class:`Node`]
            An optional node to use when querying for tracks. Defaults to best available.
        partial_tracks: Optional[bool]
            Whether or not to create :class:`wavelink.tracks.PartialTrack` objects for search at playtime.
            This can make queuing large albums or playlists considerably faster, but with less information.
            Defaults to False.

        Examples
        --------

        .. code:: python3

                async for track in spotify.SpotifyTrack.iterator(query=..., type=spotify.SpotifySearchType.playlist):
                    ...
        """

        if type is not SpotifySearchType.album and type is not SpotifySearchType.playlist:
            raise TypeError("Iterator search type must be either album or playlist.")

        if node is MISSING:
            node = NodePool.get_node()

        return SpotifyAsyncIterator(query=query, limit=limit, node=node, type=type, partial=partial_tracks)

    @classmethod
    async def convert(cls: Type[ST], ctx: commands.Context, argument: str) -> ST:
        """Converter which searches for and returns the first track.

        Used as a type hint in a discord.py command.
        """
        results = await cls.search(argument)

        if not results:
            raise commands.BadArgument("Could not find any songs matching that query.")

        return results[0]
