"""MIT License

Copyright (c) 2019 EvieePy(MysterialPy)

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
from typing import Optional, Union

from .errors import *
from .player import Player
from .node import Node


__log__ = logging.getLogger(__name__)


class Client:

    def __init__(self, bot: Union[commands.Bot, commands.AutoShardedBot]):
        self.bot = bot
        self.loop = bot.loop or asyncio.get_event_loop()
        self.session = aiohttp.ClientSession(loop=self.loop)

        self.nodes = {}

        bot.add_listener(self.update_handler, 'on_socket_response')

    @property
    def shard_count(self) -> int:
        return self.bot.shard_count or 1

    @property
    def user_id(self) -> int:
        return self.bot.user.id

    @property
    def players(self) -> dict:
        return self._get_players()

    async def get_tracks(self, query: str) -> Optional[list]:
        node = self.get_best_node()

        return await node.get_tracks(query)

    def _get_players(self) -> dict:
        players = []

        for node in self.nodes.values():
            players.extend(node.players.values())

        return {player.guild_id: player for player in players}

    def get_node(self, identifier: str) -> Optional[Node]:
        return self.nodes.get(identifier, None)

    def get_best_node(self) -> Node:
        return sorted(self.nodes.values(), key=lambda n: len(n.players))[0]

    def get_node_by_region(self, region: str) -> Optional[Node]:
        nodes = [n for n in self.nodes.values() if n.region.lower() == region.lower()]
        if not nodes:
            return None

        return sorted(nodes, key=lambda n: len(n.players))[0]

    def get_node_by_shard(self, shard_id: int) -> Optional[Node]:
        nodes = [n for n in self.nodes.values() if n.shard_id == shard_id]
        if not nodes:
            return None

        return sorted(nodes, key=lambda n: len(n.players))[0]

    def get_player(self, guild_id: int) -> Optional[Player]:
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

        shard_options = []
        region_options = []
        nodes = self.nodes.values()

        for node in nodes:
            if node.shard_id == guild.shard_id:
                shard_options.append(node)
            elif node.region.lower() == guild.region.lower():
                region_options.append(node)

        if not shard_options or region_options:
            node = sorted(nodes, key=lambda n: len(n.players))[0]
            player = Player(self.bot, guild_id, node)
            node.players[guild_id] = player

            return player

        best = [n for n in shard_options if n in region_options]
        if best:
            node = sorted(best, key=lambda _: len(_.players))[0]
        elif shard_options:
            node = sorted(shard_options, key=lambda n: len(n.players))[0]
        else:
            node = sorted(region_options, key=lambda n: len(n.players))[0]

        player = Player(self.bot, guild_id, node)
        node.players[guild_id] = player

        return player

    async def initiate_node(self, host: str, port: int, *, rest_uri: str, password: str, region: str, identifier: str,
                            shard_id: int=None) -> Node:
        if identifier in self.nodes:
            node = self.nodes[identifier]
            raise NodeOccupied(f'Node with identifier ({identifier}) already exists >> {node.__repr__()}')

        node = Node(host, port, self.shard_count, self.user_id,
                    rest_uri=rest_uri,
                    password=password,
                    region=region,
                    identifier=identifier,
                    shard_id=shard_id,
                    session=self.session)

        await node.connect(bot=self.bot)
        self.nodes[identifier] = node

        __log__.info(f'CLIENT | New node initiated:: {node.__repr__()} ')
        return node

        # todo Connection logic, Unload Logic

    async def update_handler(self, data):
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
        else:
            return
