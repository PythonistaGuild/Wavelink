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
import enum
import re
from typing import Any, Optional


__all__ = (
    'GRANTURL',
    'URLREGEX',
    'BASEURL',
    'RECURL',
    'SpotifyDecodePayload',
    'decode_url',
    'SpotifySearchType'
)


GRANTURL = 'https://accounts.spotify.com/api/token?grant_type=client_credentials'
URLREGEX = re.compile(r'(https?://open.)?(spotify)(.com/|:)(.*[/:])?'
                      r'(?P<type>album|playlist|track|artist|show|episode)([/:])'
                      r'(?P<id>[a-zA-Z0-9]+)(\?si=[a-zA-Z0-9]+)?(&dl_branch=[0-9]+)?')
BASEURL = 'https://api.spotify.com/v1/{entity}s/{identifier}'
RECURL = 'https://api.spotify.com/v1/recommendations?seed_tracks={tracks}'


class SpotifySearchType(enum.Enum):
    """An enum specifying which type to search for with a given Spotify ID.

    Attributes
    ----------
    track
        Track search type.
    album
        Album search type.
    playlist
        Playlist search type.
    unusable
        Unusable type. This type is assigned when Wavelink can not be used to play this track.
    """
    track = 0
    album = 1
    playlist = 2
    unusable = 3


class SpotifyDecodePayload:
    """The SpotifyDecodePayload received when using :func:`decode_url`.

    .. container:: operations

        .. describe:: repr(payload)

            Returns an official string representation of this payload.

        .. describe:: payload['attr']

            Allows this object to be accessed like a dictionary.


    Attributes
    ----------
    type: :class:`SpotifySearchType`
        Either track, album or playlist.
        If type is not track, album or playlist, a special unusable type is assigned.
    id: str
        The Spotify ID associated with the decoded URL.


    .. note::

        To keep backwards compatibility with previous versions of :func:`decode_url`, you can access this object like
        a dictionary.


    .. warning::

        You do not instantiate this object manually. Instead you receive it via :func:`decode_url`.


    .. versionadded:: 2.6.0
    """

    def __init__(self, *, type_: SpotifySearchType, id_: str) -> None:
        self.__type = type_
        self.__id = id_

    def __repr__(self) -> str:
        return f'SpotifyDecodePayload(type={self.type}, id={self.id})'

    @property
    def type(self) -> SpotifySearchType:
        return self.__type

    @property
    def id(self) -> str:
        return self.__id

    def __getitem__(self, item: Any) -> SpotifySearchType | str:
        valid: list[str] = ['type', 'id']

        if item not in valid:
            raise KeyError(f'SpotifyDecodePayload object has no key {item}. Valid keys are "{valid}".')

        return getattr(self, item)


def decode_url(url: str) -> SpotifyDecodePayload | None:
    """Check whether the given URL is a valid Spotify URL and return a :class:`SpotifyDecodePayload` if this URL
    is valid, or ``None`` if this URL is invalid.

    Parameters
    ----------
    url: str
        The URL to check.

    Returns
    -------
    Optional[:class:`SpotifyDecodePayload`]
        The decode payload containing the Spotify :class:`SpotifySearchType` and Spotify ID.

        Could return ``None`` if the URL is invalid.

    Examples
    --------

    .. code:: python3

        from wavelink.ext import spotify


        decoded = spotify.decode_url("https://open.spotify.com/track/6BDLcvvtyJD2vnXRDi1IjQ?si=e2e5bd7aaf3d4a2a")


    .. versionchanged:: 2.6.0

        This function now returns :class:`SpotifyDecodePayload`. For backwards compatibility you can access this
        payload like a dictionary.
    """
    match = URLREGEX.match(url)
    if match:
        try:
            type_ = SpotifySearchType[match['type']]
        except KeyError:
            type_ = SpotifySearchType.unusable

        return SpotifyDecodePayload(type_=type_, id_=match['id'])

    return None

