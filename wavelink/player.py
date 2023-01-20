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
from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING, Any, Union

import discord
from discord.utils import MISSING

from .enums import *
from .node import Node, NodePool
from .queue import Queue
from .tracks import *

if TYPE_CHECKING:
    from discord.types.voice import GuildVoiceState, VoiceServerUpdate
    from typing_extensions import Self

    from .types.events import PlayerState, PlayerUpdateOp
    from .types.request import EncodedTrackRequest, Request
    from .types.state import DiscordVoiceState

__all__ = ("Player",)


logger: logging.Logger = logging.getLogger(__name__)


VoiceChannel = Union[
    discord.VoiceChannel, discord.StageChannel
]  # todo: VocalGuildChannel?


class Player(discord.VoiceProtocol):

    def __call__(self, client: discord.Client, channel: VoiceChannel) -> Self:
        self.client = client
        self.channel = channel

        return self

    def __init__(
        self,
        client: discord.Client = MISSING,
        channel: VoiceChannel = MISSING,
        *,
        nodes: list[Node] | None = None,
        swap_node_on_disconnect: bool = True
    ) -> None:
        self.client: discord.Client = client
        self.channel: VoiceChannel | None = channel

        self.nodes: list[Node]
        self.current_node: Node

        if swap_node_on_disconnect and not nodes:
            self.nodes = list(NodePool.nodes.values())
            self.current_node = self.nodes[0]
        elif nodes:
            self.current_node = nodes[0]
            self.nodes = nodes
        else:
            self.current_node = NodePool.get_connected_node()
            self.nodes = [self.current_node]

        if not self.client:
            if self.current_node.client is None:
                raise RuntimeError('')
            self.client = self.current_node.client

        self._guild: discord.Guild | None = None
        self._voice_state: DiscordVoiceState = {}
        self._player_state: dict[str, Any] = {}

        self.swap_on_disconnect: bool = swap_node_on_disconnect

        self.last_update: datetime.datetime | None = None
        self.last_position: int = 0

        self._ping: int = 0

        self.queue: Queue = Queue()
        self._current: Playable | None = None

    @property
    def guild(self) -> discord.Guild | None:
        """The discord Guild associated with the Player."""
        return self._guild

    @property
    def position(self) -> int:
        """The position of the currently playing track in milliseconds."""
        # TODO - player is playing logic

        delta = (datetime.datetime.now(datetime.timezone.utc) - self.last_update).total_seconds() * 1000
        position = self.last_position + delta

        # TODO - min(position, duration)
        return position

    @property
    def ping(self) -> int:
        """The ping to the discord endpoint in milliseconds."""
        return self._ping

    @property
    def current(self) -> Playable | None:
        return self._current

    async def _update_event(self, data: PlayerUpdateOp | None) -> None:
        assert self._guild is not None

        if data is None: 
            if self.swap_on_disconnect:

                if len(self.nodes) < 2:
                    return

                new: Node = [n for n in self.nodes if n != self.current_node and n.status is NodeStatus.CONNECTED][0]
                del self.current_node._players[self._guild.id]

                if not new:
                    return

                self.current_node: Node = new
                new._players[self._guild.id] = self

                await self._dispatch_voice_update()
                await self._swap_state()
            return

        data.pop('op')  # type: ignore
        self._player_state.update(**data)

        state: PlayerState = data['state']
        self.last_update = datetime.datetime.fromtimestamp(state.get("time", 0) / 1000, datetime.timezone.utc)
        self.last_position = state.get('position', 0)

        self._ping = state['ping']

    async def on_voice_server_update(self, data: VoiceServerUpdate) -> None:
        self._voice_state['token'] = data['token']
        self._voice_state['endpoint'] = data['endpoint']

        await self._dispatch_voice_update()

    async def on_voice_state_update(self, data: GuildVoiceState) -> None:
        assert self._guild is not None

        channel_id = data["channel_id"]

        if not channel_id:
            self._voice_state = MISSING
            del self.current_node._players[self._guild.id]

            self.channel = None
            self._guild = None

            return

        self._voice_state['session_id'] = data['session_id']
        self.channel = self.client.get_channel(int(channel_id))  # type: ignore

        if not self._guild:
            self._guild = self.channel.guild  # type: ignore
            assert self._guild is not None
            self.current_node._players[self._guild.id] = self

        await self._dispatch_voice_update()

    async def _dispatch_voice_update(self, data: DiscordVoiceState | None = None) -> None:
        assert self._guild is not None

        data = data or self._voice_state

        try:
            session_id: str = data['session_id']
            token: str = data['token']
            endpoint: str = data['endpoint']
        except KeyError:
            return

        voice: Request = {'voice': {'sessionId': session_id, 'token': token, 'endpoint': endpoint}}
        self._player_state.update(**voice)

        resp: dict[str, Any] = await self.current_node._send(method='PATCH',
                                                             path=f'sessions/{self.current_node._session_id}/players',
                                                             guild_id=self._guild.id,
                                                             data=voice)

        print(f'DISPATCH VOICE_UPDATE: {resp}')

    async def connect(self, *, timeout: float, reconnect: bool, **kwargs: Any) -> None:
        if self.channel is None:
            raise RuntimeError('')

        if not self._guild:
            self._guild = self.channel.guild
            self.current_node._players[self._guild.id] = self

        await self.channel.guild.change_voice_state(channel=self.channel, **kwargs)

    async def play(self, track: Playable) -> dict[str, Any]:
        assert self._guild is not None

        resp: dict[str, Any] = await self.current_node._send(method='PATCH',
                                                             path=f'sessions/{self.current_node._session_id}/players',
                                                             guild_id=self._guild.id,
                                                             data={'encodedTrack': track.encoded})

        self._player_state['track'] = resp['track']['encoded']
        self._current = track

        print(f'PLAY: {resp}')
        return resp

    async def stop(self) -> dict[str, Any]:
        """
        This seems to currently be broken on the lavalink side
        """
        assert self._guild is not None

        resp: dict[str, Any] = await self.current_node._send(method='PATCH',
                                                             path=f'sessions/{self.current_node._session_id}/players',
                                                             guild_id=self._guild.id,
                                                             data={'encodedTrack': None})

        self._player_state['track'] = None

        print(f'STOP: {resp}')
        return resp

    async def destroy(self) -> None:
        assert self._guild is not None

        await self.current_node._send(method='DELETE',
                                     path=f'sessions/{self.current_node._session_id}/players',
                                     guild_id=self._guild.id)

    async def _swap_state(self) -> None:
        assert self._guild is not None

        print(f'SWAP STATE: {self._player_state}')

        try:
            self._player_state['track']
        except KeyError:
            return

        data: EncodedTrackRequest = {'encodedTrack': self._player_state['track'], 'position': self.position}
        resp: dict[str, Any] = await self.current_node._send(method='PATCH',
                                                             path=f'sessions/{self.current_node._session_id}/players',
                                                             guild_id=self._guild.id,
                                                             data=data)

        print(f'SWAP STATE RESP: {resp}')
