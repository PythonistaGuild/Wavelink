"""
MIT License

Copyright (c) 2019-Current PythonistaGuild, EvieePy

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

from typing import TypedDict

from typing_extensions import NotRequired

from ..filters import Filters
from ..tracks import Playable


class PlayerState(TypedDict):
    time: int
    position: int
    connected: bool
    ping: int


class VoiceState(TypedDict, total=False):
    token: str
    endpoint: str | None
    session_id: str


class PlayerVoiceState(TypedDict):
    voice: VoiceState
    channel_id: NotRequired[str]
    track: NotRequired[str]
    position: NotRequired[int]


class PlayerBasicState(TypedDict):
    """A dictionary of basic state for the Player.

    Attributes
    ----------
    voice_state: :class:`PlayerVoiceState`
        The voice state received via Discord. Includes the voice connection ``token``, ``endpoint`` and ``session_id``.
    position: int
        The player position.
    connected: bool
        Whether the player is currently connected to a channel.
    current: :class:`~wavelink.Playable` | None
        The currently playing track or `None` if no track is playing.
    paused: bool
        The players paused state.
    volume: int
        The players current volume.
    filters: :class:`~wavelink.Filters`
        The filters currently assigned to the Player.
    """

    voice_state: PlayerVoiceState
    position: int
    connected: bool
    current: Playable | None
    paused: bool
    volume: int
    filters: Filters
