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

import logging
from typing import TYPE_CHECKING, Any, Union

import discord
from discord.utils import MISSING

from .exceptions import InvalidChannelStateException
from .node import Pool

if TYPE_CHECKING:
    from discord.types.voice import GuildVoiceState as GuildVoiceStatePayload
    from discord.types.voice import \
        VoiceServerUpdate as VoiceServerUpdatePayload
    from typing_extensions import Self

    from .node import Node
    from .types.request import Request as RequestPayload
    from .types.response import PlayerResponse
    from .types.state import PlayerVoiceState, VoiceState


logger: logging.Logger = logging.getLogger(__name__)


VoiceChannel = Union[discord.VoiceChannel, discord.StageChannel]


class Player(discord.VoiceProtocol):
    """

    Attributes
    ----------
    client: discord.Client
        The :class:`discord.Client` associated with this :class:`Player`.
    channel: discord.abc.Connectable | None
        The currently connected :class:`discord.VoiceChannel`.
        Could be None if this :class:`Player` has not been connected or has previously been disconnected.

    """

    def __call__(self, client: discord.Client, channel: VoiceChannel) -> Self:
        self.client = client
        self.channel = channel
        self._guild = channel.guild

        return self

    def __init__(
        self, client: discord.Client = MISSING, channel: VoiceChannel = MISSING, *, nodes: list[Node] | None = None
    ) -> None:
        self.client: discord.Client = client
        self.channel: VoiceChannel = channel
        self._guild: discord.Guild | None = None

        self._voice_state: PlayerVoiceState = {"voice": {}}

        self._node: Node
        if not nodes:
            self._node = Pool.get_node()
        else:
            self._node = sorted(nodes, key=lambda n: len(n.players))[0]

        if self.client is MISSING and self.node.client:
            self.client = self.node.client

        super().__init__(client=self.client, channel=self.channel)

    @property
    def node(self) -> Node:
        """The :class:`Player`'s currently selected :class:`Node`.


        ..versionchanged:: 3.0.0
            This property was previously known as ``current_node``.
        """
        return self._node

    @property
    def guild(self) -> discord.Guild | None:
        """Returns the :class:`Player`'s associated :class:`discord.Guild`.

        Could be None if this :class:`Player` has not been connected.
        """
        return self._guild

    async def on_voice_state_update(self, data: GuildVoiceStatePayload, /) -> None:
        channel_id = data["channel_id"]

        if not channel_id:
            await self._destroy()
            return

        self._voice_state["voice"]["session_id"] = data["session_id"]
        self.channel = self.client.get_channel(int(channel_id))  # type: ignore

    async def on_voice_server_update(self, data: VoiceServerUpdatePayload, /) -> None:
        self._voice_state["voice"]["token"] = data["token"]
        self._voice_state["voice"]["endpoint"] = data["endpoint"]

        await self._dispatch_voice_update()

    async def _dispatch_voice_update(self) -> None:
        assert self.guild is not None
        data: VoiceState = self._voice_state["voice"]

        try:
            session_id: str = data["session_id"]
            token: str = data["token"]
        except KeyError:
            return

        endpoint: str | None = data.get("endpoint", None)
        if not endpoint:
            return

        request: RequestPayload = {"voice": {"sessionId": session_id, "token": token, "endpoint": endpoint}}
        resp: PlayerResponse = await self.node._update_player(self.guild.id, data=request)

        # warning: print
        print(f"RESPONSE WHEN UPDATING STATE: {resp}")

        logger.debug(f"Player {self.guild.id} is dispatching VOICE_UPDATE.")

    async def connect(
        self, *, timeout: float, reconnect: bool, self_deaf: bool = False, self_mute: bool = False
    ) -> None:
        if self.channel is None:
            msg: str = 'Please use "discord.VoiceChannel.connect(cls=...)" and pass this Player to cls.'
            raise InvalidChannelStateException(f"Player tried to connect without a valid channel: {msg}")

        if not self._guild:
            self._guild = self.channel.guild
            self.node._players[self._guild.id] = self

        assert self.guild is not None
        await self.guild.change_voice_state(channel=self.channel, self_mute=self_mute, self_deaf=self_deaf)

        # warning: print
        print(f"PLAYER CONNECTED TO GUILD {self.guild.id} ON CHANNEL {self.channel}")

    async def play(self, ytid: str) -> None:
        """Test play command."""
        assert self.guild is not None

        request: RequestPayload = {"identifier": ytid, "volume": 20}
        resp: PlayerResponse = await self.node._update_player(self.guild.id, data=request)

        # warning: print
        print(f"PLAYER STARTED PLAYING: {resp}")

    async def disconnect(self, **kwargs: Any) -> None:
        ...

    async def _destroy(self) -> None:
        ...

    def cleanup(self) -> None:
        ...
