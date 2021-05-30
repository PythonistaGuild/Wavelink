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

import json
import logging
import uuid
from typing import Optional, Union

import discord
from discord.ext import commands

from .enums import *
from .errors import *
from .websocket import Websocket


logger = logging.getLogger(__name__)


class Node:
    """WaveLink Node object.

    Attributes
    ----------
    bot: :class:`~commands.Bot`
        The discord.py Bot object.


    .. warning::
        This class should not be created manually. Please use :meth:`NodePool.create_node()` instead.
    """
    def __init__(self, **attrs):
        self.bot = attrs.get("bot")
        self._host: str = attrs.get("host")
        self._port: int = attrs.get("port")
        self._password: str = attrs.get("password")
        self._https: bool = attrs.get("https")
        self._heartbeat: float = attrs.get("heartbeat")
        self._region: discord.VoiceRegion = attrs.get("region")
        self._identifier: str = attrs.get("identifier")

        self._players = []

        self._dumps = attrs.get("dumps")
        self._websocket: Websocket = None

        self.stats = None

    def __repr__(self):
        return f"<WaveLink Node: <{self.identifier}>, Region: <{self.region}>, Players: <{len(self._players)}>>"

    @property
    def host(self) -> str:
        """The host this node is connected to."""
        return self._host

    @property
    def port(self) -> int:
        """The port this node is connected to."""
        return self._port

    @property
    def region(self) -> discord.VoiceRegion:
        """The voice region of the Node."""
        return self._region

    @property
    def identifier(self) -> str:
        """The Nodes unique identifier."""
        return self._identifier

    @property
    def players(self) -> list:
        """A list of currently connected Players."""
        return self._players

    @property
    def penalty(self) -> float:
        """The load-balancing penalty for this node."""
        if self.stats is None:
            return 9e30

        return self.stats.penalty.total

    def is_connected(self):
        """Bool indicating whether or not this Node is currently connected to Lavalink."""
        if self._websocket is None:
            return False

        return self._websocket.is_connected()

    async def _connect(self):
        self._websocket = Websocket(node=self)

        await self._websocket.connect()

    async def _get_data(self, endpoint: str, params: dict):
        headers = {"Authorization": self._password}
        async with self._websocket.session.get(
            f"{self._websocket.host}/{endpoint}", headers=headers, params=params
        ) as resp:
            data = await resp.json()

        return data, resp

    async def get_tracks(self, cls, query: str):
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
        data, resp = await self._get_data("loadtracks", {"identifier": query})

        if resp.status != 200:
            raise LavalinkException("Invalid response from Lavalink server.")

        load_type = LoadType.try_value(data.get("loadType"))

        if load_type == LoadType.load_failed:
            raise LoadTrackError(data)

        if load_type == LoadType.no_matches:
            return []

        if load_type == LoadType.track_loaded:
            track_data = data["tracks"][0]
            return [cls(track_data["track"], track_data["info"])]

        if load_type != LoadType.search_result:
            raise LavalinkException("Track failed to load.")

        tracks = []
        for track_data in data["tracks"]:
            track = cls(track_data["track"], track_data["info"])
            tracks.append(track)

        return tracks

    async def get_playlist(self, cls, identifier: str):
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
        data, resp = await self._get_data("loadtracks", {"identifier": identifier})

        if resp.status != 200:
            raise LavalinkException("Invalid response from Lavalink server.")

        load_type = LoadType.try_value(data.get("loadType"))

        if load_type == LoadType.load_failed:
            raise LoadTrackError(data)

        if load_type == LoadType.no_matches:
            return None

        if load_type != LoadType.playlist_loaded:
            raise LavalinkException("Track failed to load.")

        return cls(data)

    async def build_track(self, cls, identifier: str):
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
        data, resp = await self._get_data("decodetrack", {"track": identifier})

        if resp.status != 200:
            raise BuildTrackError(data)

        return cls(identifier, data)

    def get_player(self, guild: discord.Guild):
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
        """Disconnect this Node and remove it from the NodePool.

        This is a graceful shutdown of the node.
        """
        for player in self.players:
            await player.disconnect(force=force)

        await self.cleanup()

    async def cleanup(self):
        try:
            self._websocket.listener.cancel()
        except Exception:
            pass

        try:
            await self._websocket.session.close()
        except Exception:
            pass

        del NodePool._nodes[self._identifier]


class NodePool:
    """Wavelink NodePool class.

    This class holds all the Node objects created with :meth:`create_node()`.
    """

    _nodes = {}

    @property
    def nodes(self) -> dict:
        """A mapping of created Node objects."""
        return self._nodes

    @classmethod
    async def create_node(
        cls,
        *,
        bot: Union[discord.Client, commands.Bot],
        host: str,
        port: int,
        password: str,
        https: Optional[bool] = False,
        heartbeat: Optional[float] = 30,
        region: Optional[discord.VoiceRegion] = None,
        identifier: Optional[str] = None,
        dumps=json.dumps,
    ) -> Node:

        """|coro|

        Classmethod that creates a :class:`Node` object and stores it for use with WaveLink.

        Parameters
        ----------
        bot: Union[discord.Client, commands.Bot]
            The discord.py Bot or Client class.
        host: str
            The lavalink host address.
        port: int
            The lavalink port.
        password: str
            The lavalink password for authentication.
        https: Optional[bool]
            Connect to lavalink over https. Defaults to False.
        heartbeat: Optional[float]
            The heartbeat in seconds for the node. Defaults to 30 seconds.
        region: Optional[discord.VoiceRegion]
            The discord.py VoiceRegion to assign to the node. This is useful for node region balancing.
        identifier: Optional[str]
            The unique identifier for this Node. By default this will be generated for you.

        Returns
        -------
        Node
            The WaveLink Node object.
        """

        if not identifier:
            identifier = str(uuid.uuid4())

        if identifier in cls._nodes:
            raise NodeOccupied(f"A node with identifier <{identifier}> already exists in this pool.")

        node = Node(
            bot=bot,
            host=host,
            port=port,
            password=password,
            https=https,
            heartbeat=heartbeat,
            region=region,
            identifier=identifier,
            dumps=dumps,
        )

        cls._nodes[identifier] = node
        await node._connect()

        return node

    @classmethod
    def get_node(cls, *, identifier: str = None, region: discord.VoiceRegion = None) -> Node:
        """Retrieve a Node from the NodePool.

        Parameters
        ------------
        identifier: Optional[str]
            If provided this method will attempt to return the Node with the provided identifier.
        region: Optional[:class:`discord.VoiceRegion`]
            If provided this method will attempt to find the best Node with the provided region.

        Returns
        --------
        Node
            The WaveLink Node object.

        Raises
        --------
        ZeroConnectedNodes
            There are no currently connected Nodes on the pool with the provided options.
        NoMatchingNode
            No Node exists with the provided identifier.
        """
        if not cls._nodes:
            raise ZeroConnectedNodes("There are no connected Nodes on this pool.")

        if identifier:
            try:
                node = cls._nodes[identifier]
            except KeyError:
                raise NoMatchingNode(f"No Node with identifier <{identifier}> exists.")
            else:
                return node

        elif region:
            nodes = [n for n in cls._nodes.values() if n._region is region]
            if not nodes:
                raise ZeroConnectedNodes(f"No Nodes for region <{region}> exist on this pool.")
        else:
            nodes = cls._nodes.values()

        return sorted(nodes, key=lambda n: len(n.players))[0]
