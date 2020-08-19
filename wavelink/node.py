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
from __future__ import annotations

import asyncio

from collections import defaultdict
from typing import DefaultDict, Generator, List, Optional, TYPE_CHECKING, Union

import aiohttp
import discord

from .errors import BuildTrackError
from .track import Track, Playlist
from .websocket import WebSocket

if TYPE_CHECKING:
    from .player import Player
    from .stats import Stats


class Node:

    _all_nodes: DefaultDict[discord.Client, List[Node]] = defaultdict(list)
    _session: aiohttp.ClientSession = None  # type: ignore

    def __init__(self, client: discord.Client, identifier: str, host: str, port: int, rest_uri: str, password: str,
                 region: discord.VoiceRegion, secure: bool = False, shard_id: int = None, heartbeat: float = None):
        self.client = client
        self.identifier = identifier

        self.host = host
        self.port = port
        self.rest_uri = rest_uri
        self.password = password
        self.secure = secure

        self.region = region
        self.shard_id = shard_id
        self.heartbeat = heartbeat

        self.websocket: WebSocket = None  # type: ignore
        self.stats: Stats = None  # type: ignore
        self.players: List[Player] = []
        self._available = True

        self._all_nodes[client].append(self)

    def is_available(self):
        return self.websocket.is_connected() and self._available

    def close(self):
        self._available = False

    def open(self):
        self._available = True

    @property
    def penalty(self):
        if not self.available or self.stats is None:
            return float('inf')

        return self.stats.penalty.total

    async def connect(self):
        self.websocket = websocket = WebSocket(self, self.host, self.port, self.password, self.secure)
        await websocket.connect()

    async def get_tracks(self, query: str) -> Union[List[Track], Playlist]:
        headers = {'Authorization': self.password}
        async with self._session.get(f'{self.rest_uri}/loadtracks?identifier={query}', headers=headers) as resp:
            data = await resp.json()

        if data['playlistInfo']:
            return Playlist(data)

        tracks = []
        for track in data['tracks']:
            tracks.append(Track(track))

        return tracks

    async def build_track(self, identifier: str) -> Track:
        headers = {'Authorization': self.password}
        params = {'track': identifier}
        async with self._session.get(f'{self.rest_uri}/decodetrack?',
                                     headers=headers, params=params) as resp:
            data = await resp.json()

            if resp.status != 200:
                raise BuildTrackError

        return Track(data)

    def get_player(self, guild: discord.Guild) -> Optional[Player]:
        for player in self.players:
            if player.guild == guild:
                return player
        return None

    async def disconnect(self, *, force: bool = False):
        for player in self.players:
            await player.disconnect(force=force)
        self.cleanup()

    def cleanup(self):
        try:
            self.websocket.task.cancel()
        except Exception:
            pass

        self._all_nodes[self.client].remove(self)

    @classmethod
    def get_nodes(cls, client: discord.Client) -> List[Node]:
        return cls._all_nodes[client]

    @classmethod
    async def create(cls, client: discord.Client, **kwargs) -> Node:
        loop = client.loop or asyncio.get_event_loop()
        if cls._session is None or cls._session.closed:
            cls._session = aiohttp.ClientSession(loop=loop)

        node = cls(client, **kwargs)
        await node.connect()
        return node

    @classmethod
    def filter_nodes(cls, nodes: List[Node], *, region: discord.VoiceRegion = None,
                     shard_id: int = None, available: bool = True) -> Generator[Node, None, None]:
        """Filters a given list of nodes depending on parameters.

        Parameters
        ----------
        nodes: Optional[List[:class:`~wavelink.node.Node`]]
            The pool of nodes to filter.
        region: Optional[:class:`~discord.VoiceRegion`]
            The discord voice region the node should be set to.
        shard_id: Optional[int]
            The shard_id of the node.
        available: Optional[bool]
            Wether the node should be available or not. Defaults to ``True``.

        Returns
        -------
        The filtered list of nodes.
        """
        for node in nodes:
            if region is None or node.region == region:
                if shard_id is None or node.shard_id == shard_id:
                    if node.is_available() == available:
                        yield node

    @classmethod
    def get_best_node(cls, client: discord.Client, nodes: Optional[List[Node]] = None, *,
                      region: discord.VoiceRegion = None, shard_id: int = None,
                      guild: discord.Guild = None) -> Optional[Node]:
        """Returns the best available :class:`~wavelink.node.Node` usable by the :class:`~discord.Client`.

        Parameters
        ----------
        client: :class:`~discord.Client`
            The discord client which nodes are attached to.
        nodes: Optional[List[:class:`~wavelink.node.Node`]]
            The pool of nodes to select from. Defaults to all nodes attached to the client.
        region: Optional[:class:`~discord.VoiceRegion`]
            The discord voice region the node should be set to.
        shard_id: Optional[int]
            The shard_id of the node.
        guild: Optional[:class:`~discord.Guild`]
            A guild in which the node should be able to connect to.

            .. note::

                When this is passed ``region`` and ``shard_id`` cannot be set.

        Returns
        -------
        Optional[:class:`~wavelink.node.Node`]
            The best available :class:`~wavelink.node.Node` usable by the :class:`~discord.Client`.

        Raises
        ------
        TypeError
            The ``region`` or ``shard_id`` parameters were set when a ``guild`` was passed.
        """
        if nodes is None:
            nodes = cls._all_nodes[client]

        if guild is None:
            nodes = list(cls.filter_nodes(nodes, region=region, shard_id=shard_id))
            if not nodes:
                return None
            return sorted(nodes, key=lambda node: len(node.players))[0]

        if region is not None or shard_id is not None:
            raise TypeError('Cannot pass region or shard_id when a guild is specified.')

        return cls.get_best_node(client, nodes, region=guild.region, shard_id=guild.shard_id)\
            or cls.get_best_node(client, nodes, shard_id=guild.shard_id)
