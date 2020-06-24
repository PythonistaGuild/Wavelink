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
import inspect
import logging
from discord.ext import commands
from typing import Optional, Union
from urllib.parse import quote

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
    shards: int
        The number of Shards.
    rest_uri: str
        The rest server address the node is connecte to.
    uid: int
        The user id.
    password: str
        The Node's password
    region: str
        The region provided to the node on connection.
    identifier: str
        The unique indentifier associated with the node.
    secure: bool
        Wether the web-sockect connection is secure.
    shard_id: Optional[int]
        The shard id, defuault value is None.
    heartbeat: float
        Duration between pings, helps keep WS stable. Defaults to None to disable.
    resume_session: bool
            If True then Lavalink server will continue to play music until bot reconnects or
            till `resume_timeout` and then shuts-down all Players. Defaults to False.
    resume_timeout: float
        Has no effect unless resume_session is True.
    resume_key: str
        Has no effect unless resume_session is True. Defaults to a secret AlphaNumeric key that is 32 characters long
    payload_timeout: float
        Has no effect unless resume_session is True. Amount of time a send request should be queued.
    force_send_queue: bool
        Send the waiting WS requests on recconect regardless of Lavalink session resume request result.
        Defaults to False.
    players: Dict[int, Player]
        A dictionary with guild id as key and the respective guild's Player as value. Please use :func:`Node.get_player` instead.
    session: aiohttp.ClientSession
        The aiohttp session.
    hook: Callable
        A callable object. use :func:`Node.set_hook`
    available: bool
        Wether the Node is in use or not. Use is_available instead.
    stats: Optional[:class:`Stats`]
        The Node's stats, sent by the server. Could be None.
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
                 heartbeat: float,
                 resume_session: bool,
                 resume_timeout: float,
                 resume_key: str,
                 force_send_queue: bool,
                 payload_timeout: float
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
        self.force_send_queue = force_send_queue
        self.resume_session = resume_session
        self.resume_timeout = resume_timeout
        self.resume_key = resume_key
        self.payload_timeout = payload_timeout
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
                                    force_send_queue=self.force_send_queue,
                                    resume_session=self.resume_session,
                                    resume_timeout=self.resume_timeout,
                                    resume_key=self.resume_key,
                                    payload_timeout=self.payload_timeout)
        await self._websocket._connect()

        __log__.info(f'NODE | {self.identifier} connected:: {self.__repr__()}')

    async def get_tracks(self, query: str) -> Union[list, TrackPlaylist, None]:
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
            A list of or TrackPlaylist instance of :class:`wavelink.player.Track` objects.
            This could be None if no tracks were found.
        """
        async with self.session.get(f'{self.rest_uri}/loadtracks?identifier={quote(query)}',
                                    headers={'Authorization': self.password}) as resp:
            data = await resp.json()

            if not data['tracks']:
                __log__.info(f'REST | No tracks with query:: <{query}> found.')
                return None

            if data['playlistInfo']:
                return TrackPlaylist(data=data)

            tracks = []
            for track in data['tracks']:
                tracks.append(Track(id_=track['track'], info=track['info']))

            __log__.debug(f'REST | Found <{len(tracks)}> tracks with query:: <{query}> ({self.__repr__()})')

            return tracks

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
        async with self.session.get(f'{self.rest_uri}/decodetrack?track={identifier}',
                                    headers={'Authorization': self.password}) as resp:
            data = await resp.json()

            if not resp.status == 200:
                raise BuildTrackError(f'Failed to build track. Status: {data["status"]}, Error: {data["error"]}.'
                                      f'Check the identfier is correct and try again.')

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

    async def destroy(self) -> None:
        """Destroy the node and all it's players."""
        players = self.players.copy()

        for player in players.values():
            await player.destroy()

        try:
            self._websocket._task.cancel()
        except Exception:
            pass

        del self._client.nodes[self.identifier]

    async def _send(self, **data) -> None:
        __log__.debug(f'NODE | Sending payload:: <{data}> ({self.__repr__()})')
        await self._websocket._send(**data)
