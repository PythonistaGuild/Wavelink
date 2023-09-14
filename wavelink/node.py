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

import asyncio
import logging
import secrets
import urllib
from typing import TYPE_CHECKING, Iterable, Union, cast

import aiohttp
import discord
from discord.utils import classproperty

from . import __version__
from .enums import NodeStatus
from .exceptions import (
    AuthorizationFailedException,
    InvalidClientException,
    InvalidNodeException,
    LavalinkException,
    LavalinkLoadException,
    NodeException,
)
from .lfu import CapacityZero, LFUCache
from .tracks import Playable, Playlist
from .websocket import Websocket

if TYPE_CHECKING:
    from .player import Player
    from .types.request import Request, UpdateSessionRequest
    from .types.response import (
        EmptyLoadedResponse,
        ErrorLoadedResponse,
        ErrorResponse,
        InfoResponse,
        PlayerResponse,
        PlaylistLoadedResponse,
        SearchLoadedResponse,
        StatsResponse,
        TrackLoadedResponse,
        UpdateResponse,
    )
    from .types.tracks import TrackPayload

    LoadedResponse = Union[
        TrackLoadedResponse, SearchLoadedResponse, PlaylistLoadedResponse, EmptyLoadedResponse, ErrorLoadedResponse
    ]


__all__ = ("Node", "Pool")


logger: logging.Logger = logging.getLogger(__name__)


