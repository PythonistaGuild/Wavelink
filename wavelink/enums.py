"""Copyright 2026 Evie. P. <evieepy@gmail.com>, PythonistaGuild

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import annotations

import enum


__all__ = ("AutoPlay", "EventType", "LoadResult", "Source", "TrackEndReason")


# fmt: off
class TrackEndReason(enum.StrEnum):
    """:class:`enum.StrEnum` representing the Track End Reason received by Lavalink.
    
    Attributes
    ----------
    finished: str
        The track finished playing. Can start the next track.
    load_failed: str
        The track failed to load. Can start the next track.
    stopped: str
        The track was stopped. Cannot start the next track.
    replaced: str
        The track was replaced. Cannot start the next track.
    cleanup: str
        The track was cleaned up. Cannot start the next track.
    """
    finished   = "finished"    # The track finished playing. Can start next: True
    load_failed = "loadFailed"  # The track failed to load. Can start next: True
    stopped    = "stopped"     # The track was stopped. Can start next: False
    replaced   = "replaced"    # The track was replaced. Can start next: False
    cleanup    = "cleanup"     # The track was cleaned up. Can start next: False


class LoadResult(enum.StrEnum):
    """:class:`enum.StrEnum` representing the load result from the /loadtracks endpoint.
    
    Attributes
    ----------
    track: str
        A single track has been loaded.
    playlist: str
        A playlist has been loaded.
    search: str
        A search has been loaded.
    empty: str
        There has been no matches for your identifier.
    error: str
        There was an error loading results.
    """
    track    = "track"     # A track has been loaded
    playlist = "playlist"  # A playlist has been loaded
    search   = "search"    # A search result has been loaded
    empty    = "empty"     # There has been no matches for your identifier
    error    = "error"     # Loading has failed with an error


class Source(enum.StrEnum):
    """:class:`enum.StrEnum` representing a music source to search from. E.g. Youtube or Spotify.
    
    Attributes
    ----------
    youtube: Literal["ytsearch"]
        Source representing Youtube.
    youtube_music: Literal["ytmsearch"]
        A source representing Youtube Music.
    soundcloud: Literal["scsearch"]
        A source representing SoundCloud.
    spotify: Literal["spsearch"]
        A source representing Spotify.
    local: Literal["local"]
        A source representing a raw or local search. E.g. a URL or File Path.
    """
    youtube       = "ytsearch"
    youtube_music = "ytmsearch"
    soundcloud    = "scsearch"
    spotify       = "spsearch"
    local         = "local"


class AutoPlay(enum.Enum):
    """..."""
    disabled = enum.auto()
    enabled = enum.auto()
    with_recommendations = enum.auto()


class EventType(enum.StrEnum):
    """:class:`enum.StrEnum` representing the event types dispatched via the Websocket.
    
    Attributes
    ----------
    TrackStart: Literal["track_start"]
    TrackEnd: Literal["track_end"]
    TrackException: Literal["track_exception"]
    TrackStuck: Literal["track_stuck"]
    WebsocketClosed: Literal["websocket_closed"]
    PlayerUpdate: Literal["player_update"]
    NodeStats: Literal["node_stats"]
    NodeReady: Literal["node_ready"]
    """
    TrackStart      = "track_start"
    TrackEnd        = "track_end"
    TrackException  = "track_exception"
    TrackStuck      = "track_stuck"
    WebsocketClosed = "websocket_closed"
    PlayerUpdate    = "player_update"
    NodeStats       = "node_stats"
    NodeReady       = "node_ready"

    @classmethod
    def all(cls) -> tuple[EventType, ...]:
        return tuple(m for m in cls)

    @classmethod
    def all_track(cls) -> tuple[EventType, ...]:
        return tuple(m for m in cls if m.startswith("track_"))
