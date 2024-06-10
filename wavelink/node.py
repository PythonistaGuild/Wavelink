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
import secrets
import urllib.parse
from typing import TYPE_CHECKING, Any, ClassVar, Literal, TypeAlias

import aiohttp
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
from .lfu import LFUCache
from .payloads import *
from .tracks import Playable, Playlist
from .websocket import Websocket


if TYPE_CHECKING:
    from collections.abc import Iterable

    import discord

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

    LoadedResponse: TypeAlias = (
        TrackLoadedResponse | SearchLoadedResponse | PlaylistLoadedResponse | EmptyLoadedResponse | ErrorLoadedResponse
    )


__all__ = ("Node", "Pool")


logger: logging.Logger = logging.getLogger(__name__)


Method = Literal["GET", "POST", "PATCH", "DELETE", "PUT", "OPTIONS"]


class Node:
    """The Node represents a connection to Lavalink.

    The Node is responsible for keeping the websocket alive, resuming session, sending API requests and keeping track
    of connected all :class:`~wavelink.Player`.

    .. container:: operations

        .. describe:: node == other

            Equality check to determine whether this Node is equal to another reference of a Node.

        .. describe:: repr(node)

            The official string representation of this Node.

    Parameters
    ----------
    identifier: str | None
        A unique identifier for this Node. Could be ``None`` to generate a random one on creation.
    uri: str
        The URL/URI that wavelink will use to connect to Lavalink. Usually this is in the form of something like:
        ``http://localhost:2333`` which includes the port. But you could also provide a domain which won't require a
        port like ``https://lavalink.example.com`` or a public IP address and port like ``http://111.333.444.55:2333``.
    password: str
        The password used to connect and authorize this Node.
    session: aiohttp.ClientSession | None
        An optional :class:`aiohttp.ClientSession` used to connect this Node over websocket and REST.
        If ``None``, one will be generated for you. Defaults to ``None``.
    heartbeat: Optional[float]
        A ``float`` in seconds to ping your websocket keep alive. Usually you would not change this.
    retries: int | None
        A ``int`` of retries to attempt when connecting or reconnecting this Node. When the retries are exhausted
        the Node will be closed and cleaned-up. ``None`` will retry forever. Defaults to ``None``.
    client: :class:`discord.Client` | None
        The :class:`discord.Client` or subclasses, E.g. ``commands.Bot`` used to connect this Node. If this is *not*
        passed you must pass this to :meth:`wavelink.Pool.connect`.
    resume_timeout: Optional[int]
        The seconds this Node should configure Lavalink for resuming its current session in case of network issues.
        If this is ``0`` or below, resuming will be disabled. Defaults to ``60``.
    inactive_player_timeout: int | None
        Set the default for :attr:`wavelink.Player.inactive_timeout` on every player that connects to this node.
        Defaults to ``300``.
    inactive_channel_tokens: int | None
        Sets the default for :attr:`wavelink.Player.inactive_channel_tokens` on every player that connects to this node.
        Defaults to ``3``.

        See also: :func:`on_wavelink_inactive_player`.
    """

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
        resume_timeout: int = 60,
        inactive_player_timeout: int | None = 300,
        inactive_channel_tokens: int | None = 3,
    ) -> None:
        self._identifier = identifier or secrets.token_urlsafe(12)
        self._uri = uri.removesuffix("/")
        self._password = password
        self._session = session or aiohttp.ClientSession()
        self._heartbeat = heartbeat
        self._retries = retries
        self._client = client
        self._resume_timeout = resume_timeout

        self._status: NodeStatus = NodeStatus.DISCONNECTED
        self._has_closed: bool = False
        self._session_id: str | None = None

        self._players: dict[int, Player] = {}
        self._total_player_count: int | None = None

        self._spotify_enabled: bool = False

        self._websocket: Websocket | None = None

        if inactive_player_timeout and inactive_player_timeout < 10:
            logger.warning('Setting "inactive_player_timeout" below 10 seconds may result in unwanted side effects.')

        self._inactive_player_timeout = (
            inactive_player_timeout if inactive_player_timeout and inactive_player_timeout > 0 else None
        )

        self._inactive_channel_tokens = inactive_channel_tokens

    def __repr__(self) -> str:
        return f"Node(identifier={self.identifier}, uri={self.uri}, status={self.status}, players={len(self.players)})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Node):
            return NotImplemented

        return other.identifier == self.identifier

    @property
    def headers(self) -> dict[str, str]:
        """A property that returns the headers configured for sending API and websocket requests.

        .. warning::

            This includes your Node password. Please be vigilant when using this property.
        """
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
        """A mapping of :attr:`discord.Guild.id` to :class:`~wavelink.Player`.


        .. versionchanged:: 3.1.1

            This property now returns a shallow copy of the internal mapping.
        """
        return self._players.copy()

    @property
    def client(self) -> discord.Client | None:
        """Returns the :class:`discord.Client` associated with this :class:`Node`.

        Could be ``None`` if it has not been set yet.


        .. versionadded:: 3.0.0
        """
        return self._client

    @property
    def password(self) -> str:
        """Returns the password used to connect this :class:`Node` to Lavalink.

        .. versionadded:: 3.0.0
        """
        return self._password

    @property
    def heartbeat(self) -> float:
        """Returns the duration in seconds that the :class:`Node` websocket should send a heartbeat.

        .. versionadded:: 3.0.0
        """
        return self._heartbeat

    @property
    def session_id(self) -> str | None:
        """Returns the Lavalink session ID. Could be None if this :class:`Node` has not connected yet.

        .. versionadded:: 3.0.0
        """
        return self._session_id

    async def _pool_closer(self) -> None:
        try:
            await self._session.close()
        except Exception:
            pass

        if not self._has_closed:
            await self.close()

    async def close(self, eject: bool = False) -> None:
        """Method to close this Node and cleanup.

        After this method has finished, the event ``on_wavelink_node_closed`` will be fired.

        This method renders the Node websocket disconnected and disconnects all players.

        Parameters
        ----------
        eject: bool
            If ``True``, this will remove the Node from the Pool. Defaults to ``False``.


        .. versionchanged:: 3.2.1

            Added the ``eject`` parameter. Fixed a bug where the connected Players were not being disconnected.
        """
        disconnected: list[Player] = []

        for player in self._players.copy().values():
            try:
                await player.disconnect()
            except Exception as e:
                logger.debug("An error occured while disconnecting a player in the close method of %r: %s", self, e)
                pass

            disconnected.append(player)

        if self._websocket is not None:
            await self._websocket.cleanup()

        self._status = NodeStatus.DISCONNECTED
        self._session_id = None
        self._players = {}

        self._has_closed = True

        if eject:
            getattr(Pool, "_Pool__nodes").pop(self.identifier, None)

        # Dispatch Node Closed Event... node, list of disconnected players
        if self.client is not None:
            self.client.dispatch("wavelink_node_closed", self, disconnected)

    async def _connect(self, *, client: discord.Client | None) -> None:
        client_ = self._client or client

        if not client_:
            raise InvalidClientException(f"Unable to connect {self!r} as you have not provided a valid discord.Client.")

        self._client = client_

        self._has_closed = False
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession()

        websocket: Websocket = Websocket(node=self)
        self._websocket = websocket
        await websocket.connect()

    async def send(
        self, method: Method = "GET", *, path: str, data: Any | None = None, params: dict[str, Any] | None = None
    ) -> Any:
        """Method for making requests to the Lavalink node.

        .. warning::

            Usually you wouldn't use this method. Please use the built in methods of :class:`~Node`, :class:`~Pool`
            and :class:`~wavelink.Player`, unless you need to send specific plugin data to Lavalink.

            Using this method may have unwanted side effects on your players and/or nodes.

        Parameters
        ----------
        method: Optional[str]
            The method to use when making this request. Available methods are
            "GET", "POST", "PATCH", "PUT", "DELETE" and "OPTIONS". Defaults to "GET".
        path: str
            The path to make this request to. E.g. "/v4/stats".
        data: Any | None
            The optional JSON data to send along with your request to Lavalink. This should be a dict[str, Any]
            and able to be converted to JSON.
        params: Optional[dict[str, Any]]
            An optional dict of query parameters to send with your request to Lavalink. If you include your query
            parameters in the ``path`` parameter, do not pass them here as well. E.g. {"thing": 1, "other": 2}
            would equate to "?thing=1&other=2".

        Returns
        -------
        Any
            The response from Lavalink which will either be None, a str or JSON.

        Raises
        ------
        LavalinkException
            An error occurred while making this request to Lavalink.
        NodeException
            An error occured while making this request to Lavalink,
            and Lavalink was unable to send any error information.


        .. versionadded:: 3.0.0
        """
        clean_path: str = path.removesuffix("/")
        uri: str = f"{self.uri}/{clean_path}"

        if params is None:
            params = {}

        async with self._session.request(
            method=method, url=uri, params=params, json=data, headers=self.headers
        ) as resp:
            if resp.status == 204:
                return

            if resp.status >= 300:
                try:
                    exc_data: ErrorResponse = await resp.json()
                except Exception as e:
                    logger.warning("An error occured making a request on %r: %s", self, e)
                    raise NodeException(status=resp.status)

                raise LavalinkException(data=exc_data)

            try:
                rdata: Any = await resp.json()
            except aiohttp.ContentTypeError:
                pass
            else:
                return rdata

            try:
                body: str = await resp.text()
            except aiohttp.ClientError:
                return

            return body

    async def _fetch_players(self) -> list[PlayerResponse]:
        uri: str = f"{self.uri}/v4/sessions/{self.session_id}/players"

        async with self._session.get(url=uri, headers=self.headers) as resp:
            if resp.status == 200:
                resp_data: list[PlayerResponse] = await resp.json()
                return resp_data

            else:
                try:
                    exc_data: ErrorResponse = await resp.json()
                except Exception as e:
                    logger.warning("An error occured making a request on %r: %s", self, e)
                    raise NodeException(status=resp.status)

                raise LavalinkException(data=exc_data)

    async def fetch_players(self) -> list[PlayerResponsePayload]:
        """Method to fetch the player information Lavalink holds for every connected player on this node.

        .. warning::

            This payload is not the same as the :class:`wavelink.Player` class. This is the data received from
            Lavalink about the players.


        Returns
        -------
        list[:class:`PlayerResponsePayload`]
            A list of :class:`PlayerResponsePayload` representing each player connected to this node.

        Raises
        ------
        LavalinkException
            An error occurred while making this request to Lavalink.
        NodeException
            An error occured while making this request to Lavalink,
            and Lavalink was unable to send any error information.


        .. versionadded:: 3.1.0
        """
        data: list[PlayerResponse] = await self._fetch_players()

        payload: list[PlayerResponsePayload] = [PlayerResponsePayload(p) for p in data]
        return payload

    async def _fetch_player(self, guild_id: int, /) -> PlayerResponse:
        uri: str = f"{self.uri}/v4/sessions/{self.session_id}/players/{guild_id}"

        async with self._session.get(url=uri, headers=self.headers) as resp:
            if resp.status == 200:
                resp_data: PlayerResponse = await resp.json()
                return resp_data

            else:
                try:
                    exc_data: ErrorResponse = await resp.json()
                except Exception as e:
                    logger.warning("An error occured making a request on %r: %s", self, e)
                    raise NodeException(status=resp.status)

                raise LavalinkException(data=exc_data)

    async def fetch_player_info(self, guild_id: int, /) -> PlayerResponsePayload | None:
        """Method to fetch the player information Lavalink holds for the specific guild.

        .. warning::

            This payload is not the same as the :class:`wavelink.Player` class. This is the data received from
            Lavalink about the player. See: :meth:`~wavelink.Node.get_player`


        Parameters
        ----------
        guild_id: int
            The ID of the guild you want to fetch info for.

        Returns
        -------
        :class:`PlayerResponsePayload` | None
            The :class:`PlayerResponsePayload` representing the player info for the guild ID connected to this node.
            Could be ``None`` if no player is found with the given guild ID.

        Raises
        ------
        LavalinkException
            An error occurred while making this request to Lavalink.
        NodeException
            An error occured while making this request to Lavalink,
            and Lavalink was unable to send any error information.


        .. versionadded:: 3.1.0
        """
        try:
            data: PlayerResponse = await self._fetch_player(guild_id)
        except LavalinkException as e:
            if e.status == 404:
                return None

            raise e

        payload: PlayerResponsePayload = PlayerResponsePayload(data)
        return payload

    async def _update_player(self, guild_id: int, /, *, data: Request, replace: bool = False) -> PlayerResponse:
        no_replace: bool = not replace

        uri: str = f"{self.uri}/v4/sessions/{self.session_id}/players/{guild_id}?noReplace={no_replace}"

        async with self._session.patch(url=uri, json=data, headers=self.headers) as resp:
            if resp.status == 200:
                resp_data: PlayerResponse = await resp.json()
                return resp_data

            else:
                try:
                    exc_data: ErrorResponse = await resp.json()
                except Exception as e:
                    logger.warning("An error occured making a request on %r: %s", self, e)
                    raise NodeException(status=resp.status)

                raise LavalinkException(data=exc_data)

    async def _destroy_player(self, guild_id: int, /) -> None:
        uri: str = f"{self.uri}/v4/sessions/{self.session_id}/players/{guild_id}"

        async with self._session.delete(url=uri, headers=self.headers) as resp:
            if resp.status == 204:
                return

            try:
                exc_data: ErrorResponse = await resp.json()
            except Exception as e:
                logger.warning("An error occured making a request on %r: %s", self, e)
                raise NodeException(status=resp.status)

            raise LavalinkException(data=exc_data)

    async def _update_session(self, *, data: UpdateSessionRequest) -> UpdateResponse:
        uri: str = f"{self.uri}/v4/sessions/{self.session_id}"

        async with self._session.patch(url=uri, json=data, headers=self.headers) as resp:
            if resp.status == 200:
                resp_data: UpdateResponse = await resp.json()
                return resp_data

            else:
                try:
                    exc_data: ErrorResponse = await resp.json()
                except Exception as e:
                    logger.warning("An error occured making a request on %r: %s", self, e)
                    raise NodeException(status=resp.status)

                raise LavalinkException(data=exc_data)

    async def _fetch_tracks(self, query: str) -> LoadedResponse:
        uri: str = f"{self.uri}/v4/loadtracks?identifier={query}"

        async with self._session.get(url=uri, headers=self.headers) as resp:
            if resp.status == 200:
                resp_data: LoadedResponse = await resp.json()
                return resp_data

            else:
                try:
                    exc_data: ErrorResponse = await resp.json()
                except Exception as e:
                    logger.warning("An error occured making a request on %r: %s", self, e)
                    raise NodeException(status=resp.status)

                raise LavalinkException(data=exc_data)

    async def _decode_track(self) -> TrackPayload: ...

    async def _decode_tracks(self) -> list[TrackPayload]: ...

    async def _fetch_info(self) -> InfoResponse:
        uri: str = f"{self.uri}/v4/info"

        async with self._session.get(url=uri, headers=self.headers) as resp:
            if resp.status == 200:
                resp_data: InfoResponse = await resp.json()
                return resp_data

            else:
                try:
                    exc_data: ErrorResponse = await resp.json()
                except Exception as e:
                    logger.warning("An error occured making a request on %r: %s", self, e)
                    raise NodeException(status=resp.status)

                raise LavalinkException(data=exc_data)

    async def fetch_info(self) -> InfoResponsePayload:
        """Method to fetch this Lavalink Nodes info response data.

        Returns
        -------
        :class:`InfoResponsePayload`
            The :class:`InfoResponsePayload` associated with this Node.

        Raises
        ------
        LavalinkException
            An error occurred while making this request to Lavalink.
        NodeException
            An error occured while making this request to Lavalink,
            and Lavalink was unable to send any error information.


        .. versionadded:: 3.1.0
        """
        data: InfoResponse = await self._fetch_info()

        payload: InfoResponsePayload = InfoResponsePayload(data)
        return payload

    async def _fetch_stats(self) -> StatsResponse:
        uri: str = f"{self.uri}/v4/stats"

        async with self._session.get(url=uri, headers=self.headers) as resp:
            if resp.status == 200:
                resp_data: StatsResponse = await resp.json()
                return resp_data

            else:
                try:
                    exc_data: ErrorResponse = await resp.json()
                except Exception as e:
                    logger.warning("An error occured making a request on %r: %s", self, e)
                    raise NodeException(status=resp.status)

                raise LavalinkException(data=exc_data)

    async def fetch_stats(self) -> StatsResponsePayload:
        """Method to fetch this Lavalink Nodes stats response data.

        Returns
        -------
        :class:`StatsResponsePayload`
            The :class:`StatsResponsePayload` associated with this Node.

        Raises
        ------
        LavalinkException
            An error occurred while making this request to Lavalink.
        NodeException
            An error occured while making this request to Lavalink,
            and Lavalink was unable to send any error information.


        .. versionadded:: 3.1.0
        """
        data: StatsResponse = await self._fetch_stats()

        payload: StatsResponsePayload = StatsResponsePayload(data)
        return payload

    async def _fetch_version(self) -> str:
        uri: str = f"{self.uri}/version"

        async with self._session.get(url=uri, headers=self.headers) as resp:
            if resp.status == 200:
                return await resp.text()

            try:
                exc_data: ErrorResponse = await resp.json()
            except Exception as e:
                logger.warning("An error occured making a request on %r: %s", self, e)
                raise NodeException(status=resp.status)

            raise LavalinkException(data=exc_data)

    async def fetch_version(self) -> str:
        """Method to fetch this Lavalink version string.

        Returns
        -------
        str
            The version string associated with this Lavalink node.

        Raises
        ------
        LavalinkException
            An error occurred while making this request to Lavalink.
        NodeException
            An error occured while making this request to Lavalink,
            and Lavalink was unable to send any error information.


        .. versionadded:: 3.1.0
        """
        data: str = await self._fetch_version()
        return data

    def get_player(self, guild_id: int, /) -> Player | None:
        """Return a :class:`~wavelink.Player` associated with the provided :attr:`discord.Guild.id`.

        Parameters
        ----------
        guild_id: int
            The :attr:`discord.Guild.id` to retrieve a :class:`~wavelink.Player` for.

        Returns
        -------
        Optional[:class:`~wavelink.Player`]
            The Player associated with this guild ID. Could be None if no :class:`~wavelink.Player` exists
            for this guild.
        """
        return self._players.get(guild_id, None)