class Node:
    def __init__(
        self,
        *,
        identifier: str | None = None,
        uri: str,
        password: str,
        session: aiohttp.ClientSession | None = None,
        heartbeat: float = 15.0,
        retries: int | None = None,
        client: discord.Client | None = None,
    ) -> None:
        self._identifier = identifier or secrets.token_urlsafe(12)
        self._uri = uri.removesuffix("/")
        self._password = password
        self._session = session or aiohttp.ClientSession()
        self._heartbeat = heartbeat
        self._retries = retries
        self._client = client

        self._status: NodeStatus = NodeStatus.DISCONNECTED
        self._session_id: str | None = None

        self._players: dict[int, Player] = {}

        self._spotify_enabled: bool = False

        self._websocket: Websocket | None = None

    def __repr__(self) -> str:
        return f"Node(identifier={self.identifier}, uri={self.uri}, status={self.status}, players={len(self.players)})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Node):
            return NotImplemented

        return other.identifier == self.identifier

    def __del__(self) -> None:
        try:
            asyncio.get_running_loop()
            asyncio.create_task(self.close())
        except RuntimeError:
            pass

    @property
    def headers(self) -> dict[str, str]:
        assert self.client is not None
        assert self.client.user is not None

        data = {
            "Authorization": self.password,
            "User-Id": str(self.client.user.id),
            "Client-Name": f"Wavelink/{__version__}",
        }

        return data

    @property
    def identifier(self) -> str:
        """The unique identifier for this :class:`Node`.


        .. versionchanged:: 3.0.0
            This property was previously known as ``id``.
        """
        return self._identifier

    @property
    def uri(self) -> str:
        """The URI used to connect this :class:`Node` to Lavalink."""
        return self._uri

    @property
    def status(self) -> NodeStatus:
        """The current :class:`Node` status.

        Refer to: :class:`~wavelink.NodeStatus`
        """
        return self._status

    @property
    def players(self) -> dict[int, Player]:
        """A mapping of :attr:`discord.Guild.id` to :class:`~wavelink.Player`."""
        return self._players

    @property
    def client(self) -> discord.Client | None:
        """The :class:`discord.Client` associated with this :class:`Node`.

        Could be ``None`` if it has not been set yet.


        .. versionadded:: 3.0.0
        """
        return self._client

    @property
    def password(self) -> str:
        """The password used to connect this :class:`Node` to Lavalink.

        .. versionadded:: 3.0.0
        """
        return self._password

    @property
    def heartbeat(self) -> float:
        """The duration in seconds that the :class:`Node` websocket should send a heartbeat.

        .. versionadded:: 3.0.0
        """
        return self._heartbeat

    @property
    def session_id(self) -> str | None:
        """The Lavalink session ID. Could be None if this :class:`Node` has not connected yet.

        .. versionadded:: 3.0.0
        """
        return self._session_id

    async def close(self) -> None:
        if self._websocket is not None:
            await self._websocket.cleanup()
        else:
            self._status = NodeStatus.DISCONNECTED
            self._session_id = None
            self._players = {}

        try:
            await self._session.close()
        except:
            pass

        Pool._Pool__nodes.pop(self.identifier, None)  # type: ignore

    async def _connect(self, *, client: discord.Client | None) -> None:
        client_ = self._client or client

        if not client_:
            raise InvalidClientException(f"Unable to connect {self!r} as you have not provided a valid discord.Client.")

        self._client = client_

        websocket: Websocket = Websocket(node=self)
        self._websocket = websocket
        await websocket.connect()

        info: InfoResponse = await self._fetch_info()
        if "spotify" in info["sourceManagers"]:
            self._spotify_enabled = True

    async def _fetch_players(self) -> list[PlayerResponse]:
        uri: str = f"{self.uri}/v4/sessions/{self.session_id}/players"

        async with self._session.get(url=uri, headers=self.headers) as resp:
            if resp.status == 200:
                resp_data: list[PlayerResponse] = await resp.json()
                return resp_data

            else:
                exc_data: ErrorResponse = await resp.json()
                raise LavalinkException(data=exc_data)

    async def _fetch_player(self, guild_id: int, /) -> PlayerResponse:
        uri: str = f"{self.uri}/v4/sessions/{self.session_id}/players/{guild_id}"

        async with self._session.get(url=uri, headers=self.headers) as resp:
            if resp.status == 200:
                resp_data: PlayerResponse = await resp.json()
                return resp_data

            else:
                exc_data: ErrorResponse = await resp.json()
                raise LavalinkException(data=exc_data)

    async def _update_player(self, guild_id: int, /, *, data: Request, replace: bool = False) -> PlayerResponse:
        no_replace: bool = not replace

        uri: str = f"{self.uri}/v4/sessions/{self.session_id}/players/{guild_id}?noReplace={no_replace}"

        async with self._session.patch(url=uri, json=data, headers=self.headers) as resp:
            if resp.status == 200:
                resp_data: PlayerResponse = await resp.json()
                return resp_data

            else:
                exc_data: ErrorResponse = await resp.json()
                raise LavalinkException(data=exc_data)

    async def _destroy_player(self, guild_id: int, /) -> None:
        uri: str = f"{self.uri}/v4/sessions/{self.session_id}/players/{guild_id}"

        async with self._session.delete(url=uri, headers=self.headers) as resp:
            if resp.status == 204:
                return

            exc_data: ErrorResponse = await resp.json()
            raise LavalinkException(data=exc_data)

    async def _update_session(self, *, data: UpdateSessionRequest) -> UpdateResponse:
        uri: str = f"{self.uri}/v4/sessions/{self.session_id}"

        async with self._session.patch(url=uri, data=data) as resp:
            if resp.status == 200:
                resp_data: UpdateResponse = await resp.json()
                return resp_data

            else:
                exc_data: ErrorResponse = await resp.json()
                raise LavalinkException(data=exc_data)

    async def _fetch_tracks(self, query: str) -> LoadedResponse:
        uri: str = f"{self.uri}/v4/loadtracks?identifier={query}"

        async with self._session.get(url=uri, headers=self.headers) as resp:
            if resp.status == 200:
                resp_data: LoadedResponse = await resp.json()
                return resp_data

            else:
                exc_data: ErrorResponse = await resp.json()
                raise LavalinkException(data=exc_data)

    async def _decode_track(self) -> TrackPayload:
        ...

    async def _decode_tracks(self) -> list[TrackPayload]:
        ...

    async def _fetch_info(self) -> InfoResponse:
        uri: str = f"{self.uri}/v4/info"

        async with self._session.get(url=uri, headers=self.headers) as resp:
            if resp.status == 200:
                resp_data: InfoResponse = await resp.json()
                return resp_data

            else:
                exc_data: ErrorResponse = await resp.json()
                raise LavalinkException(data=exc_data)

    async def _fetch_stats(self) -> StatsResponse:
        uri: str = f"{self.uri}/v4/stats"

        async with self._session.get(url=uri, headers=self.headers) as resp:
            if resp.status == 200:
                resp_data: StatsResponse = await resp.json()
                return resp_data

            else:
                exc_data: ErrorResponse = await resp.json()
                raise LavalinkException(data=exc_data)

    async def _fetch_version(self) -> str:
        uri: str = f"{self.uri}/version"

        async with self._session.get(url=uri, headers=self.headers) as resp:
            if resp.status == 200:
                return await resp.text()

            exc_data: ErrorResponse = await resp.json()
            raise LavalinkException(data=exc_data)

    def get_player(self, guild_id: int, /) -> Player | None:
        """Return a :class:`~wavelink.Player` associated with the provided :attr:discord.Guild.id`.

        Parameters
        ----------
        guild_id: int
            The :attr:discord.Guild.id` to retrieve a :class:`~wavelink.Player` for.

            .. positional-only::
        /

        Returns
        -------
        Optional[:class:`~wavelink.Player`]
            The Player associated with this guild ID. Could be None if no :class:`~wavelink.Player` exists
            for this guild.
        """
        return self._players.get(guild_id, None)


