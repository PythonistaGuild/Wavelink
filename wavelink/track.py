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

from typing import Any, Dict

__all__ = ('Track',
           'Playlist')


class Playable:
    ...


class Track(Playable):
    """Wavelink Tack object.
    Attributes
    ------------
    id: str
        The Base64 Track ID.
    info: dict
        The raw track info.
    title: str
        The track title.
    identifier: Optional[str]
        The tracks identifier. could be None depending on track type.
    ytid: Optional[str]
        The tracks YouTube ID. Could be None if ytsearch was not used.
    length:
        The duration of the track.
    duration:
        Alias to length.
    uri: Optional[str]
        The tracks URI. Could be None.
    author: Optional[str]
        The author of the track. Could be None
    is_stream: bool
        Indicated whether the track is a stream or not.
    thumb: Optional[str]
        The thumbnail URL associated with the track. Could be None.
    """

    def __init__(self, data: Dict[str, Any], query: str = None):
        self.id = data.get('track')
        self.query = query

        info = data['info']

        self.title = info.get('title')
        self.identifier = info.get('identifier')
        self.length = self.duration = info.get('length')
        self.uri = info.get('uri')
        self.author = info.get('author')

        self._stream = data.get('isStream')
        self._dead = False

    def __str__(self):
        return self.title

    def is_stream(self):
        return self._stream

    def is_dead(self):
        return self._dead


class YoutubeVideo(Track):

    def __init__(self, data: Dict[str, Any], query: str = None):
        super().__init__(data, query)
        self.thumb = f"https://img.youtube.com/vi/{self.identifier}/maxresdefault.jpg"


class Playlist:
    def __init__(self, data: Dict[str, Any]):
        self.tracks = [Track(track['track'], track) for track in data['tracks']]
