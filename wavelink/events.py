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
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .player import Player
    from .player import Track


__all__ = ('WavelinkEvent', 'TrackEnd', 'TrackException', 'TrackStuck', 'TrackStart', 'WebsocketClosed')


class WavelinkEvent:
    """Base Wavelink event class. Most events derive from this class.

    Attributes
    ------------
    player: :class:`wavelink.player.Player`
        The player associated with the event.
    track: :class:`wavelink.player.Track`
        The track associated with the event.
    """

    __slots__ = ('player', 'track')

    def __init__(self, player: Player, track: Track):
        self.player = player
        self.track = track


class TrackEnd(WavelinkEvent):
    """Event dispatched on TrackEnd.

    Attributes
    ------------
    player: :class:`wavelink.player.Player`
        The player associated with the event.
    track: :class:`wavelink.player.Track`
        The track associated with the event.
    reason: str
        The reason the TrackEnd event was dispatched.
    """

    __slots__ = ('reason', )

    def __init__(self, player: Player, track: Track, reason: str):
        super().__init__(player, track)
        self.reason = reason

    def __str__(self):
        return 'TrackEnd'


class TrackException(WavelinkEvent):
    """Event dispatched on TrackException.

    Attributes
    ------------
    player: :class:`wavelink.player.Player`
        The player associated with the event.
    track: :class:`wavelink.player.Track`
        The track associated with the event.
    error: str
        The error reason dispatched with the event.
    """

    __slots__ = ('error', )

    def __init__(self, player: Player, track: Track, error: str):
        super().__init__(player, track)
        self.error = error

    def __str__(self):
        return 'TrackException'


class TrackStuck(WavelinkEvent):
    """Event dispatched on TrackStuck.

    Attributes
    ------------
    player: :class:`wavelink.player.Player`
        The player associated with the event.
    track: :class:`wavelink.player.Track`
        The track associated with the event.
    threshold: int
        The threshold associated with the event.
    """

    __slots__ = ('threshold', )

    def __init__(self, player: Player, track: Track, threshold: int):
        super().__init__(player, track)
        self.threshold = threshold

    def __str__(self):
        return 'TrackStuck'


class TrackStart(WavelinkEvent):
    """Event dispatched on TrackStart.

    Attributes
    ------------
    player: :class:`wavelink.player.Player`
        The player associated with the event.
    track: :class:`wavelink.player.Track`
        The track associated with the event.
    """

    __slots__ = ()

    def __init__(self, player: Player, track: Track):
        super().__init__(player, track)

    def __str__(self):
        return 'TrackStart'


class WebsocketClosed:
    """Event dispatched when a player disconnects from a Guild.

    Attributes
    ------------
    player: :class:`wavelink.player.Player`
        The player associated with the event.
    reason: str
        The reason the event was dispatched.
    code: int
        The websocket reason code.
    guild_id: int
        The guild ID associated with the disconnect.
    """

    def __init__(self, player: Player, reason: str, code: int, guild_id: int):
        self.player = player
        self.reason = reason
        self.code = code
        self.guild_id = guild_id

    def __str__(self):
        return 'WebsocketClosed'