class Pool:
    __nodes: dict[str, Node] = {}
    __cache: LFUCache | None = None

    @classmethod
    async def connect(
        cls, *, nodes: Iterable[Node], client: discord.Client | None = None, cache_capacity: int | None = None
    ) -> dict[str, Node]:
        """Connect the provided Iterable[:class:`Node`] to Lavalink.

        Parameters
        ----------
        *
        nodes: Iterable[:class:`Node`]
            The :class:`Node`'s to connect to Lavalink.
        client: :class:`discord.Client` | None
            The :class:`discord.Client` to use to connect the :class:`Node`. If the Node already has a client
            set, this method will **not** override it. Defaults to None.

        Returns
        -------
        dict[str, :class:`Node`]
            A mapping of :attr:`Node.identifier` to :class:`Node` associated with the :class:`Pool`.


        .. versionchanged:: 3.0.0
            The ``client`` parameter is no longer required.
        """
        for node in nodes:
            client_ = node.client or client

            if node.identifier in cls.__nodes:
                msg: str = f'Unable to connect {node!r} as you already have a node with identifier "{node.identifier}"'
                logger.error(msg)

                continue

            if node.status in (NodeStatus.CONNECTING, NodeStatus.CONNECTED):
                logger.error(f"Unable to connect {node!r} as it is already in a connecting or connected state.")
                continue

            try:
                await node._connect(client=client_)
            except InvalidClientException as e:
                logger.error(e)
            except AuthorizationFailedException:
                logger.error(f"Failed to authenticate {node!r} on Lavalink with the provided password.")
            except NodeException:
                logger.error(
                    f"Failed to connect to {node!r}. Check that your Lavalink major version is '4' "
                    f"and that you are trying to connect to Lavalink on the correct port."
                )
            else:
                cls.__nodes[node.identifier] = node

        if cache_capacity is not None and cls.nodes:
            if cache_capacity <= 0:
                logger.warning("LFU Request cache capacity must be > 0. Not enabling cache.")

            else:
                cls.__cache = LFUCache(capacity=cache_capacity)
                logger.info("Experimental request caching has been toggled ON. To disable run Pool.toggle_cache()")

        return cls.nodes

    @classproperty
    def nodes(cls) -> dict[str, Node]:
        """A mapping of :attr:`Node.identifier` to :class:`Node` that have previously been successfully connected.


        .. versionchanged:: 3.0.0
            This property now returns a copy.
        """
        nodes = cls.__nodes.copy()
        return nodes

    @classmethod
    def get_node(cls, identifier: str | None = None, /) -> Node:
        """Retrieve a :class:`Node` from the :class:`Pool` with the given identifier.

        If no identifier is provided, this method returns the ``best`` node.

        Parameters
        ----------
        identifier: str | None
            An optional identifier to retrieve a :class:`Node`.

            .. positional-only::
        /

        Raises
        ------
        InvalidNodeException
            Raised when a Node can not be found, or no :class:`Node` exists on the :class:`Pool`.


        .. versionchanged:: 3.0.0
            The ``id`` parameter was changed to ``identifier`` and is positional only.
        """
        if identifier:
            if identifier not in cls.__nodes:
                raise InvalidNodeException(f'A Node with the identifier "{identifier}" does not exist.')

            return cls.__nodes[identifier]

        nodes: list[Node] = [n for n in cls.__nodes.values() if n.status is NodeStatus.CONNECTED]
        if nodes:
            raise InvalidNodeException("No nodes are currently assigned to the wavelink.Pool in a CONNECTED state.")

        return sorted(nodes, key=lambda n: len(n.players))[0]

    @classmethod
    async def fetch_tracks(cls, query: str, /) -> list[Playable] | Playlist:
        """Search for a list of :class:`~wavelink.Playable` or a :class:`~wavelink.Playlist`, with the given query.

        Parameters
        ----------
        query: str
            The query to search tracks for. If this is not a URL based search you should provide the appropriate search
            prefix, E.g. "ytsearch:Rick Roll"

            .. positional-only::
        /

        Returns
        -------
        list[Playable] | Playlist
            A list of :class:`~wavelink.Playable` or a :class:`~wavelink.Playlist`
            based on your search ``query``. Could be an empty list, if no tracks were found.

        Raises
        ------
        LavalinkLoadException
            Exception raised when Lavalink fails to load results based on your query.


        .. versionchanged:: 3.0.0
            This method was previously known as both ``.get_tracks`` and ``.get_playlist``. This method now searches
            for both :class:`~wavelink.Playable` and :class:`~wavelink.Playlist` and returns the appropriate type,
            or an empty list if no results were found.

            This method no longer accepts the ``cls`` parameter.
        """
        # TODO: Documentation Extension for `.. positional-only::` marker.
        encoded_query: str = cast(str, urllib.parse.quote(query))  # type: ignore

        if cls.__cache is not None:
            potential: list[Playable] | Playlist = cls.__cache.get(encoded_query, None)

            if potential:
                return potential

        node: Node = cls.get_node()
        resp: LoadedResponse = await node._fetch_tracks(encoded_query)

        if resp["loadType"] == "track":
            track = Playable(data=resp["data"])

            if cls.__cache is not None and not track.is_stream:
                cls.__cache.put(encoded_query, [track])

            return [track]

        elif resp["loadType"] == "search":
            tracks = [Playable(data=tdata) for tdata in resp["data"]]

            if cls.__cache is not None:
                cls.__cache.put(encoded_query, tracks)

            return tracks

        if resp["loadType"] == "playlist":
            playlist: Playlist = Playlist(data=resp["data"])

            if cls.__cache is not None:
                cls.__cache.put(encoded_query, playlist)

            return playlist

        elif resp["loadType"] == "empty":
            return []

        elif resp["loadType"] == "error":
            raise LavalinkLoadException(data=resp["data"])

        else:
            return []

    @classmethod
    def toggle_cache(cls, capacity: int = 100) -> None:
        if cls.__cache is None and capacity <= 0:
            raise CapacityZero("LFU Request cache capacity must be > 0.")

        if cls.__cache is None:
            cls.__cache = LFUCache(capacity=capacity)
            logger.info("Experimental request caching has been toggled ON. To disable run Pool.toggle_cache()")
        else:
            cls.__cache = None
            logger.info("Experimental request caching has been toggled OFF. To enable run Pool.toggle_cache()")

    @classproperty
    def cache(cls) -> bool:
        return cls.__cache is not None
