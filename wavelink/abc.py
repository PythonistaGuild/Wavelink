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

import abc

from typing import Any, Dict


class Playable(metaclass=abc.ABCMeta):
    def __init__(self, id: str, data: Dict[str, Any]):
        self.id = id


class Playlist(metaclass=abc.ABCMeta):
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
