"""
MIT License

Copyright (c) 2019-Present PythonistaGuild

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
import logging
from typing import Any, Union, TYPE_CHECKING

import discord

from .node import Node, NodePool


__all__ = ("Player",)


logger: logging.Logger = logging.getLogger(__name__)


VoiceChannel = Union[
    discord.VoiceChannel, discord.StageChannel
]  # todo: VocalGuildChannel?


class Player(discord.VoiceProtocol):

    def __call__(self, client: discord.Client, channel: VoiceChannel):
        self.client: discord.Client = client
        self.channel: VoiceChannel = channel

        return self

    def __init__(
        self,
        client: discord.Client | None = None,
        channel: VoiceChannel | None = None,
        *,
        node: Node = None,
    ):
        self.client: discord.Client | None = client
        self.channel: VoiceChannel | None = channel

        if node is None:
            node = NodePool.get_connected_node()

        self.node: Node = node
        if not self.client:
            self.client = self.node.client

        self._guild: discord.Guild | None = None
        self._voice_state: dict[str, Any] = {}

    async def on_voice_server_update(self, data: dict[str, Any]) -> None:
        self._voice_state['token'] = data['token']
        self._voice_state['endpoint'] = data['endpoint']

        await self._dispatch_voice_update()

    async def on_voice_state_update(self, data: dict[str, Any]) -> None:
        channel_id = data["channel_id"]

        if not channel_id:
            self._voice_state = {}
            del self.node._players[self._guild.id]

            self.channel = None
            self._guild = None

            return

        self._voice_state['session_id'] = data['session_id']
        self.channel: VoiceChannel = self.client.get_channel(int(channel_id))

        if not self._guild:
            self._guild = self.channel.guild
            self.node._players[self._guild.id] = self

        await self._dispatch_voice_update()

    async def _dispatch_voice_update(self) -> None:
        data = self._voice_state
        try:
            session_id: str = data['session_id']
            token: str = data['token']
            endpoint: str = data['endpoint']
        except KeyError:
            return

        voice: dict[str, dict[str, str]] = {'voice': {'sessionId': session_id, 'token': token, 'endpoint': endpoint}}
        resp: dict[str, Any] = await self.node._send(method='PATCH',
                                                     path=f'sessions/{self.node._session_id}/players',
                                                     guild_id=self._guild.id,
                                                     data=voice)

        print(f'DISPATCH VOICE_UPDATE: {resp}')

    async def connect(self, *, timeout: float, reconnect: bool, **kwargs: Any) -> None:
        if not self._guild:
            self._guild = self.channel.guild
            self.node._players[self._guild.id] = self

        await self.channel.guild.change_voice_state(channel=self.channel, **kwargs)

    async def play(self, id: str) -> None:
        resp: dict[str, Any] = await self.node._send(method='PATCH',
                                                     path=f'sessions/{self.node._session_id}/players',
                                                     guild_id=self._guild.id,
                                                     data={'identifier': id})

        print(f'PLAY: {resp}')





