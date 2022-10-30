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
import re
import uuid
from typing import Any, TYPE_CHECKING

import aiohttp
import discord
from discord.utils import classproperty

from .enums import NodeStatus
from .exceptions import *
from .websocket import Websocket

if TYPE_CHECKING:
    from .player import Player


__all__ = ('Node', 'NodePool')


logger: logging.Logger = logging.getLogger(__name__)


# noinspection PyShadowingBuiltins
class Node:

    def __init__(
            self,
            *,
            id: str = str(uuid.uuid4()),
            uri: str,
            password: str,
            secure: bool = False,
            session: aiohttp.ClientSession | None = None,
            heartbeat: float = 15.0,
            retries: int | None = None
    ):
        self._id: str = id
        self._uri: str = uri
        host: str = re.sub(r'https://|http://|wss://|ws://', '', self._uri)
        self._host: str = f'{"https://" if secure else "http://"}{host}'
        self._password: str = password

        self._session: aiohttp.ClientSession | None = session
        self.heartbeat: float = heartbeat
        self._retries: int | None = retries

        self.client: discord.Client | None = None
        self.client_id: int | None = None
        self._websocket: Websocket | None = None
        self._session_id: str | None = None

        self._players: dict[int, 'Player'] = {}

        self._status: NodeStatus = NodeStatus.DISCONNECTED
        self._major_version: int | None = None

    def __repr__(self):
        return f'Node: id="{self._id}", uri="{self.uri}", status={self.status}'

    def __eq__(self, other):
        return self.id == other.id

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
    def players(self) -> dict[int, 'Player']:
        return self._players

    @property
    def status(self) -> NodeStatus:
        return self._status

    async def _connect(self, client_id: int, client: discord.Client) -> None:
        if not self._session:
            self._session: aiohttp.ClientSession = aiohttp.ClientSession(headers={'Authorization': self._password})

        self.client: discord.Client = client
        self.client_id: int = client_id

        self._websocket: Websocket = Websocket(node=self)

        await self._websocket.connect()

        async with self._session.get(f'{self._host}/version') as resp:
            version: str = await resp.text()

            if version.endswith('-SNAPSHOT'):
                self._major_version: int = 3
                return

            version_tuple = tuple(int(v) for v in version.split('.'))
            if version_tuple[0] < 3:
                raise InvalidLavalinkVersion(f'Wavelink 2 is not compatible with Lavalink "{version}".')

            if version_tuple[0] == 3 and version_tuple[1] < 7:
                raise InvalidLavalinkVersion(f'Wavelink 2 is not compatible with Lavalink versions under "3.7".')

            self._major_version: int = version_tuple[0]

    async def _send(self,
                    *,
                    method: str,
                    path: str,
                    guild_id: int | str | None = None,
                    query: str | None = None,
                    data: dict[str, Any] = {}
                    ) -> dict[str, Any]:

        uri: str = f'{self._host}/' \
                   f'v{self._major_version}/' \
                   f'{path}' \
                   f'{f"/{guild_id}" if guild_id else ""}' \
                   f'{f"?{query}" if query else ""}'

        async with self._session.request(method=method, url=uri, json=data) as resp:
            if resp.status >= 300:
                raise InvalidLavalinkResponse(f'An error occurred when attempting to reach: "{uri}".',
                                              status=resp.status)

            return await resp.json()


# noinspection PyShadowingBuiltins
class NodePool:

    __nodes: dict[str, Node] = {}
    _client_id: int | None = None

    @classmethod
    async def connect(cls, *, client: discord.Client, nodes: list[Node]) -> dict[str, Node]:

        if not cls._client_id:
            cls._client_id = client.application_id or (await client.application_info()).id

        for node in nodes:

            if node.id in cls.__nodes:
                logger.error(f'A Node with the ID "{node.id}" already exists on the NodePool. Disregarding.')
                continue

            try:
                await node._connect(cls._client_id, client)
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
