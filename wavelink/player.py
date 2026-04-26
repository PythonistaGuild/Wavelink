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

from typing import TYPE_CHECKING

from ._lib import VoiceProtocol
from .node import MusicBot
from .utils import MISSING, VoiceUpdateCondition


if TYPE_CHECKING:
    from ._lib import Client, Connectable, Guild, GuildVoiceStatePayload, VoiceServerUpdatePayload
    from .node import Node
    from .types_.rest import UpdatePlayerReqT
    from .types_.websocket import WebSocketClosedEventT


class Player(VoiceProtocol):
    def __init__(self, client: Client, channel: Connectable, *, node: Node | None = None) -> None:
        super().__init__(client, channel)

        node = node or self._get_node()
        if not node:
            # TODO: Exception...
            raise

        self._node: Node = node

        self._guild: Guild | None = None
        self._guild_id: int | None = None

        self._condition = VoiceUpdateCondition()

    def _get_node(self) -> Node | None:
        if isinstance(self.client, MusicBot):
            return self.client.get_node()

        pool = getattr(self.client, "pool", None)
        if not pool:
            return

        try:
            return pool.get_node()
        except Exception:
            pass

    async def _node_close(self, data: WebSocketClosedEventT) -> ...:
        # by_discord = data["byRemote"]
        # code = data["code"]
        ...

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
            # TODO: ...
            ...

        original = self._condition.channelId
        self._condition.channelId = channel_id
        self._condition.sessionId = data["session_id"]

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
        reconnect: bool,
        self_deaf: bool = False,
        self_mute: bool = False,
    ) -> None:
        if self.channel is MISSING:
            raise

        if not self._guild:
            self._guild = self.channel.guild

        assert self._guild is not None
        await self._guild.change_voice_state(channel=self.channel, self_mute=self_mute, self_deaf=self_deaf)

    async def play(self, track: ...) -> None:
        await self._node.update_player(self._guild_id, data={"track": {"encoded": track.encoded}})
