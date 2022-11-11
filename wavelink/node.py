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

import logging
import random
import re
import string
from typing import TYPE_CHECKING, Any, TypeVar

import aiohttp
import discord
from discord.enums import try_enum
from discord.utils import MISSING, classproperty

from .enums import LoadType, NodeStatus
from .exceptions import *
from .websocket import Websocket

if TYPE_CHECKING:
    from .player import Player
    from .tracks import *
    from .types.request import Request

    PlayableT = TypeVar('PlayableT', bound=Playable)
    

__all__ = ('Node', 'NodePool')


logger: logging.Logger = logging.getLogger(__name__)


# noinspection PyShadowingBuiltins
class Node:

    def __init__(
            self,
            *,
            id: str | None = None,
            uri: str,
            password: str,
            secure: bool = False,
            session: aiohttp.ClientSession = MISSING,
            heartbeat: float = 15.0,
            retries: int | None = None
    ) -> None:
        if id is None:
            id = ''.join(random.sample(string.ascii_letters + string.digits, 12))

        self._id: str = id
        self._uri: str = uri
        host: str = re.sub(r'(?:http|ws)s?://', '', self._uri)
        self._host: str = f'{"https://" if secure else "http://"}{host}'
        self._password: str = password

        self._session: aiohttp.ClientSession = session
        self.heartbeat: float = heartbeat
        self._retries: int | None = retries

        self.client: discord.Client | None = None
        self._websocket: Websocket  = MISSING
        self._session_id: str | None = None

        self._players: dict[int, 'Player'] = {}

        self._status: NodeStatus = NodeStatus.DISCONNECTED
        self._major_version: int | None = None

    def __repr__(self) -> str:
        return f'Node: id="{self._id}", uri="{self.uri}", status={self.status}'

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Node):
            return self.id == other.id
        return NotImplemented

    @property
    def id(self) -> str:
        return self._id

    @property
    def uri(self) -> str:
        return self._uri

    @property
    def password(self) -> str:
        return self._password

    @property
    def players(self) -> dict[int, Player]:
        return self._players

    @property
    def status(self) -> NodeStatus:
        return self._status

    async def _connect(self, client: discord.Client) -> None:
        if client.user is None:
            raise RuntimeError('')

        if not self._session:
            self._session = aiohttp.ClientSession(headers={'Authorization': self._password})

        self.client = client

        self._websocket = Websocket(node=self)

        await self._websocket.connect()

        async with self._session.get(f'{self._host}/version') as resp:
            version: str = await resp.text()

            if version.endswith('-SNAPSHOT'):
                self._major_version = 3
                return

            version_tuple = tuple(int(v) for v in version.split('.'))
            if version_tuple[0] < 3:
                raise InvalidLavalinkVersion(f'Wavelink 2 is not compatible with Lavalink "{version}".')

            if version_tuple[0] == 3 and version_tuple[1] < 7:
                raise InvalidLavalinkVersion(f'Wavelink 2 is not compatible with Lavalink versions under "3.7".')

            self._major_version = version_tuple[0]

    async def _send(self,
                    *,
                    method: str,
                    path: str,
                    guild_id: int | str | None = None,
                    query: str | None = None,
                    data: Request | None = None,
                    ) -> dict[str, Any]:

        uri: str = f'{self._host}/' \
                   f'v{self._major_version}/' \
                   f'{path}' \
                   f'{f"/{guild_id}" if guild_id else ""}' \
                   f'{f"?{query}" if query else ""}'

        async with self._session.request(method=method, url=uri, json=data or {}) as resp:
            if resp.status >= 300:
                raise InvalidLavalinkResponse(f'An error occurred when attempting to reach: "{uri}".',
                                              status=resp.status)

            return await resp.json()

    async def get_tracks(self, cls: type[PlayableT], query: str) -> list[PlayableT]:
        data = await self._send(method='GET', path='loadtracks', query=f'identifier={query}')
        load_type = try_enum(LoadType, data.get("loadType"))

        if load_type is LoadType.load_failed:
            # TODO - Proper Exception...

            raise ValueError('Track Failed to load.')

        if load_type is LoadType.no_matches:
            return []

        if load_type is LoadType.track_loaded:
            track_data = data["tracks"][0]
            return [cls(track_data)]

        if load_type is not LoadType.search_result:
            # TODO - Proper Exception...

            raise ValueError('Track Failed to load.')

        return [cls(track_data) for track_data in data["tracks"]]

    async def build_track(self, *, cls: type[PlayableT], encoded: str) -> PlayableT:
        data = await self._send(method='GET', path='decodetrack', query=f'encodedTrack={encoded}')

        return cls(data=data)


# noinspection PyShadowingBuiltins
class NodePool:

    __nodes: dict[str, Node] = {}

    @classmethod
    async def connect(cls, *, client: discord.Client, nodes: list[Node]) -> dict[str, Node]:
        if client.user is None:
            raise RuntimeError('')

        for node in nodes:

            if node.id in cls.__nodes:
                logger.error(f'A Node with the ID "{node.id}" already exists on the NodePool. Disregarding.')
                continue

            try:
                await node._connect(client)
            except AuthorizationFailed:
                logger.error(f'The Node <{node!r}> failed to authenticate properly. '
                             f'Please check your password and try again.')
            else:
                cls.__nodes[node.id] = node

        return cls.nodes

    @classproperty
    def nodes(cls) -> dict[str, Node]:
        return cls.__nodes

    @classmethod
    def get_node(cls, id: str | None = None) -> Node:
        if id:
            if id not in cls.__nodes:
                raise InvalidNode(f'A Node with ID "{id}" does not exist on the Wavelink NodePool.')

            return cls.__nodes[id]

        if not cls.__nodes:
            raise InvalidNode('No Node currently exists on the Wavelink NodePool.')

        nodes = cls.__nodes.values()
        return sorted(nodes, key=lambda n: len(n.players))[0]

    @classmethod
    def get_connected_node(cls) -> Node:

        nodes: list[Node] = [n for n in cls.__nodes.values() if n.status is NodeStatus.CONNECTED]
        if not nodes:
            raise InvalidNode('There are Nodes on the Wavelink NodePool that are currently in the connected state.')

        return sorted(nodes, key=lambda n: len(n.players))[0]

    @classmethod
    async def get_tracks(cls_,  # type: ignore
                         query: str,
                         /,
                         *,
                         cls: type[PlayableT],
                         node: Node | None = None
                         ) -> list[PlayableT]:
        if not node:
            node = cls_.get_connected_node()

        return await node.get_tracks(cls=cls, query=query)
