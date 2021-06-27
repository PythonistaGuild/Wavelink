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

import base64
import enum
import re
import time
from typing import List, Optional, Type, TypeVar, Union

import aiohttp
from discord.ext import commands

import wavelink
from wavelink import Node, NodePool, YouTubeTrack
from wavelink.utils import MISSING


__all__ = ('SpotifySearchType',
           'SpotifyClient',
           'SpotifyTrack',
           'SpotifyRequestError')


GRANTURL = 'https://accounts.spotify.com/api/token?grant_type=client_credentials'
URLREGEX = re.compile(r'https://open\.spotify\.com/(?P<entity>.+)/(?P<identifier>.+)\?')
BASEURL = 'https://api.spotify.com/v1/{entity}s/{identifier}'

ST = TypeVar("ST", bound="SearchableTrack")


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
                      type: SpotifySearchType = SpotifySearchType.track
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


class SpotifyTrack(YouTubeTrack):
    """A track retrieved via YouTube with a Spotify URL/ID."""

    @classmethod
    async def search(
        cls: Type[ST],
            query: str,
            *,
            spotify_type: SpotifySearchType = SpotifySearchType.track,
            node: Node = MISSING,
            return_first: bool = False
    ) -> Union[Optional[ST], List[ST]]:
        """|coro|

        Search for tracks with the given query.

        Parameters
        ----------
        query: str
            The song to search for.
        spotify_type: Optional[:class:`spotify.SpotifySearchType`]
            An optional enum value to use when searching with Spotify.
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

        tracks = await node._spotify._search(query=query, type=spotify_type)

        if return_first:
            return tracks[0]

        return tracks

    @classmethod
    async def convert(cls: Type[ST], ctx: commands.Context, argument: str) -> ST:
        """Converter which searches for and returns the first track.

        Used as a type hint in a discord.py command.
        """
        results = await cls.search(argument)

        if not results:
            raise commands.BadArgument("Could not find any songs matching that query.")

        return results[0]