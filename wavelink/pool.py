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

from __future__ import annotations

import json
import logging
import os
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
)

import aiohttp
import discord
from discord.enums import try_enum

from . import abc
from .enums import *
from .errors import *
from .stats import Stats
from .utils import MISSING
from .websocket import Websocket

if TYPE_CHECKING:
    from .player import Player
    from .ext import spotify


__all__ = (
    "Node",
    "NodePool",
)


PT = TypeVar("PT", bound=abc.Playable)
PLT = TypeVar("PLT", bound=abc.Playlist)


logger: logging.Logger = logging.getLogger(__name__)


class Node:
    """WaveLink Node object.

    Attributes
    ----------
    bot: :class:`discord.Client`
        The discord.py Bot object.


    .. warning::
        This class should not be created manually. Please use :meth:`NodePool.create_node()` instead.
    """

    def __init__(
        self,
        bot: discord.Client,
        host: str,
        port: int,
        password: str,
        https: bool,
        heartbeat: float,
        region: Optional[discord.VoiceRegion],
        spotify: Optional[spotify.SpotifyClient],
        identifier: str,
        dumps: Callable[[Any], str],
        resume_key: Optional[str],
    ):
        self.bot: discord.Client = bot
        self._host: str = host
        self._port: int = port
        self._password: str = password
        self._https: bool = https
        self._heartbeat: float = heartbeat
        self._region: Optional[discord.VoiceRegion] = region
        self._spotify = spotify
        self._identifier: str = identifier

        self._players: List[Player] = []

        self._dumps: Callable[[Any], str] = dumps
        self._websocket: Websocket = MISSING

        self.stats: Optional[Stats] = None

        self.resume_key = resume_key or str(os.urandom(8).hex())

    def __repr__(self) -> str:
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
    def region(self) -> Optional[discord.VoiceRegion]:
        """The voice region of the Node."""
        return self._region

    @property
    def identifier(self) -> str:
        """The Nodes unique identifier."""
        return self._identifier

    @property
    def players(self) -> List[Player]:
        """A list of currently connected Players."""
        return self._players

    @property
    def penalty(self) -> float:
        """The load-balancing penalty for this node."""
        if self.stats is None:
            return 9e30

        return self.stats.penalty.total

    def is_connected(self) -> bool:
        """Bool indicating whether or not this Node is currently connected to Lavalink."""
        if self._websocket is MISSING:
            return False

        return self._websocket.is_connected()

    async def _connect(self) -> None:
        self._websocket = Websocket(node=self)

        await self._websocket.connect()

    async def _get_data(
        self, endpoint: str, params: dict
    ) -> Tuple[Dict[str, Any], aiohttp.ClientResponse]:
        headers = {"Authorization": self._password}
        async with self._websocket.session.get(
            f"{self._websocket.host}/{endpoint}", headers=headers, params=params
        ) as resp:
            data = await resp.json()

        return data, resp

    async def get_tracks(self, cls: Type[PT], query: str) -> List[PT]:
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

        load_type = try_enum(LoadType, data.get("loadType"))

        if load_type is LoadType.load_failed:
            raise LoadTrackError(data)

        if load_type is LoadType.no_matches:
            return []

        if load_type is LoadType.track_loaded:
            track_data = data["tracks"][0]
            return [cls(track_data["track"], track_data["info"])]

        if load_type is not LoadType.search_result:
            raise LavalinkException("Track failed to load.")

        return [
            cls(track_data["track"], track_data["info"])
            for track_data in data["tracks"]
        ]

    async def get_playlist(self, cls: Type[PLT], identifier: str) -> Optional[PLT]:
        """|coro|

        Search for and return a :class:`abc.Playlist` given an identifier.

        Parameters
        ----------
        cls: Type[:class:`abc.Playlist`]
            The type of which playlist should be returned, this must subclass :class:`abc.Playlist`.
        identifier: str
            The playlist's identifier. This may be a YouTube playlist URL for example.

        Returns
        -------
        Optional[:class:`abc.Playlist`]:
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

        load_type = try_enum(LoadType, data.get("loadType"))

        if load_type is LoadType.load_failed:
            raise LoadTrackError(data)

        if load_type is LoadType.no_matches:
            return None

        if load_type is not LoadType.playlist_loaded:
            raise LavalinkException("Track failed to load.")

        return cls(data)

    async def build_track(self, cls: Type[PT], identifier: str) -> PT:
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

    def get_player(self, guild: discord.Guild) -> Optional[Player]:
        """Returns a :class:`Player` object playing in a specific :class:`discord.Guild`.

        Parameters
        ----------
        guild: :class:`discord.Guild`
            The Guild the player is in.

        Returns
        -------
        Optional[:class:`Player`]
        """
        for player in self.players:
            if player.guild == guild:
                return player

        return None

    async def disconnect(self, *, force: bool = False) -> None:
        """Disconnect this Node and remove it from the NodePool.

        This is a graceful shutdown of the node.
        """
        for player in self.players:
            await player.disconnect(force=force)

        await self.cleanup()

    async def cleanup(self) -> None:
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

    _nodes: ClassVar[Dict[str, Node]] = {}

    @property
    def nodes(self) -> Dict[str, Node]:
        """A mapping of created Node objects."""
        return self._nodes

    @classmethod
    async def create_node(
        cls,
        *,
        bot: discord.Client,
        host: str,
        port: int,
        password: str,
        https: bool = False,
        heartbeat: float = 30,
        region: Optional[discord.VoiceRegion] = None,
        spotify_client: Optional[spotify.SpotifyClient] = None,
        identifier: str = MISSING,
        dumps: Callable[[Any], str] = json.dumps,
        resume_key: Optional[str] = None,
    ) -> Node:

        """|coro|

        Classmethod that creates a :class:`Node` object and stores it for use with WaveLink.

        Parameters
        ----------
        bot: Union[:class:`discord.Client`]
            The discord.py Bot or Client class.
        host: :class:`str`
            The lavalink host address.
        port: :class:`int`
            The lavalink port.
        password: :class:`str`
            The lavalink password for authentication.
        https: :class:`bool`
            Connect to lavalink over https. Defaults to False.
        heartbeat: :class:`float`
            The heartbeat in seconds for the node. Defaults to 30 seconds.
        region: Optional[:class:`discord.VoiceRegion`]
            The discord.py VoiceRegion to assign to the node. This is useful for node region balancing.
        spotify_client: Optional[:class:`wavelink.ext.spotify.SpotifyClient`]
            An optional SpotifyClient with credentials to use when searching for spotify tracks.
        identifier: :class:`str`
            The unique identifier for this Node. By default this will be generated for you.

        Returns
        -------
        :class:`Node`
            The WaveLink Node object.
        """

        if identifier is MISSING:
            identifier = os.urandom(8).hex()

        if identifier in cls._nodes:
            raise NodeOccupied(
                f"A node with identifier <{identifier}> already exists in this pool."
            )

        node = Node(
            bot=bot,
            host=host,
            port=port,
            password=password,
            https=https,
            heartbeat=heartbeat,
            region=region,
            spotify=spotify_client,
            identifier=identifier,
            dumps=dumps,
            resume_key=resume_key
        )

        cls._nodes[identifier] = node
        await node._connect()

        return node

    @classmethod
    def get_node(
        cls, *, identifier: str = MISSING, region: discord.VoiceRegion = MISSING
    ) -> Node:
        """Retrieve a Node from the NodePool.

        Parameters
        ------------
        identifier: :class:`str`
            If provided this method will attempt to return the Node with the provided identifier.
        region: :class:`discord.VoiceRegion`
            If provided this method will attempt to find the best Node with the provided region.

        Returns
        --------
        :class:`Node`
            The WaveLink Node object.

        Raises
        --------
        :class:`ZeroConnectedNodes`
            There are no currently connected Nodes on the pool with the provided options.
        :class:`NoMatchingNode`
            No Node exists with the provided identifier.
        """
        if not cls._nodes:
            raise ZeroConnectedNodes("There are no connected Nodes on this pool.")

        if identifier is not MISSING:
            try:
                node = cls._nodes[identifier]
            except KeyError:
                raise NoMatchingNode(f"No Node with identifier <{identifier}> exists.")
            else:
                return node

        elif region is not MISSING:
            nodes = [n for n in cls._nodes.values() if n._region is region]
            if not nodes:
                raise ZeroConnectedNodes(
                    f"No Nodes for region <{region}> exist on this pool."
                )
        else:
            nodes = cls._nodes.values()

        return sorted(nodes, key=lambda n: len(n.players))[0]
