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

__all__ = ('TrackEnd',
           'TrackException',
           'TrackStuck',
           'TrackStart',
           'WebsocketClosed')


class TrackEnd:
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

    __slots__ = ('track', 'player', 'reason')

    def __init__(self, data: dict):
        self.track = data.get('track')
        self.player = data.get('player')
        self.reason = data.get('reason')

    def __str__(self):
        return 'TrackEndEvent'


class TrackException:
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

    __slots__ = ('track', 'player', 'error')

    def __init__(self, data: dict):
        self.track = data.get('track')
        self.player = data.get('player')
        self.error = data.get('error')

    def __str__(self):
        return 'TrackExceptionEvent'


class TrackStuck:
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

    __slots__ = ('track', 'player', 'threshold')

    def __init__(self, data: dict):
        self.track = data.get('track')
        self.player = data.get('player')
        self.threshold = int(data.get('thresholdMs'))

    def __str__(self):
        return 'TrackStuckEvent'


class TrackStart:
    """Event dispatched on TrackStart.

    Attributes
    ------------
    player: :class:`wavelink.player.Player`
        The player associated with the event.
    track: :class:`wavelink.player.Track`
        The track associated with the event.
    """

    __slots__ = ('track', 'player')

    def __init__(self, data: dict):
        self.track = data.get('track')
        self.player = data.get('player')

    def __str__(self):
        return 'TrackStartEvent'


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

    __slots__ = ('player', 'reason', 'code', 'guild_id')

    def __init__(self, data: dict):
        self.player = data.get('player')
        self.reason = data.get('reason')
        self.code = data.get('code')
        self.guild_id = data.get('guildID')

    def __str__(self):
        return 'WebsocketClosedEvent'
