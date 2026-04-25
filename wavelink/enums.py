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

from enum import StrEnum


# fmt: off
class TrackEndReason(StrEnum):
    finished   = "finished"    # The track finished playing. Can start next: True
    loadFailed = "loadFailed"  # The track failed to load. Can start next: True
    stopped    = "stopped"     # The track was stopped. Can start next: False
    replaced   = "replaced"    # The track was replaced. Can start next: False
    cleanup    = "cleanup"     # The track was cleaned up. Can start next: False


class LoadResult(StrEnum):
    track    = "track"     # A track has been loaded
    playlist = "playlist"  # A playlist has been loaded
    search   = "search"    # A search result has been loaded
    empty    = "empty"     # There has been no matches for your identifier
    error    = "error"     # Loading has failed with an error


class Source(StrEnum):
    youtube = "ytsearch"
    youtube_music = "ytmsearch"
    soundcloud = "scsearch"
    spotify = "spsearch"
    local = "local"
