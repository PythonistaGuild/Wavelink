class TrackEnd:
    """Event dispatched on TrackEnd.

    :ivar player: The :class:`wavelink.player.Player` associated with the event.
    :ivar track: The :class:`wavelink.player.Track` associated with the event.
    :ivar reason: The reason the TrackEnd event was dispatched.
    """

    __slots__ = ('player', 'track', 'reason')

    def __init__(self, player, track, reason: str):
        self.player = player
        self.track = track
        self.reason = reason

    def __str__(self):
        return 'TrackEnd'


class TrackException:
    """Event dispatched on TrackException.

    :ivar player: The :class:`wavelink.player.Player` associated with the event.
    :ivar track: The :class:`wavelink.player.Track` associated with the event.
    :ivar error: The error associated with the event.
    """

    __slots__ = ('player', 'track', 'error')

    def __init__(self, player, track, error: Exception):
        self.player = player
        self.track = track
        self.error = error

    def __str__(self):
        return 'TrackException'


class TrackStuck:
    """Event dispatched on TrackStuck.

    :ivar player: The :class:`wavelink.player.Player` associated with the event.
    :ivar track: The :class:`wavelink.player.Track` associated with the event.
    :ivar threshold: The threshold associated with the event.
    """

    __slots__ = ('player', 'track', 'threshold')

    def __init__(self, player, track, threshold: int):
        self.player = player
        self.track = track
        self.threshold = threshold

    def __str__(self):
        return 'TrackStuck'
