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
from discord.enums import Enum

__all__ = ('NodeStatus', 'TrackSource', 'LoadType', 'TrackEventType')


class NodeStatus(Enum):

    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2


class TrackSource(Enum):

    YouTube = 0
    YouTubeMusic = 1
    SoundCloud = 2
    Local = 3
    Unknown = 4


class LoadType(Enum):

    track_loaded = "TRACK_LOADED"
    playlist_loaded = "PLAYLIST_LOADED"
    search_result = "SEARCH_RESULT"
    no_matches = "NO_MATCHES"
    load_failed = "LOAD_FAILED"


class TrackEventType(Enum):

    START = 'TrackStartEvent'
    END = 'TrackEndEvent'
