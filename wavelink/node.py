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

import wavelink.abc
from .enums import LoadType
from .errors import BuildTrackError, LoadTrackError, NodeOccupied, LavalinkException
from .websocket import WebSocket

if TYPE_CHECKING:
    from .player import Player
    from .stats import Stats


T = TypeVar('T', bound=wavelink.abc.Playable)
U = TypeVar('U', bound=wavelink.abc.Playlist)
V = TypeVar('V', bound=wavelink.abc.Searchable)


class Node:
    """Represents a WaveLink Node.

    .. warning::
        You should not create :class:`Node` objects manually.
        Instead you should use the :func:`Node.create` helper method.

    Attributes
    ----------
    client: :class:`~discord.Client`
        The discord client attached to this node.
    identifier: str
        The unique identifier associated with the node.
    host: str
        The host address the node is connected to.
    port: int
        The port the node is connected to.
    rest_uri: str
        The rest server address the node is connected to.
    region: :class:`~discord.VoiceRegion`
        The discord voice region provided to the node on connection.
    players: List[:class:`Player`]
        The list of players attached to this node.
    """
    _all_nodes: DefaultDict[discord.Client, List[Node]] = defaultdict(list)
    _session: aiohttp.ClientSession = None  # type: ignore

    def __init__(self, client: discord.Client, identifier: str, host: str, port: int, rest_uri: str, password: str,
                 region: discord.VoiceRegion, secure: bool = False, shard_id: int = None, heartbeat: float = None):
        self.client = client
        self.identifier = identifier

        node = Node.get_node(client, identifier)
        if node is not None:
            raise NodeOccupied(f'Node with identifier ({identifier}) already exists >> {node.__repr__()}')

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

    def is_available(self) -> bool:
        """Indicates whether the node is currently available."""
        return self.websocket.is_connected() and self._available

    def close(self):
        """Closes the node and makes it unavailable."""
        self._available = False

    def open(self):
        """Opens the node and makes it available."""
        self._available = True

    @property
    def penalty(self) -> float:
        """The load-balancing penalty for this node."""
        if not self.is_available() or self.stats is None:
            return 9e30

        return self.stats.penalty.total

    async def connect(self):
        self.websocket = websocket = WebSocket(self, self.host, self.port, self.password, self.secure)
        await websocket.connect()

    async def _get_data(self, endpoint: str, params: Dict[str, str]) -> Tuple[Dict[str, Any], aiohttp.ClientResponse]:
        headers = {'Authorization': self.password}
        async with self._session.get(f'{self.rest_uri}/{endpoint}', headers=headers, params=params) as resp:
            data = await resp.json()

        return data, resp

    async def get_track(self, cls: Type[T], identifier: str) -> Optional[T]:
        """|coro|

        Search for an return a :class:`abc.Playable` given an identifier.

        Parameters
        ----------
        cls: Type[:class:`abc.Playable`]
            The type of which track should be returned, this must subclass :class:`abc.Playable`.
        identifier: str
            The track's identifier. This may be a URL to a file or YouTube video for example.

        Returns
        -------
        Union[:class:`abc.Playable`, ``None``]:
            The related wavelink track object or ``None`` if none was found.

        Raises
        ------
        LoadTrackError
            Loading the track failed.
        LavalinkException
            An unspecified error occurred when loading the track.
        """
        data, resp = await self._get_data('loadtracks', {'identifier': identifier})

        if resp.status != 200:
            raise LavalinkException('Invalid response from Lavalink server.')

        load_type = LoadType.try_value(data.get('loadType'))

        if load_type == LoadType.load_failed:
            raise LoadTrackError(data)

        if load_type == LoadType.no_matches:
            return None

        if load_type != LoadType.track_loaded:
            raise LavalinkException('Track failed to load.')

        track_data = data['tracks'][0]
        return cls(track_data['track'], track_data['info'])

    async def get_playlist(self, cls: Type[U], identifier: str) -> Optional[U]:
        """|coro|

        Search for an return a :class:`abc.Playlist` given an identifier.

        Parameters
        ----------
        cls: Type[:class:`abc.Playlist`]
            The type of which playlist should be returned, this must subclass :class:`abc.Playlist`.
        identifier: str
            The playlist's identifier. This may be a YouTube playlist URL for example.

        Returns
        -------
        Union[:class:`abc.Playlist`, None]:
            The related wavelink track object or ``None`` if none was found.

        Raises
        ------
        LoadTrackError
            Loading the playlist failed.
        LavalinkException
            An unspecified error occurred when loading the playlist.
        """
        data, resp = await self._get_data('loadtracks', {'identifier': identifier})

        if resp.status != 200:
            raise LavalinkException('Invalid response from Lavalink server.')

        load_type = LoadType.try_value(data.get('loadType'))

        if load_type == LoadType.load_failed:
            raise LoadTrackError(data)

        if load_type == LoadType.no_matches:
            return None

        if load_type != LoadType.playlist_loaded:
            raise LavalinkException('Track failed to load.')

        return cls(data)

    async def get_tracks(self, cls: Type[V], query: str) -> List[V]:
        """|coro|

        Search for and return a list of :class:`abc.Playable` for a given query.

        Parameters
        ----------
        cls: Type[:class:`abc.Playable`]
            The type of which track should be returned, this must subclass :class:`abc.Playable`.
        query: str
            A query to use to search for tracks.

        Returns
        -------
        List[:class:`abc.Playable`]:
            A list of wavelink track objects.

        Raises
        ------
        LoadTrackError
            Loading the track failed.
        LavalinkException
            An unspecified error occurred when loading the track.
        """
        data, resp = await self._get_data('loadtracks', {'identifier': query})

        if resp.status != 200:
            raise LavalinkException('Invalid response from Lavalink server.')

        load_type = LoadType.try_value(data.get('loadType'))

        if load_type == LoadType.load_failed:
            raise LoadTrackError(data)

        if load_type == LoadType.no_matches:
            return []

        if load_type == LoadType.track_loaded:
            track_data = data['tracks'][0]
            return [cls(track_data['track'], track_data['info'])]

        if load_type != LoadType.search_result:
            raise LavalinkException('Track failed to load.')

        tracks = []
        for track_data in data['tracks']:
            track = cls(track_data['track'], track_data['info'])
            tracks.append(track)

        return tracks

    async def build_track(self, cls: Type[T], identifier: str) -> T:
        """|coro|

        Build a track object with a valid track identifier.

        Parameters
        ------------
        cls: Type[:class:`abc.Playable`]
            The type of which track should be returned, this must subclass :class:`abc.Playable`.
        identifier: str
            The tracks unique Base64 encoded identifier. This is usually retrieved from various lavalink events.

        Returns
        ---------
        :class:`abc.Playable`
            The track built from a Base64 identifier.

        Raises
        --------
        BuildTrackError
            Decoding and building the track failed.
        """
        data, resp = await self._get_data('decodetrack', {'track': identifier})

        if resp.status != 200:
            raise BuildTrackError(data)

        return cls(identifier, data)

    def get_player(self, guild: discord.Guild) -> Optional[Player]:
        """Returns a :class:`Player` object playing in a specific :class:`~discord.Guild`.

        Parameters
        ----------
        guild: :class:`~discord.Guild`
            The Guild the player is in.

        Returns
        -------
        Optional[:class:`Player`]
        """
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
        """Returns all nodes attached to a given discord client.

        Parameters
        ----------
        client: :class:`~discord.Client`
            The discord client attached to the nodes.

        Returns
        -------
        List[:class:`Node`]
        """
        return cls._all_nodes[client]

    @classmethod
    def get_node(cls, client: discord.Client, identifier: str) -> Optional[Node]:
        """Returns the node attached to the given discord client with matching identifier.

        Parameters
        ----------
        client: :class:`~discord.Client`
            The discord client attached to the nodes.
        identifier: str
            The unique identifier for the node.

        Returns
        -------
        Optional[:class:`Node`]

        """
        for node in cls.get_nodes(client):
            if node.identifier == identifier:
                return node
        return None

    @classmethod
    async def create(cls, client: discord.Client, **kwargs) -> Node:
        """|coro|

        Create a new Wavelink Node.

        Parameters
        ----------

        client: :class:`~discord.Client`
            The discord client this :class:`Node` is attached to.
        identifier: str
            A unique identifier for the :class:`Node`.
        host: str
            The host address to connect to.
        port: int
            The port to connect to.
        rest_uri: str
            The URI to use to connect to the REST server.
        password: str
            The password to authenticate on the server.
        region: :class:`~discord.VoiceRegion`
            The discord voice region to associate the :class:`Node` with.
        shard_id: Optional[int]
            An optional Shard ID to associate with the :class:`Node`. Could be None.
        secure: bool
            Whether the websocket should be started with the secure wss protocol. Defaults to ``False``.
        heartbeat: Optional[float]
            Send ping message every heartbeat seconds and wait pong response, if pong response is not received then close connection.

        Returns
        -------
        :class:`Node`
            The newly created Wavelink node.

        Raises
        ------
        NodeOccupied
            A node with provided identifier already exists.

        """
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
        nodes: Optional[List[:class:`Node`]]
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
        """Returns the best available :class:`Node` usable by the :class:`~discord.Client`.

        Parameters
        ----------
        client: :class:`~discord.Client`
            The discord client which nodes are attached to.
        nodes: Optional[List[:class:`Node`]]
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
        Optional[:class:`Node`]
            The best available :class:`Node` usable by the :class:`~discord.Client`.

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
