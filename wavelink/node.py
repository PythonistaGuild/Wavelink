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
import asyncio
import inspect
import json
import logging
from discord.ext import commands
from typing import Any, Callable, Dict, Optional, Union
from urllib.parse import quote

from .backoff import ExponentialBackoff
from .errors import *
from .player import Player, Track, TrackPlaylist
from .websocket import WebSocket


__log__ = logging.getLogger(__name__)


class Node:
    """A WaveLink Node instance.

    .. warning::
        You should not create :class:`Node` objects manually. Instead you should use, :func:`Client.initiate_node`.

    Attributes
    ------------
    host: str
        The host address the node is connected to.
    port: int
        The port the node is connected to.
    rest_uri: str
        The rest server address the node is connecte to.
    region: str
        The region provided to the node on connection.
    identifier: str
        The unique indentifier associated with the node.
    """

    def __init__(self, host: str,
                 port: int,
                 shards: int,
                 user_id: int,
                 *,
                 client,
                 session,
                 rest_uri: str,
                 password: str,
                 region: str,
                 identifier: str,
                 shard_id: int = None,
                 secure: bool = False,
                 heartbeat: float = None,
                 dumps: Callable[[Dict[str, Any]], Union[str, bytes]] = json.dumps
                 ):

        self.host = host
        self.port = port
        self.rest_uri = rest_uri
        self.shards = shards
        self.uid = user_id
        self.password = password
        self.region = region
        self.identifier = identifier
        self.secure = secure
        self.heartbeat = heartbeat

        self._dumps = dumps

        self.shard_id = shard_id

        self.players = {}

        self.session = session
        self._websocket = None
        self._client = client

        self.hook = None
        self.available = True

        self.stats = None

    def __repr__(self):
        return f'{self.identifier} | {self.region} | (Shard: {self.shard_id})'

    @property
    def is_available(self) -> bool:
        """Return whether the Node is available or not."""
        return self._websocket.is_connected and self.available

    def close(self) -> None:
        """Close the node and make it unavailable."""
        self.available = False

    def open(self) -> None:
        """Open the node and make it available."""
        self.available = True

    @property
    def penalty(self) -> float:
        """Returns the load-balancing penalty for this node."""
        if not self.available or not self.stats:
            return 9e30

        return self.stats.penalty.total

    async def connect(self, bot: Union[commands.Bot, commands.AutoShardedBot]) -> None:
        self._websocket = WebSocket(node=self,
                                    host=self.host,
                                    port=self.port,
                                    password=self.password,
                                    shard_count=self.shards,
                                    user_id=self.uid,
                                    secure=self.secure,
                                    dumps=self._dumps)
        await self._websocket._connect()

        __log__.info(f'NODE | {self.identifier} connected:: {self.__repr__()}')

    async def get_tracks(self, query: str, *, retry_on_failure: bool = True) -> Union[list, TrackPlaylist, None]:
        """|coro|

        Search for and return a list of Tracks for the given query.

        Parameters
        ------------
        query: str
            The query to use to search for tracks. If a valid URL is not provided, it's best to default to
            "ytsearch:query", which allows the REST server to search YouTube for Tracks.
        retry_on_failure: bool
            Bool indicating whether the Node should retry upto a maximum of 5 attempts on load failure.
            If this is set to True, the Node will attempt to retrieve tracks with an exponential backoff delay
            between retries. Defaults to True.

        Returns
        ---------
        Union[list, TrackPlaylist, None]:
            A list of or TrackPlaylist instance of :class:`wavelink.player.Track` objects.
            This could be None if no tracks were found.
        """
        backoff = ExponentialBackoff(base=1)

        for attempt in range(5):
            async with self.session.get(f'{self.rest_uri}/loadtracks?identifier={quote(query)}',
                                        headers={'Authorization': self.password}) as resp:

                if not resp.status == 200 and retry_on_failure:
                    retry = backoff.delay()

                    __log__.info(f'REST | Status code ({resp.status}) while retrieving tracks. '
                                 f'Attempt {attempt} of 5, retrying in {retry} seconds.')

                    await asyncio.sleep(retry)
                    continue

                elif not resp.status == 200 and not retry_on_failure:
                    __log__.info(f'REST | Status code ({resp.status}) while retrieving tracks. Not retrying.')
                    return

                data = await resp.json()

                if not data['tracks']:
                    __log__.info(f'REST | No tracks with query <{query}> found.')
                    return None

                if data['playlistInfo']:
                    return TrackPlaylist(data=data)

                tracks = []
                for track in data['tracks']:
                    tracks.append(Track(id_=track['track'], info=track['info']))

                __log__.debug(f'REST | Found <{len(tracks)}> tracks with query <{query}> ({self.__repr__()})')

                return tracks

        __log__.warning('REST | Failure to load tracks after 5 attempts.')

    async def build_track(self, identifier: str) -> Track:
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
        BuildTrackError
            Decoding and building the track failed.
        """
        async with self.session.get(f'{self.rest_uri}/decodetrack?',
                                    headers={'Authorization': self.password},
                                    params={'track': identifier}) as resp:
            data = await resp.json()

            if not resp.status == 200:
                raise BuildTrackError(f'Failed to build track. Status: {data["status"]}, Error: {data["error"]}.'
                                      f'Check the identifier is correct and try again.')

            track = Track(id_=identifier, info=data)
            return track

    def get_player(self, guild_id: int) -> Optional[Player]:
        """Retrieve a player object associated with the Node.

        Parameters
        ------------
        guild_id: int
            The guild id belonging to the player.

        Returns
        ---------
        Optional[Player]
        """
        return self.players.get(guild_id, None)

    async def on_event(self, event) -> None:
        """Function which dispatches events when triggered on the Node."""
        __log__.info(f'NODE | Event dispatched:: <{str(event)}> ({self.__repr__()})')
        await event.player.hook(event)

        if not self.hook:
            return

        if inspect.iscoroutinefunction(self.hook):
            await self.hook(event)
        else:
            self.hook(event)

    def set_hook(self, func) -> None:
        """Set the Node Event Hook.

        The event hook will be dispatched when an Event occurs.
        Maybe a coroutine.

        Raises
        --------
        WavelinkException
            The hook provided was not a valid callable.
        """
        if not callable(func):
            raise WavelinkException('Node hook must be a callable.')

        self.hook = func

    async def destroy(self, *, force: bool = False) -> None:
        """Destroy the node and all it's players."""
        players = self.players.copy()

        for player in players.values():
            await player.destroy(force=force)

        try:
            self._websocket._task.cancel()
        except Exception:
            pass

        del self._client.nodes[self.identifier]

    async def _send(self, **data) -> None:
        __log__.debug(f'NODE | Sending payload:: <{data}> ({self.__repr__()})')
        await self._websocket._send(**data)
