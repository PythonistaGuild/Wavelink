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
import aiohttp
import asyncio
import logging
from discord.ext import commands
from functools import partial
from typing import Optional, Union

from .errors import *
from .player import Player
from .node import Node


__log__ = logging.getLogger(__name__)


class Client:
    """The main WaveLink client."""

    def __new__(cls, *args, **kwargs):
        cls.__qualname__ = 'wavelink.Client'

        try:
            bot = kwargs['bot']
        except KeyError:
            msg = 'wavelink.Client: bot is a required keyword only argument which is missing.'
            raise WavelinkException(msg)

        if not isinstance(bot, (commands.Bot, commands.AutoShardedBot)):
            msg = f'wavelink.Client expected type <commands.Bot or commands.AutoShardedBot> not {type(bot)}'
            raise TypeError(msg)

        try:
            update_handlers = bot.extra_events['on_socket_response']
        except KeyError:
            return super().__new__(cls)

        for handler in update_handlers:
            if handler.__self__.__class__.__qualname__ == 'wavelink.Client':
                bot.remove_listener(handler, 'on_socket_response')

        return super().__new__(cls)

    def __init__(self, bot: Union[commands.Bot, commands.AutoShardedBot]):
        self.bot = bot
        self.loop = bot.loop or asyncio.get_event_loop()
        self.session = aiohttp.ClientSession(loop=self.loop)

        self.nodes = {}

        bot.add_listener(self.update_handler, 'on_socket_response')

    @property
    def shard_count(self) -> int:
        """Return the bots Shard Count as an int.

        Returns
        ---------
        int:
            An int of the bots shard count.
        """
        return self.bot.shard_count or 1

    @property
    def user_id(self) -> int:
        """Return the Bot users ID.

        Returns
        ---------
        int:
            The bots user ID.
        """
        return self.bot.user.id

    @property
    def players(self) -> dict:
        """Return the WaveLink clients current players across all nodes.

        Returns
        ---------
        dict:
            A dict of the current WaveLink players.
        """
        return self._get_players()

    async def _dispatch_listeners(self, name: str, *args, **kwargs) -> None:
        futures = []

        for cog in self.bot.cogs.values():
            try:
                listeners = cog.__wavelink_listeners__[name]
            except (AttributeError, KeyError):
                continue

            for listener in listeners:
                method = getattr(cog, listener)
                future = asyncio.ensure_future(method(*args, **kwargs))

                callback = partial(self._future_callback, cog, method)
                future.add_done_callback(callback)
                futures.append(future)

        if not futures:
            return

        await asyncio.gather(*futures, return_exceptions=True)

    def _future_callback(self, cog, listener, fut):
        if fut.exception():
            self.loop.create_task(cog.on_wavelink_error(listener, fut.exception()))

    async def get_tracks(self, query: str) -> Optional[list]:
        """|coro|

        Search for and return a list of Tracks for the given query.

        Parameters
        ------------
        query: str
            The query to use to search for tracks. If a valid URL is not provided, it's best to default to
            "ytsearch:query", which allows the REST server to search YouTube for Tracks.

        Returns
        ---------
        Union[list, TrackPlaylist, None]:
            A list of or :class:`TrackPlaylist` instance of :class:`Track` objects.
            This could be None if no tracks were found.

        Raises
        --------
        ZeroConnectedNodes
            There are no :class:`wavelink.node.Node`s currently connected.
        """
        node = self.get_best_node()
        
        if node is None:
            raise ZeroConnectedNodes

        return await node.get_tracks(query)

    async def build_track(self, identifier: str):
        """|coro|

        Build a track object with a valid track identifier.

        Parameters
        ------------
        identifier: str
            The tracks unique Base64 encoded identifier. This is usually retrieved from various lavalink events.

        Returns
        ---------
        :class:`wavelink.player.Track`
            The track built from a Base64 identifier.

        Raises
        --------
        ZeroConnectedNodes
            There are no :class:`wavelink.node.Node`s currently connected.
        BuildTrackError
            Decoding and building the track failed.
        """
        node = self.get_best_node()

        if node is None:
            raise ZeroConnectedNodes

        return await node.build_track(identifier)

    def _get_players(self) -> dict:
        players = []

        for node in self.nodes.values():
            players.extend(node.players.values())

        return {player.guild_id: player for player in players}

    def get_node(self, identifier: str) -> Optional[Node]:
        """Retrieve a Node with the given identifier.

        Parameters
        ------------
        identifier: str
            The unique identifier to search for.

        Returns
        ---------
        Optional[:class:`wavelink.node.Node`]
            The Node matching the given identifier. This could be None if no :class:`wavelink.node.Node` could be found.
        """
        return self.nodes.get(identifier, None)

    def get_best_node(self) -> Optional[Node]:
        """Return the best available :class:`wavelink.node.Node` across the :class:`.Client`.

        Returns
        ---------
        Optional[:class:`wavelink.node.Node`]
            The best available :class:`wavelink.node.Node` available to the :class:`.Client`.
        """
        nodes = [n for n in self.nodes.values() if n.is_available]
        if not nodes:
            return None

        return sorted(nodes, key=lambda n: len(n.players))[0]

    def get_node_by_region(self, region: str) -> Optional[Node]:
        """Retrieve the best available Node with the given region.

        Parameters
        ------------
        region: str
            The region to search for.

        Returns
        ---------
        Optional[:class:`wavelink.node.Node`]
            The best available Node matching the given region.
            This could be None if no :class:`wavelink.node.Node` could be found.
        """
        nodes = [n for n in self.nodes.values() if n.region.lower() == region.lower() and n.is_available]
        if not nodes:
            return None

        return sorted(nodes, key=lambda n: len(n.players))[0]

    def get_node_by_shard(self, shard_id: int) -> Optional[Node]:
        """Retrieve the best available Node with the given shard ID.

        Parameters
        ------------
        shard_id: int
            The shard ID to search for.

        Returns
        ---------
        Optional[:class:`wavelink.node.Node`]
            The best available Node matching the given Shard ID.
            This could be None if no :class:`wavelink.node.Node` could be found.
        """
        nodes = [n for n in self.nodes.values() if n.shard_id == shard_id and n.is_available]
        if not nodes:
            return None

        return sorted(nodes, key=lambda n: len(n.players))[0]

    def get_player(self, guild_id: int, *, cls=None, node_id=None, **kwargs) -> Player:
        """Retrieve a player for the given guild ID. If None, a player will be created and returned.

        .. versionchanged:: 0.3.0
            cls is now a keyword only argument.

        .. versionadded:: 0.5.01
            Added support for passing kwarg parameters to the cls.

        Parameters
        ------------
        guild_id: int
            The guild ID to retrieve a player for.
        cls: Optional[class]
            An optional class to pass to build from, overriding the default :class:`Player` class.
            This must be similar to :class:`Player`. E.g a subclass.
        node_id: Optional[str]
            An optional Node identifier to create a player under. If the player already exists this will be ignored.
            Otherwise an attempt to find the node and assign a new player will be made.

        Returns
        ---------
        Player
            The :class:`wavelink.player.Player` associated with the given guild ID.

        Raises
        --------
        InvalidIDProvided
            The given ID does not yield a valid guild or Node.
        ZeroConnectedNodes
            There are no :class:`wavelink.node.Node`'s currently connected.
        """
        players = self.players

        try:
            player = players[guild_id]
        except KeyError:
            pass
        else:
            return player

        guild = self.bot.get_guild(guild_id)
        if not guild:
            raise InvalidIDProvided(f'A guild with the id <{guild_id}> can not be located.')

        if not self.nodes:
            raise ZeroConnectedNodes('There are not any currently connected nodes.')

        if not cls:
            cls = Player

        if node_id:
            node = self.get_node(identifier=node_id)

            if not node:
                raise InvalidIDProvided(f'A Node with the identifier <{node_id}> does not exist.')

            player = cls(self.bot, guild_id, node, **kwargs)
            node.players[guild_id] = player

            return player

        shard_options = []
        region_options = []
        nodes = self.nodes.values()

        for node in nodes:
            if not node.is_available:
                continue
            if node.shard_id == guild.shard_id:
                shard_options.append(node)
            if node.region.lower() == str(guild.region).lower():
                region_options.append(node)

        if not shard_options and not region_options:
            # Sort by len of node players
            node = sorted(nodes, key=lambda n: len(n.players))[0]
            player = cls(self.bot, guild_id, node, **kwargs)
            node.players[guild_id] = player

            return player

        best = [n for n in shard_options if n in region_options]
        if best:
            node = sorted(best, key=lambda n: len(n.players))[0]
        elif shard_options:
            node = sorted(shard_options, key=lambda n: len(n.players))[0]
        else:
            node = sorted(region_options, key=lambda n: len(n.players))[0]

        player = cls(self.bot, guild_id, node, **kwargs)
        node.players[guild_id] = player

        return player

    async def initiate_node(self, host: str, port: int, *, rest_uri: str, password: str, region: str, identifier: str,
                            shard_id: int = None, secure: bool = False, heartbeat: float = None) -> Node:
        """|coro|

        Initiate a Node and connect to the provided server.

        Parameters
        ------------
        host: str
            The host address to connect to.
        port: int
            The port to connect to.
        rest_uri: str
            The URI to use to connect to the REST server.
        password: str
            The password to authenticate on the server.
        region: str
            The region as a valid discord.py guild.region to associate the :class:`wavelink.node.Node` with.
        identifier: str
            A unique identifier for the :class:`wavelink.node.Node`
        shard_id: Optional[int]
            An optional Shard ID to associate with the :class:`wavelink.node.Node`. Could be None.
        secure: bool
            Whether the websocket should be started with the secure wss protocol.
        heartbeat: Optional[float]
            Send ping message every heartbeat seconds and wait pong response, if pong response is not received then close connection.
        
        Returns
        ---------
        :class:`wavelink.node.Node`
            Returns the initiated Node in a connected state.

        Raises
        --------
        NodeOccupied
            A node with provided identifier already exists.
        """
        await self.bot.wait_until_ready()

        if identifier in self.nodes:
            node = self.nodes[identifier]
            raise NodeOccupied(f'Node with identifier ({identifier}) already exists >> {node.__repr__()}')

        node = Node(host, port, self.shard_count, self.user_id,
                    rest_uri=rest_uri,
                    password=password,
                    region=region,
                    identifier=identifier,
                    shard_id=shard_id,
                    session=self.session,
                    client=self,
                    secure=secure,
                    heartbeat=heartbeat)
        
        await node.connect(bot=self.bot)

        node.available = True
        self.nodes[identifier] = node

        __log__.info(f'CLIENT | New node initiated:: {node.__repr__()} ')
        return node

    async def destroy_node(self, *, identifier: str) -> None:
        """Destroy the node and it's players.

        Parameters
        ------------
        identifier: str
            The identifier belonging to the node you wish to destroy.

        Raises
        --------
        ZeroConnectedNodes
            The provided identifier does not belong to any connected nodes.
        """
        try:
            node = self.nodes[identifier]
        except KeyError:
            raise ZeroConnectedNodes(f'A node with identifier:: {identifier}, does not exist.')

        await node.destroy()

    async def update_handler(self, data) -> None:
        if not data or 't' not in data:
            return

        if data['t'] == 'VOICE_SERVER_UPDATE':
            guild_id = int(data['d']['guild_id'])

            try:
                player = self.players[guild_id]
            except KeyError:
                pass
            else:
                await player._voice_server_update(data['d'])

        elif data['t'] == 'VOICE_STATE_UPDATE':
            if int(data['d']['user_id']) != int(self.user_id):
                return

            guild_id = int(data['d']['guild_id'])
            try:
                player = self.players[guild_id]
            except KeyError:
                pass
            else:
                await player._voice_state_update(data['d'])