class Pool:
    """The wavelink Pool represents a collection of :class:`~wavelink.Node` and helper methods for searching tracks.

    To connect a :class:`~wavelink.Node` please use this Pool.

    .. note::

        All methods and attributes on this class are class level, not instance. Do not create an instance of this class.
    """

    __nodes: ClassVar[dict[str, Node]] = {}
    __cache: LFUCache | None = None

    @classmethod
    async def connect(
        cls, *, nodes: Iterable[Node], client: discord.Client | None = None, cache_capacity: int | None = None
    ) -> dict[str, Node]:
        """Connect the provided Iterable[:class:`Node`] to Lavalink.

        Parameters
        ----------
        nodes: Iterable[:class:`Node`]
            The :class:`Node`'s to connect to Lavalink.
        client: :class:`discord.Client` | None
            The :class:`discord.Client` to use to connect the :class:`Node`. If the Node already has a client
            set, this method will **not** override it. Defaults to None.
        cache_capacity: int | None
            An optional integer of the amount of track searches to cache. This is an experimental mode.
            Passing ``None`` will disable this experiment. Defaults to ``None``.

        Returns
        -------
        dict[str, :class:`Node`]
            A mapping of :attr:`Node.identifier` to :class:`Node` associated with the :class:`Pool`.


        Raises
        ------
        AuthorizationFailedException
            The node password was incorrect.
        InvalidClientException
            The :class:`discord.Client` passed was not valid.
        NodeException
            The node failed to connect properly. Please check that your Lavalink version is version 4.


        .. versionchanged:: 3.0.0

            The ``client`` parameter is no longer required.
            Added the ``cache_capacity`` parameter.
        """
        for node in nodes:
            client_ = node.client or client

            if node.identifier in cls.__nodes:
                msg: str = f'Unable to connect {node!r} as you already have a node with identifier "{node.identifier}"'
                logger.error(msg)

                continue

            if node.status in (NodeStatus.CONNECTING, NodeStatus.CONNECTED):
                logger.error("Unable to connect %r as it is already in a connecting or connected state.", node)
                continue

            try:
                await node._connect(client=client_)
            except InvalidClientException as e:
                logger.error(e)
            except AuthorizationFailedException:
                logger.error("Failed to authenticate %r on Lavalink with the provided password.", node)
            except NodeException:
                logger.error(
                    "Failed to connect to %r. Check that your Lavalink major version is '4' and that you are trying to connect to Lavalink on the correct port.",
                    node,
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

    @classmethod
    async def reconnect(cls) -> dict[str, Node]:
        for node in cls.__nodes.values():
            if node.status is not NodeStatus.DISCONNECTED:
                continue

            try:
                await node._connect(client=None)
            except InvalidClientException as e:
                logger.error(e)
            except AuthorizationFailedException:
                logger.error("Failed to authenticate %r on Lavalink with the provided password.", node)
            except NodeException:
                logger.error(
                    "Failed to connect to %r. Check that your Lavalink major version is '4' and that you are trying to connect to Lavalink on the correct port.",
                    node,
                )

        return cls.nodes

    @classmethod
    async def close(cls) -> None:
        """Close and clean up all :class:`~wavelink.Node` on this Pool.

        This calls :meth:`wavelink.Node.close` on each node.


        .. versionadded:: 3.0.0
        """
        for node in cls.__nodes.values():
            await node.close()

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
        if not nodes:
            raise InvalidNodeException("No nodes are currently assigned to the wavelink.Pool in a CONNECTED state.")

        return sorted(nodes, key=lambda n: n._total_player_count or len(n.players))[0]

    @classmethod
    async def fetch_tracks(cls, query: str, /, *, node: Node | None = None) -> list[Playable] | Playlist:
        """Search for a list of :class:`~wavelink.Playable` or a :class:`~wavelink.Playlist`, with the given query.

        Parameters
        ----------
        query: str
            The query to search tracks for. If this is not a URL based search you should provide the appropriate search
            prefix, e.g. "ytsearch:Rick Roll"
        node: :class:`~wavelink.Node` | None
            An optional :class:`~wavelink.Node` to use when fetching tracks. Defaults to ``None``, which selects the
            most appropriate :class:`~wavelink.Node` automatically.

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


        .. versionadded:: 3.4.0

            Added the ``node`` Keyword-Only argument.
        """

        # TODO: Documentation Extension for `.. positional-only::` marker.
        encoded_query: str = urllib.parse.quote(query)

        if cls.__cache is not None:
            potential: list[Playable] | Playlist = cls.__cache.get(encoded_query, None)

            if potential:
                return potential

        node_: Node = node or cls.get_node()
        resp: LoadedResponse = await node_._fetch_tracks(encoded_query)

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
    def cache(cls, capacity: int | None | bool = None) -> None:
        if capacity in (None, False) or capacity <= 0:
            cls.__cache = None
            return

        if not isinstance(capacity, int):  # type: ignore
            raise ValueError("The LFU cache expects an integer, None or bool.")

        cls.__cache = LFUCache(capacity=capacity)

    @classmethod
    def has_cache(cls) -> bool:
        return cls.__cache is not None
