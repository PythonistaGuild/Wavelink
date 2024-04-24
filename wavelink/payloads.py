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

import datetime
from typing import TYPE_CHECKING, cast

import wavelink

from .enums import DiscordVoiceCloseType
from .filters import Filters
from .tracks import Playable


if TYPE_CHECKING:
    from .node import Node
    from .player import Player
    from .types.filters import *
    from .types.response import *
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
    "StatsResponsePayload",
    "GitResponsePayload",
    "VersionResponsePayload",
    "PluginResponsePayload",
    "InfoResponsePayload",
    "PlayerStatePayload",
    "VoiceStatePayload",
    "PlayerResponsePayload",
    "ExtraEventPayload",
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
    frames: :class:`wavelink.StatsEventFrames` | None
        See Also: :class:`wavelink.StatsEventFrames`. This could be ``None``.
    """

    def __init__(self, data: StatsOP) -> None:
        self.players: int = data["players"]
        self.playing: int = data["playingPlayers"]
        self.uptime: int = data["uptime"]

        self.memory: StatsEventMemory = StatsEventMemory(data=data["memory"])
        self.cpu: StatsEventCPU = StatsEventCPU(data=data["cpu"])
        self.frames: StatsEventFrames | None = None

        if frames := data.get("frameStats", None):
            self.frames = StatsEventFrames(frames)


class StatsResponsePayload:
    """Payload received when using :meth:`~wavelink.Node.fetch_stats`

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
    frames: :class:`wavelink.StatsEventFrames` | None
        See Also: :class:`wavelink.StatsEventFrames`. This could be ``None``.
    """

    def __init__(self, data: StatsResponse) -> None:
        self.players: int = data["players"]
        self.playing: int = data["playingPlayers"]
        self.uptime: int = data["uptime"]

        self.memory: StatsEventMemory = StatsEventMemory(data=data["memory"])
        self.cpu: StatsEventCPU = StatsEventCPU(data=data["cpu"])
        self.frames: StatsEventFrames | None = None

        if frames := data.get("frameStats", None):
            self.frames = StatsEventFrames(frames)


class PlayerStatePayload:
    """Represents the PlayerState information received via :meth:`~wavelink.Node.fetch_player_info` or
    :meth:`~wavelink.Node.fetch_players`

    Attributes
    ----------
    time: int
        Unix timestamp in milliseconds received from Lavalink.
    position: int
        The position of the track in milliseconds received from Lavalink.
    connected: bool
        Whether Lavalink is connected to the voice gateway.
    ping: int
        The ping of the node to the Discord voice server in milliseconds (-1 if not connected).
    """

    def __init__(self, data: PlayerState) -> None:
        self.time: int = data["time"]
        self.position: int = data["position"]
        self.connected: bool = data["connected"]
        self.ping: int = data["ping"]


class VoiceStatePayload:
    """Represents the VoiceState information received via :meth:`~wavelink.Node.fetch_player_info` or
    :meth:`~wavelink.Node.fetch_players`. This is the voice state information received via Discord and sent to your
    Lavalink node.

    Attributes
    ----------
    token: str | None
        The Discord voice token authenticated with. This is not the same as your bots token. Could be ``None``.
    endpoint: str | None
        The Discord voice endpoint connected to. Could be ``None``.
    session_id: str | None
        The Discord voice session ID autheticated with. Could be ``None``.
    """

    def __init__(self, data: VoiceStateResponse) -> None:
        self.token: str | None = data.get("token")
        self.endpoint: str | None = data.get("endpoint")
        self.session_id: str | None = data.get("sessionId")


class PlayerResponsePayload:
    """Payload received when using :meth:`~wavelink.Node.fetch_player_info` or :meth:`~wavelink.Node.fetch_players`

    Attributes
    ----------
    guild_id: int
        The guild ID as an int that this player is connected to.
    track: :class:`wavelink.Playable` | None
        The current track playing on Lavalink. Could be ``None`` if no track is playing.
    volume: int
        The current volume of the player.
    paused: bool
        A bool indicating whether the player is paused.
    state: :class:`wavelink.PlayerStatePayload`
        The current state of the player. See: :class:`wavelink.PlayerStatePayload`.
    voice_state: :class:`wavelink.VoiceStatePayload`
        The voice state infomration received via Discord and sent to Lavalink. See: :class:`wavelink.VoiceStatePayload`.
    filters: :class:`wavelink.Filters`
        The :class:`wavelink.Filters` currently associated with this player.
    """

    def __init__(self, data: PlayerResponse) -> None:
        self.guild_id: int = int(data["guildId"])
        self.track: Playable | None = None

        if track := data.get("track"):
            self.track = Playable(track)

        self.volume: int = data["volume"]
        self.paused: bool = data["paused"]
        self.state: PlayerStatePayload = PlayerStatePayload(data["state"])
        self.voice_state: VoiceStatePayload = VoiceStatePayload(data["voice"])
        self.filters: Filters = Filters(data=data["filters"])


class GitResponsePayload:
    """Represents Git information received via :meth:`wavelink.Node.fetch_info`

    Attributes
    ----------
    branch: str
        The branch this Lavalink server was built on.
    commit: str
        The commit this Lavalink server was built on.
    commit_time: :class:`datetime.datetime`
        The timestamp for when the commit was created.
    """

    def __init__(self, data: GitPayload) -> None:
        self.branch: str = data["branch"]
        self.commit: str = data["commit"]
        self.commit_time: datetime.datetime = datetime.datetime.fromtimestamp(
            data["commitTime"] / 1000, tz=datetime.timezone.utc
        )


class VersionResponsePayload:
    """Represents Version information received via :meth:`wavelink.Node.fetch_info`

    Attributes
    ----------
    semver: str
        The full version string of this Lavalink server.
    major: int
        The major version of this Lavalink server.
    minor: int
        The minor version of this Lavalink server.
    patch: int
        The patch version of this Lavalink server.
    pre_release: str
        The pre-release version according to semver as a ``.`` separated list of identifiers.
    build: str | None
        The build metadata according to semver as a ``.`` separated list of identifiers. Could be ``None``.
    """

    def __init__(self, data: VersionPayload) -> None:
        self.semver: str = data["semver"]
        self.major: int = data["major"]
        self.minor: int = data["minor"]
        self.patch: int = data["patch"]
        self.pre_release: str | None = data.get("preRelease")
        self.build: str | None = data.get("build")


class PluginResponsePayload:
    """Represents Plugin information received via :meth:`wavelink.Node.fetch_info`

    Attributes
    ----------
    name: str
        The plugin name.
    version: str
        The plugin version.
    """

    def __init__(self, data: PluginPayload) -> None:
        self.name: str = data["name"]
        self.version: str = data["version"]


class InfoResponsePayload:
    """Payload received when using :meth:`~wavelink.Node.fetch_info`

    Attributes
    ----------
    version: :class:`VersionResponsePayload`
        The version info payload for this Lavalink node in the :class:`VersionResponsePayload` object.
    build_time: :class:`datetime.datetime`
        The timestamp when this Lavalink jar was built.
    git: :class:`GitResponsePayload`
        The git info payload for this Lavalink node in the :class:`GitResponsePayload` object.
    jvm: str
        The JVM version this Lavalink node runs on.
    lavaplayer: str
        The Lavaplayer version being used by this Lavalink node.
    source_managers: list[str]
        The enabled source managers for this node.
    filters: list[str]
        The enabled filters for this node.
    plugins: list[:class:`PluginResponsePayload`]
        The enabled plugins for this node.
    """

    def __init__(self, data: InfoResponse) -> None:
        self.version: VersionResponsePayload = VersionResponsePayload(data["version"])
        self.build_time: datetime.datetime = datetime.datetime.fromtimestamp(
            data["buildTime"] / 1000, tz=datetime.timezone.utc
        )
        self.git: GitResponsePayload = GitResponsePayload(data["git"])
        self.jvm: str = data["jvm"]
        self.lavaplayer: str = data["lavaplayer"]
        self.source_managers: list[str] = data["sourceManagers"]
        self.filters: list[str] = data["filters"]
        self.plugins: list[PluginResponsePayload] = [PluginResponsePayload(p) for p in data["plugins"]]


class ExtraEventPayload:
    """Payload received in the :func:`on_wavelink_extra_event` event.

    This payload is created when an ``Unknown`` and ``Unhandled`` event is received from Lavalink, most likely via
    a plugin.

    .. note::

        See the appropriate documentation of the plugin for the data sent with these events.


    Attributes
    ----------
    node: :class:`~wavelink.Node`
        The node that the event pertains to.
    player: :class:`~wavelink.Player` | None
        The player associated with this event. Could be None.
    data: dict[str, Any]
        The raw data sent from Lavalink for this event.


    .. versionadded:: 3.1.0
    """

    def __init__(self, *, node: Node, player: Player | None, data: dict[str, Any]) -> None:
        self.node = node
        self.player = player
        self.data = data
