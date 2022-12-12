"""MIT License

Copyright (c) 2019-2021 PythonistaGuild

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

import contextlib
import datetime
import logging
from typing import Any, Dict, Union, Optional

import discord
from discord.channel import VoiceChannel

from . import abc
from .pool import Node, NodePool
from .queue import WaitQueue
from .tracks import PartialTrack
from .utils import MISSING
from .filters import Filter


__all__ = ("Player",)


logger: logging.Logger = logging.getLogger(__name__)


VoiceChannel = Union[
    discord.VoiceChannel, discord.StageChannel
]  # todo: VocalGuildChannel?


class Player(discord.VoiceProtocol):
    """WaveLink Player object.

    This class subclasses :class:`discord.VoiceProtocol` and such should be treated as one with additions.

    Examples
    --------

        .. code::

            @commands.command()
            async def connect(self, channel: discord.VoiceChannel):

                voice_client = await channel.connect(cls=wavelink.Player)


    .. warning::
        This class should not be created manually but can be subclassed to add additional functionality.
        You should instead use :meth:`discord.VoiceChannel.connect()` and pass the player object to the cls kwarg.
    """

    def __call__(self, client: discord.Client, channel: VoiceChannel):
        self.client: discord.Client = client
        self.channel: VoiceChannel = channel

        return self

    def __init__(
        self,
        client: discord.Client = MISSING,
        channel: VoiceChannel = MISSING,
        *,
        node: Node = MISSING,
    ):
        self.client: discord.Client = client
        self.channel: VoiceChannel = channel

        if node is MISSING:
            node = NodePool.get_node()
        self.node: Node = node
        self.node._players.append(self)

        self._voice_state: Dict[str, Any] = {}

        self.last_update: datetime.datetime = MISSING
        self.last_position: float = MISSING

        self._connected: bool = False
        self._paused: bool = False

        self._volume: int = 100
        self._source: Optional[abc.Playable] = None
        self._filter: Optional[Filter] = None

        self.queue = WaitQueue()

    @property
    def guild(self) -> discord.Guild:
        """The :class:`discord.Guild` this :class:`Player` is in."""
        return self.channel.guild

    @property
    def user(self) -> discord.ClientUser:
        """The :class:`discord.ClientUser` of the :class:`discord.Client`"""
        return self.client.user  # type: ignore

    @property
    def volume(self) -> int:
        return self._volume

    @property
    def source(self) -> Optional[abc.Playable]:
        """The currently playing audio source."""
        return self._source

    @property
    def filter(self) -> Optional[Filter]:
        return self._filter

    track = source

    @property
    def position(self) -> float:
        """The current seek position of the playing source in seconds. If nothing is playing this defaults to ``0``."""
        if not self.is_playing():
            return 0

        if self.is_paused():
            return min(self.last_position, self.source.duration)  # type: ignore

        delta = (
            datetime.datetime.now(datetime.timezone.utc) - self.last_update
        ).total_seconds()
        position = round(self.last_position + delta, 1)

        return min(position, self.source.duration)  # type: ignore

    async def update_state(self, state: Dict[str, Any]) -> None:
        state = state["state"]

        self.last_update = datetime.datetime.fromtimestamp(
            state.get("time", 0) / 1000, datetime.timezone.utc
        )
        self.last_position = round(state.get("position", 0) / 1000, 1)

    async def on_voice_server_update(self, data: Dict[str, Any]) -> None:
        self._voice_state.update({"event": data})

        await self._dispatch_voice_update(self._voice_state)

    async def on_voice_state_update(self, data: Dict[str, Any]) -> None:
        self._voice_state.update({"sessionId": data["session_id"]})

        channel_id = data["channel_id"]
        if not channel_id:  # We're disconnecting
            self._voice_state.clear()
            return

        self.channel = self.guild.get_channel(int(channel_id))  # type: ignore
        await self._dispatch_voice_update({**self._voice_state, "event": data})

    async def _dispatch_voice_update(self, voice_state: Dict[str, Any]) -> None:
        logger.debug(f"Dispatching voice update:: {self.channel.id}")

        if {"sessionId", "event"} == self._voice_state.keys():
            await self.node._websocket.send(
                op="voiceUpdate", guildId=str(self.guild.id), **voice_state
            )

    async def connect(self, *, timeout: float, reconnect: bool, **kwargs: Any) -> None:
        await self.guild.change_voice_state(channel=self.channel, **kwargs)
        self._connected = True

        logger.info(f"Connected to voice channel:: {self.channel.id}")

    async def disconnect(self, *, force: bool = False) -> None:
        try:
            logger.info(f"Disconnected from voice channel:: {self.channel.id}")

            await self.guild.change_voice_state(channel=None)
            self._connected = False
        finally:
            with contextlib.suppress(ValueError):
                self.node._players.remove(self)

            payload = {"op": "destroy", "guildId": str(self.guild.id)}
            await self.node._websocket.send(**payload)

            self.cleanup()

    async def move_to(self, channel: discord.VoiceChannel) -> None:
        """|coro|

        Moves the player to a different voice channel.

        Parameters
        -----------
        channel: :class:`discord.VoiceChannel`
            The channel to move to. Must be a voice channel.
        """
        await self.guild.change_voice_state(channel=channel)
        logger.info(f"Moving to voice channel:: {channel.id}")

    async def play(
        self,
        source: abc.Playable,
        replace: bool = True,
        start: Optional[int] = None,
        end: Optional[int] = None,
        volume: Optional[int] = None,
        pause: Optional[bool] = None,
    ):
        """|coro|

        Play a WaveLink Track.

        Parameters
        ----------
        source: :class:`abc.Playable`
            The :class:`abc.Playable` track to start playing.
        replace: bool
            Whether this track should replace the current track. Defaults to ``True``.
        start: Optional[int]
            The position to start the track at in milliseconds.
            Defaults to ``None`` which will start the track at the beginning.
        end: Optional[int]
            The position to end the track at in milliseconds.
            Defaults to ``None`` which means it will play until the end.
        volume: Optional[int]
            Sets the volume of the player. Must be between ``0`` and ``1000``.
            Defaults to ``None`` which will not change the volume.
        pause: bool
            Changes the players pause state. Defaults to ``None`` which will not change the pause state.

        Returns
        -------
        :class:`wavelink.abc.Playable`
            The track that is now playing.
        """

        if not replace and self.is_playing():
            return

        await self.update_state({"state": {}})

        if isinstance(source, PartialTrack):
            source = await source._search()

        self._source = source

        payload = {
            "op": "play",
            "guildId": str(self.guild.id),
            "track": source.id,
            "noReplace": not replace,
        }
        if start is not None and start > 0:
            payload["startTime"] = str(start)
        if end is not None and end > 0:
            payload["endTime"] = str(end)
        if volume is not None:
            self._volume = volume
            payload["volume"] = str(volume)
        if pause is not None:
            self._paused = pause
            payload["pause"] = pause

        await self.node._websocket.send(**payload)

        logger.debug(f"Started playing track:: {str(source)} ({self.channel.id})")
        return source

    def is_connected(self) -> bool:
        """Indicates whether the player is connected to voice."""
        return self._connected

    def is_playing(self) -> bool:
        """Indicates whether a track is currently being played."""
        return self.is_connected() and self._source is not None

    def is_paused(self) -> bool:
        """Indicates whether the currently playing track is paused."""
        return self._paused

    async def stop(self) -> None:
        """|coro|

        Stop the Player's currently playing song.
        """
        await self.node._websocket.send(op="stop", guildId=str(self.guild.id))
        logger.debug(f"Current track stopped:: {str(self.source)} ({self.channel.id})")
        self._source = None

    async def set_pause(self, pause: bool) -> None:
        """|coro|

        Set the players paused state.

        Parameters
        ----------
        pause: bool
            A bool indicating if the player's paused state should be set to True or False.
        """
        await self.node._websocket.send(
            op="pause", guildId=str(self.guild.id), pause=pause
        )
        self._paused = pause
        logger.info(f"Set pause:: {self._paused} ({self.channel.id})")

    async def pause(self) -> None:
        """|coro|

        Pauses the player if it was playing.
        """
        await self.set_pause(True)

    async def resume(self) -> None:
        """|coro|

        Resumes the player if it was paused.
        """
        await self.set_pause(False)

    async def set_volume(self, volume: int) -> None:
        """|coro|

        Sets the player's volume. Accepts an int between ``0`` and ``1000`` where ``100`` means 100% volume.

        Parameters
        ----------
        volume: int
            The volume to set the player to.
        """

        self._volume = max(min(volume, 1000), 0)

        await self.node._websocket.send(
            op="volume",
            guildId=str(self.guild.id),
            volume=self.volume
        )
        logger.debug(f"Set volume:: {self.volume} ({self.channel.id})")

    async def seek(self, position: int = 0) -> None:
        """|coro|

        Seek to the given position in the song.

        Parameters
        ----------
        position: int
            The position as an int in milliseconds to seek to.
        """
        await self.node._websocket.send(
            op="seek", guildId=str(self.guild.id), position=position
        )

    async def set_filter(
        self,
        _filter: Filter,
        /, *,
        seek: bool = False
    ) -> None:
        """|coro|

        Set the player's filter.

        Parameters
        ----------
        filter: :class:`wavelink.Filter`
            The filter to apply to the player.
        seek: bool
            Whether to seek the player to its current position
            which will apply the filter immediately. Defaults to ``False``.
        """

        self._filter = _filter

        await self.node._websocket.send(
            op="filters",
            guildId=str(self.guild.id),
            **_filter._payload
        )
        logger.debug(f"Set filter:: {self._filter} ({self.channel.id})")

        if self.is_playing() and seek:
            await self.seek(int(self.position * 1000))
