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

__all__ = ('NodeStatus', 'TrackSource', 'LoadType', 'TrackEventType', 'DiscordVoiceCloseType')


class NodeStatus(Enum):
    """Enum representing the current status of a Node.

    Attributes
    ----------
    DISCONNECTED
        0
    CONNECTING
        1
    CONNECTED
        2
    """

    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2


class TrackSource(Enum):
    """Enum representing the Track Source Type.

    Attributes
    ----------
    YouTube
        0
    YouTubeMusic
        1
    SoundCloud
        2
    Local
        3
    Unknown
        4
    """

    YouTube = 0
    YouTubeMusic = 1
    SoundCloud = 2
    Local = 3
    Unknown = 4


class LoadType(Enum):
    """Enum representing the Tracks Load Type.

    Attributes
    ----------
    track_loaded
        "TRACK_LOADED"
    playlist_loaded
        "PLAYLIST_LOADED"
    search_result
        "SEARCH_RESULT"
    no_matches
        "NO_MATCHES"
    load_failed
        "LOAD_FAILED"
    """
    track_loaded = "TRACK_LOADED"
    playlist_loaded = "PLAYLIST_LOADED"
    search_result = "SEARCH_RESULT"
    no_matches = "NO_MATCHES"
    load_failed = "LOAD_FAILED"


class TrackEventType(Enum):
    """Enum representing the TrackEvent types.

    Attributes
    ----------
    START
        "TrackStartEvent"
    END
        "TrackEndEvent"
    """

    START = 'TrackStartEvent'
    END = 'TrackEndEvent'


class DiscordVoiceCloseType(Enum):
    """Enum representing the various Discord Voice Websocket Close Codes.

    Attributes
    ----------
    CLOSE_NORMAL
        1000
    UNKNOWN_OPCODE
        4001
    FAILED_DECODE_PAYLOAD
        4002
    NOT_AUTHENTICATED
        4003
    AUTHENTICATION_FAILED
        4004
    ALREADY_AUTHENTICATED
        4005
    SESSION_INVALID
        4006
    SESSION_TIMEOUT
        4009
    SERVER_NOT_FOUND
        4011
    UNKNOWN_PROTOCOL
        4012
    DISCONNECTED
        4014
    VOICE_SERVER_CRASHED
        4015
    UNKNOWN_ENCRYPTION_MODE
        4016
    """
    CLOSE_NORMAL = 1000  # Not Discord but standard websocket
    UNKNOWN_OPCODE = 4001
    FAILED_DECODE_PAYLOAD = 4002
    NOT_AUTHENTICATED = 4003
    AUTHENTICATION_FAILED = 4004
    ALREADY_AUTHENTICATED = 4005
    SESSION_INVALID = 4006
    SESSION_TIMEOUT = 4009
    SERVER_NOT_FOUND = 4011
    UNKNOWN_PROTOCOL = 4012
    DISCONNECTED = 4014
    VOICE_SERVER_CRASHED = 4015
    UNKNOWN_ENCRYPTION_MODE = 4016
