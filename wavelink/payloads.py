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
from __future__ import annotations

from typing import TYPE_CHECKING, cast

import wavelink

from .enums import DiscordVoiceCloseType

if TYPE_CHECKING:
    from .node import Node
    from .player import Player
    from .tracks import Playable
    from .types.state import PlayerState
    from .types.stats import CPUStats, FrameStats, MemoryStats
    from .types.websocket import StatsOP, TrackExceptionPayload


__all__ = (
    "TrackStartEventPayload",
    "TrackEndEventPayload",
    "TrackExceptionEventPayload",
    "TrackStuckEventPayload",
    "WebsocketClosedEventPayload",
    "PlayerUpdateEventPayload",
    "StatsEventPayload",
    "NodeReadyEventPayload",
    "StatsEventMemory",
    "StatsEventCPU",
    "StatsEventFrames",
)


class NodeReadyEventPayload:
    """Payload received in the :func:`on_wavelink_node_ready` event.

    Attributes
    ----------
    node: :class:`~wavelink.Node`
        The node that has connected or reconnected.
    resumed: bool
        Whether this node was successfully resumed.
    session_id: str
        The session ID associated with this node.
    """

    def __init__(self, node: Node, resumed: bool, session_id: str) -> None:
        self.node = node
        self.resumed = resumed
        self.session_id = session_id


class TrackStartEventPayload:
    """Payload received in the :func:`on_wavelink_track_start` event.

    Attributes
    ----------
    player: :class:`~wavelink.Player` | None
        The player associated with this event. Could be None.
    track: :class:`~wavelink.Playable`
        The track received from Lavalink regarding this event.
    original: :class:`~wavelink.Playable` | None
        The original track associated this event. E.g. the track that was passed to :meth:`~wavelink.Player.play` or
        inserted into the queue, with all your additional attributes assigned. Could be ``None``.
    """

    def __init__(self, player: Player | None, track: Playable) -> None:
        self.player = player
        self.track = track
        self.original: Playable | None = None

        if player:
            self.original = player._original


class TrackEndEventPayload:
    """Payload received in the :func:`on_wavelink_track_end` event.

    Attributes
    ----------
    player: :class:`~wavelink.Player` | None
        The player associated with this event. Could be None.
    track: :class:`~wavelink.Playable`
        The track received from Lavalink regarding this event.
    reason: str
        The reason Lavalink ended this track.
    original: :class:`~wavelink.Playable` | None
        The original track associated this event. E.g. the track that was passed to :meth:`~wavelink.Player.play` or
        inserted into the queue, with all your additional attributes assigned. Could be ``None``.
    """

    def __init__(self, player: Player | None, track: Playable, reason: str) -> None:
        self.player = player
        self.track = track
        self.reason = reason
        self.original: Playable | None = None

        if player:
            self.original = player._previous


class TrackExceptionEventPayload:
    """Payload received in the :func:`on_wavelink_track_exception` event.

    Attributes
    ----------
    player: :class:`~wavelink.Player` | None
        The player associated with this event. Could be None.
    track: :class:`~wavelink.Playable`
        The track received from Lavalink regarding this event.
    exception: TrackExceptionPayload
        The exception data received via Lavalink.
    """

    def __init__(self, player: Player | None, track: Playable, exception: TrackExceptionPayload) -> None:
        self.player = cast(wavelink.Player, player)
        self.track = track
        self.exception = exception


class TrackStuckEventPayload:
    """Payload received in the :func:`on_wavelink_track_stuck` event.

    Attributes
    ----------
    player: :class:`~wavelink.Player` | None
        The player associated with this event. Could be None.
    track: :class:`~wavelink.Playable`
        The track received from Lavalink regarding this event.
    threshold: int
        The Lavalink threshold associated with this event.
    """

    def __init__(self, player: Player | None, track: Playable, threshold: int) -> None:
        self.player = cast(wavelink.Player, player)
        self.track = track
        self.threshold = threshold


