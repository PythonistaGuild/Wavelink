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
from typing import Any, DefaultDict, Dict, Generator, List, Optional, Tuple, Type, TypeVar, TYPE_CHECKING

import aiohttp
import discord

from .enums import LoadType
from .errors import BuildTrackError, LoadTrackError, WavelinkException
from .playable import Playable, Track, Playlist
from .websocket import WebSocket

if TYPE_CHECKING:
    from .player import Player
    from .stats import Stats


T = TypeVar('T', bound=Playable)
U = TypeVar('U', bound=Playlist)


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

    async def _get_data(self, endpoint: str, params: Dict[str, str]) -> Tuple[Dict[str, Any], aiohttp.ClientResponse]:
        headers = {'Authorization': self.password}
        async with self._session.get(f'{self.rest_uri}/{endpoint}', headers=headers, params=params) as resp:
            data = await resp.json()

        return data, resp

    async def get_tracks(self, query: str, cls: Type[T] = Track) -> List[T]:  # type: ignore
        data, _ = await self._get_data('loadtracks', {'identifier': query})
        load_type = LoadType.try_value(data['loadType'])

        if load_type == LoadType.load_failed:
            raise LoadTrackError(data)

        if load_type == LoadType.no_matches:
            return []

        if load_type == LoadType.track_loaded:
            track_data = data['tracks'][0]
            return [cls(track_data['track'], track_data['info'])]

        if load_type != LoadType.search_result:
            raise WavelinkException

        tracks = []
        for track_data in data['tracks']:
            track = cls(track_data['track'], track_data['info'])
            tracks.append(track)

        return tracks

    async def get_track(self, identifier: str, cls: Type[T] = Track) -> Optional[T]:  # type: ignore
        data, _ = await self._get_data('loadtracks', {'identifier': identifier})
        load_type = LoadType.try_value(data['loadType'])

        if load_type == LoadType.load_failed:
            raise LoadTrackError(data)

        if load_type == LoadType.no_matches:
            return None

        if load_type != LoadType.track_loaded:
            raise WavelinkException

        track_data = data['tracks'][0]
        return cls(track_data['track'], track_data['info'])

    async def get_playlist(self, identifier: str, cls: Type[U] = Playlist) -> Optional[U]:  # type: ignore
        data, _ = await self._get_data('loadtracks', {'identifier': identifier})
        load_type = LoadType.try_value(data['loadType'])

        if load_type == LoadType.load_failed:
            raise LoadTrackError(data)

        if load_type == LoadType.no_matches:
            return None

        if load_type != LoadType.playlist_loaded:
            raise WavelinkException

        return cls(data)

    async def build_track(self, identifier: str, cls: Type[T] = Track) -> T:  # type: ignore
        data, resp = await self._get_data('decodetrack', {'track': identifier})

        if resp.status != 200:
            raise BuildTrackError(data)

        return cls(identifier, data)

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
