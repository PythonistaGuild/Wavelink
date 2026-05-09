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

import datetime
from functools import wraps
from typing import TYPE_CHECKING, Any, Concatenate, ParamSpec, Self, TypeVar

import wavelink

from ._lib import VoiceProtocol
from .exceptions import InvalidPlayerState, InvalidTrackError, NodeNotFound
from .queue import Queue
from .tracks import Search, Track
from .utils import MISSING, VoiceUpdateCondition


if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from ._lib import Client, Connectable, Guild, GuildVoiceStatePayload, VoiceChannel, VoiceServerUpdatePayload
    from .node import Node
    from .types_.rest import UpdatePlayerReqT
    from .types_.websocket import PlayerStateT, WebSocketClosedEventT


P = ParamSpec("P")
R = TypeVar("R")


def has_channel[**P, R](func: Callable[Concatenate[Any, P], Awaitable[R]]) -> Callable[Concatenate[Any, P], Awaitable[R]]:
    @wraps(func)
    async def wrapper(self: Any, *args: P.args, **kwargs: P.kwargs) -> R:
        if not self._guild or not self.channel:
            raise InvalidPlayerState("Unable to update player. No connected Voice Channel.")

        return await func(self, *args, **kwargs)

    return wrapper


class Player(VoiceProtocol):
    channel: VoiceChannel

    def __init__(self, client: Client, channel: Connectable, /, *, node: Node | None = None) -> None:
        super().__init__(client, channel)

        node = node or self._get_node()
        if not node:
            raise NodeNotFound(f"No Node was provided or could be found and used for {self!r}.")

        # Passing the Client to Node is optional; since we get Client here we can take advantage of this to set
        # Client if it was never originally set...
        if not node._client and client.application_id == node._client_id:
            node._client = client

        self._node: Node = node
        self._guild: Guild | None = None
        self._guild_id: int | None = None

        self._condition = VoiceUpdateCondition()
        self._should_reconnect = MISSING

        self._volume: int = 100
        self._is_playing: bool = False
        self._is_paused: bool = False
        self._is_deaf: bool = False
        self._is_mute: bool = False
        self._lava_connected: bool = False
        self._ping: int = -1
        self._position: int = 0
        self._last_update: int | None = 0

        self.queue: Queue = Queue()

    def __repr__(self) -> str:
        return f"Player(guild={self._guild}, channel={self.channel})"

    @classmethod
    def factory(cls, client: Client, channel: Connectable, *args: Any, **kwargs: Any) -> Self:
        # NOTE: Allows customizing the player when passed to Channel.connect(cls=...)
        return cls(client, channel, *args, **kwargs)

    @property
    def node(self) -> Node:
        return self._node

    @property
    def guild(self) -> Guild | None:
        return self._guild

    @property
    def volume(self) -> int:
        return self._volume

    @property
    def ping(self) -> int:
        return self._ping

    @property
    def position(self) -> int:
        return self._position

    @property
    def last_update(self) -> datetime.datetime | None:
        return datetime.datetime.fromtimestamp(self._last_update) if self._last_update else None

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    @property
    def is_paused(self) -> bool:
        return self._is_paused

    @property
    def is_deaf(self) -> bool:
        return self._is_deaf

    @property
    def is_mute(self) -> bool:
        return self._is_mute

    def _get_node(self) -> Node | None:
        if isinstance(self.client, wavelink.MusicBot):
            return self.client.get_node()

        pool = getattr(self.client, "pool", None)
        if not pool:
            return

        try:
            return pool.get_node()
        except Exception:
            pass

    async def _node_close(self, data: WebSocketClosedEventT) -> None: ...

    def _lavalink_update(self, data: PlayerStateT) -> None:
        self._lava_connected = data["connected"]
        self._ping = data["ping"]
        self._position = data["position"]
        self._last_update = data["time"]

    async def on_voice_server_update(self, data: VoiceServerUpdatePayload) -> None:
        endpoint = data["endpoint"]
        if not endpoint:
            return

        guild_id = int(data.get("guild_id", 0))
        guild = self.client.get_guild(guild_id)
        self._guild_id = guild_id

        if guild:
            self._guild = guild

        self._condition.endpoint = endpoint
        self._condition.token = data["token"]

        await self._dispatch_voice()

    async def on_voice_state_update(self, data: GuildVoiceStatePayload) -> None:
        channel_id = str(data["channel_id"]) if data["channel_id"] else None

        if not channel_id:
            return await self.destroy()

        if self._guild:
            self.channel = self._guild.get_channel(int(channel_id))  # type: ignore

        original = self._condition.channelId
        self._condition.channelId = channel_id
        self._condition.sessionId = data["session_id"]

        self._is_deaf = data["self_deaf"]
        self._is_mute = data["self_mute"]

        if original != channel_id:
            await self._dispatch_voice()

    async def _dispatch_voice(self) -> None:
        if self._condition.waiting:
            return

        await self._condition.wait()
        assert self._guild_id

        data: UpdatePlayerReqT = {"voice": self._condition.as_dict()}
        await self._node.update_player(self._guild_id, data=data)

    async def connect(
        self,
        *,
        timeout: float = 10.0,
        reconnect: bool = True,
        self_deaf: bool = False,
        self_mute: bool = False,
    ) -> None:
        if self.channel is MISSING:
            raise InvalidPlayerState(f"No valid channel could be found to connect for {self!r}.")

        if not self._guild:
            self._guild = self.channel.guild

        self._should_reconnect = reconnect
        async with self._condition.timeout(timeout):
            await self._guild.change_voice_state(channel=self.channel, self_mute=self_mute, self_deaf=self_deaf)

        self._node._players[self._guild.id] = self

    @has_channel
    async def disconnect(self, *, force: bool) -> None: ...  # type: ignore

    async def destroy(self) -> None: ...

    @has_channel
    async def play(
        self,
        track: Track | Search,
        *,
        volume: int | None = None,
        paused: bool | None = None,
        replace: bool = True,
    ) -> None:
        assert self._guild
        playable = track.first if isinstance(track, Search) else track

        if not playable:
            raise InvalidTrackError(
                f"Could not determine playable from {track}. Excpected {type(Track).__name__!r}, got {playable!r}."
            )

        data: UpdatePlayerReqT = {
            "endTime": playable.end,
            "position": playable.start,
            "track": {"encoded": playable.encoded},
        }

        if volume is not None:
            data["volume"] = volume
        if paused is not None:
            data["paused"] = paused

        await self._node.update_player(self._guild.id, data=data, no_replace=not replace)

    @has_channel
    async def search_play(
        self,
        search: str,
        *,
        volume: int | None = None,
        paused: bool | None = None,
        replace: bool = True,
    ) -> Track:
        assert self._guild

        result = await self._node.search(search)
        playable = result.first

        if not playable:
            raise InvalidTrackError(f"Could not find tracks for search {search!r}. {result} was empty.")

        data: UpdatePlayerReqT = {
            "endTime": playable.end,
            "position": playable.start,
            "track": {"encoded": playable.encoded},
        }

        if volume is not None:
            data["volume"] = volume
        if paused is not None:
            data["paused"] = paused

        await self._node.update_player(self._guild.id, data=data, no_replace=not replace)
        return playable

    @has_channel
    async def direct_play(
        self,
        *,
        identifier: str | None = None,
        encoded: str | None = None,
        volume: int | None = None,
        paused: bool | None = None,
        replace: bool = True,
    ) -> None:
        assert self._guild

        if not identifier and not encoded:
            raise ValueError("The 'identifier' and 'encoded' parameters are missing. One must be provided.")
        elif identifier and encoded:
            raise ValueError("Only one of 'indentifier' and 'encoded' can be provided.")

        data: UpdatePlayerReqT = {"track": {}}

        if encoded:
            data["track"]["encoded"] = encoded
        elif identifier:
            data["track"]["identifier"] = identifier

        if volume is not None:
            data["volume"] = volume
        if paused is not None:
            data["paused"] = paused

        await self._node.update_player(self._guild.id, data=data, no_replace=not replace)

    @has_channel
    async def pause(self) -> None:
        assert self._guild

        data: UpdatePlayerReqT = {"paused": True}
        await self._node.update_player(self._guild.id, data=data)
        self._is_paused = True

    @has_channel
    async def resume(self) -> None:
        assert self._guild

        data: UpdatePlayerReqT = {"paused": False}
        await self._node.update_player(self._guild.id, data=data)
        self._is_paused = False

    @has_channel
    async def toggle_pause(self) -> None:
        assert self._guild

        paused = not self._is_paused
        data: UpdatePlayerReqT = {"paused": paused}

        await self._node.update_player(self._guild.id, data=data)
        self._is_paused = paused

    @has_channel
    async def skip(self) -> ...: ...

    @has_channel
    async def stop(self) -> ...: ...

    @has_channel
    async def set_volume(self, volume: int = 100, /) -> int:
        assert self._guild

        if not 0 <= volume <= 1000:
            raise ValueError(f"'volume' parameter must be an integer between 1 and 1000. Got {volume}.")

        data: UpdatePlayerReqT = {"volume": volume}
        old = self._volume

        await self._node.update_player(self._guild.id, data=data)
        self._volume = volume

        return old

    @has_channel
    async def mute(self) -> None:
        assert self._guild and self.channel
        if self._is_mute:
            return

        await self._guild.change_voice_state(channel=self.channel, self_mute=True, self_deaf=self._is_deaf)

    @has_channel
    async def deafen(self) -> None:
        assert self._guild and self.channel
        if self._is_deaf:
            return

        await self._guild.change_voice_state(channel=self.channel, self_deaf=True, self_mute=self._is_mute)

    @has_channel
    async def move(
        self,
        channel: VoiceChannel,
        *,
        timeout: float = 10.0,
        self_deaf: bool | None = None,
        self_mute: bool | None = None,
    ) -> None:
        assert self._guild
        if self.channel.id == channel.id:
            return

        async with self._condition.timeout(timeout):
            await self._guild.change_voice_state(
                channel=channel,
                self_mute=self_mute or self._is_mute,
                self_deaf=self_deaf or self._is_deaf,
            )

        self._node._players[self._guild.id] = self