class WebsocketClosedEventPayload:
    """Payload received in the :func:`on_wavelink_websocket_closed` event.

    Attributes
    ----------
    player: :class:`~wavelink.Player` | None
        The player associated with this event. Could be None.
    code: :class:`wavelink.DiscordVoiceCloseType`
        The close code enum value.
    reason: str
        The reason the websocket was closed.
    by_remote: bool
        ``True`` if discord closed the websocket. ``False`` otherwise.
    """

    def __init__(self, player: Player | None, code: int, reason: str, by_remote: bool) -> None:
        self.player = player
        self.code: DiscordVoiceCloseType = DiscordVoiceCloseType(code)
        self.reason = reason
        self.by_remote = by_remote


class PlayerUpdateEventPayload:
    """Payload received in the :func:`on_wavelink_player_update` event.

    Attributes
    ----------
    player: :class:`~wavelink.Player` | None
        The player associated with this event. Could be None.
    time: int
        Unix timestamp in milliseconds, when this event fired.
    position: int
        The position of the currently playing track in milliseconds.
    connected: bool
        Whether Lavalink is connected to the voice gateway.
    ping: int
        The ping of the node to the Discord voice server in milliseconds (-1 if not connected).
    """

    def __init__(self, player: Player | None, state: PlayerState) -> None:
        self.player = cast(wavelink.Player, player)
        self.time: int = state["time"]
        self.position: int = state["position"]
        self.connected: bool = state["connected"]
        self.ping: int = state["ping"]


class StatsEventMemory:
    """Represents Memory Stats.

    Attributes
    ----------
    free: int
        The amount of free memory in bytes.
    used: int
        The amount of used memory in bytes.
    allocated: int
        The amount of allocated memory in bytes.
    reservable: int
        The amount of reservable memory in bytes.
    """

    def __init__(self, data: MemoryStats) -> None:
        self.free: int = data["free"]
        self.used: int = data["used"]
        self.allocated: int = data["allocated"]
        self.reservable: int = data["reservable"]


class StatsEventCPU:
    """Represents CPU Stats.

    Attributes
    ----------
    cores: int
        The number of CPU cores available on the node.
    system_load: float
        The system load of the node.
    lavalink_load: float
        The load of Lavalink on the node.
    """

    def __init__(self, data: CPUStats) -> None:
        self.cores: int = data["cores"]
        self.system_load: float = data["systemLoad"]
        self.lavalink_load: float = data["lavalinkLoad"]


class StatsEventFrames:
    """Represents Frame Stats.

    Attributes
    ----------
    sent: int
        The amount of frames sent to Discord.
    nulled: int
        The amount of frames that were nulled.
    deficit: int
        The difference between sent frames and the expected amount of frames.
    """

    def __init__(self, data: FrameStats) -> None:
        self.sent: int = data["sent"]
        self.nulled: int = data["nulled"]
        self.deficit: int = data["deficit"]


class StatsEventPayload:
    """Payload received in the :func:`on_wavelink_stats_update` event.

    Attributes
    ----------
    players: int
        The amount of players connected to the node (Lavalink).
    playing: int
        The amount of players playing a track.
    uptime: int
        The uptime of the node in milliseconds.
    memory: :class:`wavelink.StatsEventMemory`
        See Also: :class:`wavelink.StatsEventMemory`
    cpu: :class:`wavelink.StatsEventCPU`
        See Also: :class:`wavelink.StatsEventCPU`
    frames: :class:`wavelink.StatsEventFrames`
        See Also: :class:`wavelink.StatsEventFrames`
    """

    def __init__(self, data: StatsOP) -> None:
        self.players: int = data["players"]
        self.playing: int = data["playingPlayers"]
        self.uptime: int = data["uptime"]

        self.memory: StatsEventMemory = StatsEventMemory(data=data["memory"])
        self.cpu: StatsEventCPU = StatsEventCPU(data=data["cpu"])
        self.frames: StatsEventFrames | None = None

        if data["frameStats"]:
            self.frames = StatsEventFrames(data=data["frameStats"])
