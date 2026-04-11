.. currentmodule:: wavelink


API Reference
-------------
The wavelink 3 API Reference.
This section outlines the API and all it's components within wavelink.


Event Reference
---------------

WaveLink Events are events dispatched when certain events happen in Lavalink and Wavelink.
All events must be coroutines.

Events are dispatched via discord.py and as such can be used with discord.py listener syntax.
All Track Events receive the appropriate payload.


**For example:**

An event listener in a cog.

.. code-block:: python3

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload) -> None:
        print(f"Node {payload.node!r} is ready!")


.. function:: on_wavelink_node_ready(payload: wavelink.NodeReadyEventPayload)

    Called when the Node you are connecting to has initialised and successfully connected to Lavalink.
    This event can be called many times throughout your bots lifetime, as it will be called when Wavelink successfully
    reconnects to your node in the event of a disconnect.

.. function:: on_wavelink_node_disconnected(payload: wavelink.NodeDisconnectedEventPayload)

    Called when a Node has disconnected/lost connection to wavelink. **This is NOT** the same as a node being closed.
    This event will however be called directly before the :func:`on_wavelink_node_closed` event.

    The default behaviour is for wavelink to attempt to reconnect a disconnected Node. This event can change that
    behaviour. If you want to close this node completely see: :meth:`Node.close`

    This event can be used to manage currrently connected players to this Node.
    See: :meth:`Player.switch_node`

    .. versionadded:: 3.5.0

.. function:: on_wavelink_stats_update(payload: wavelink.StatsEventPayload)

    Called when the ``stats`` OP is received by Lavalink.

.. function:: on_wavelink_player_update(payload: wavelink.PlayerUpdateEventPayload)

    Called when the ``playerUpdate`` OP is received from Lavalink.
    This event contains information about a specific connected player on the node.

.. function:: on_wavelink_track_start(payload: wavelink.TrackStartEventPayload)

    Called when a track starts playing.

    .. note::

        It is preferred to use this method when sending feedback about the now playing track etc.

.. function:: on_wavelink_track_end(payload: wavelink.TrackEndEventPayload)

    Called when the current track has finished playing.

    .. warning::

        If you are using AutoPlay, please make sure you take this into consideration when using this event.
        See: :func:`on_wavelink_track_start` for an event for performing logic when a new track starts playing.

.. function:: on_wavelink_track_exception(payload: wavelink.TrackExceptionEventPayload)

    Called when an exception occurs while playing a track.

.. function:: on_wavelink_track_stuck(payload: wavelink.TrackStuckEventPayload)

    Called when a track gets stuck while playing.

.. function:: on_wavelink_websocket_closed(payload: wavelink.WebsocketClosedEventPayload)

    Called when the websocket to the voice server is closed.

.. function:: on_wavelink_node_closed(node: wavelink.Node, disconnected: list[wavelink.Player])

    Called when a node has been closed and cleaned-up. The second parameter ``disconnected`` is a list of
    :class:`wavelink.Player` that were connected on this Node and are now disconnected.

.. function:: on_wavelink_extra_event(payload: wavelink.ExtraEventPayload)

    Called when an ``Unknown`` and/or ``Unhandled`` event is recevied via Lavalink. This is most likely due to
    a plugin like SponsorBlock sending custom event data. The payload includes the raw data sent from Lavalink.

    .. note::

        Please see the documentation for your Lavalink plugins to determine what data they send.
    

    .. versionadded:: 3.1.0

.. function:: on_wavelink_inactive_player(player: wavelink.Player)

    Triggered when the :attr:`~wavelink.Player.inactive_timeout` countdown expires for the specific :class:`~wavelink.Player`.


    - See: :attr:`~wavelink.Player.inactive_timeout`
    - See: :class:`~wavelink.Node` for setting a default on all players.


    Examples
    --------

        **Basic Usage:**

        .. code:: python3

            @commands.Cog.listener()
            async def on_wavelink_inactive_player(self, player: wavelink.Player) -> None:
                await player.channel.send(f"The player has been inactive for `{player.inactive_timeout}` seconds. Goodbye!")
                await player.disconnect()


    .. versionadded:: 3.2.0


Types
-----
.. attributetable:: Search

.. py:class:: Search

    A type hint used when searching tracks. Used in :meth:`Playable.search` and :meth:`Pool.fetch_tracks`

    **Example:**

    .. code:: python3

        tracks: wavelink.Search = await wavelink.Playable.search("Ocean Drive")

.. attributetable:: PlayerBasicState

.. autoclass:: PlayerBasicState



Payloads
---------
.. attributetable:: NodeReadyEventPayload

.. autoclass:: NodeReadyEventPayload
    :members:

.. attributetable:: NodeDisconnectedEventPayload

.. autoclass:: NodeDisconnectedEventPayload
    :members:

.. attributetable:: TrackStartEventPayload

.. autoclass:: TrackStartEventPayload
    :members:

.. attributetable:: TrackEndEventPayload

.. autoclass:: TrackEndEventPayload
    :members:

.. attributetable:: TrackExceptionEventPayload

.. autoclass:: TrackExceptionEventPayload
    :members:

.. attributetable:: TrackStuckEventPayload

.. autoclass:: TrackStuckEventPayload
    :members:

.. attributetable:: WebsocketClosedEventPayload

.. autoclass:: WebsocketClosedEventPayload
    :members:

.. attributetable:: PlayerUpdateEventPayload

.. autoclass:: PlayerUpdateEventPayload
    :members:

.. attributetable:: StatsEventPayload

.. autoclass:: StatsEventPayload
    :members:

.. attributetable:: StatsEventMemory

.. autoclass:: StatsEventMemory
    :members:

.. attributetable:: StatsEventCPU

.. autoclass:: StatsEventCPU
    :members:

.. attributetable:: StatsEventFrames

.. autoclass:: StatsEventFrames
    :members:

.. attributetable:: StatsResponsePayload

.. autoclass:: StatsResponsePayload
    :members:

.. attributetable:: PlayerStatePayload

.. autoclass:: PlayerStatePayload
    :members:

.. attributetable:: VoiceStatePayload

.. autoclass:: VoiceStatePayload
    :members:

.. attributetable:: PlayerResponsePayload

.. autoclass:: PlayerResponsePayload
    :members:

.. attributetable:: GitResponsePayload

.. autoclass:: GitResponsePayload
    :members:

.. attributetable:: VersionResponsePayload

.. autoclass:: VersionResponsePayload
    :members:

.. attributetable:: PluginResponsePayload

.. autoclass:: PluginResponsePayload
    :members:

.. attributetable:: InfoResponsePayload

.. autoclass:: InfoResponsePayload
    :members:

.. attributetable:: ExtraEventPayload

.. autoclass:: ExtraEventPayload
    :members:


Enums
-----
.. attributetable:: NodeStatus

.. autoclass:: NodeStatus
    :members:

.. attributetable:: TrackSource

.. autoclass:: TrackSource
    :members:

.. attributetable:: DiscordVoiceCloseType

.. autoclass:: DiscordVoiceCloseType
    :members:

.. attributetable:: AutoPlayMode

.. autoclass:: AutoPlayMode
    :members:

.. attributetable:: QueueMode

.. autoclass:: QueueMode
    :members:


Pool
--------
.. attributetable:: Pool

.. autoclass:: Pool
    :members:

Node
----

.. attributetable:: Node

.. autoclass:: Node
    :members:

Tracks
------

Tracks in wavelink 3 have been simplified. Please read the docs for :class:`Playable`.
Additionally the following data classes are provided on every :class:`Playable`.

.. attributetable:: Artist

.. autoclass:: Artist
    :members:

.. attributetable:: Album

.. autoclass:: Album
    :members:


Playable
~~~~~~~~~~~~

.. attributetable:: Playable

.. autoclass:: Playable
    :members:

Playlists
~~~~~~~~~~~~~~~

.. attributetable:: Playlist

.. autoclass:: Playlist
    :members:

.. attributetable:: PlaylistInfo

.. autoclass:: PlaylistInfo
    :members:


Player
------

.. attributetable:: Player

.. autoclass:: Player
    :members:
    :exclude-members: on_voice_state_update, on_voice_server_update


Queue
------

.. attributetable:: Queue

.. autoclass:: Queue
    :members:
    :inherited-members:


Filters
-------

.. attributetable:: Filters

.. autoclass:: Filters
    :members:

.. attributetable:: Equalizer

.. autoclass:: Equalizer
    :members:

.. attributetable:: Karaoke

.. autoclass:: Karaoke
    :members:

.. attributetable:: Timescale

.. autoclass:: Timescale
    :members:

.. attributetable:: Tremolo

.. autoclass:: Tremolo
    :members:

.. attributetable:: Vibrato

.. autoclass:: Vibrato
    :members:

.. attributetable:: Rotation

.. autoclass:: Rotation
    :members:

.. attributetable:: Distortion

.. autoclass:: Distortion
    :members:

.. attributetable:: ChannelMix

.. autoclass:: ChannelMix
    :members:

.. attributetable:: LowPass

.. autoclass:: LowPass
    :members:

.. attributetable:: PluginFilters

.. autoclass:: PluginFilters
    :members:


Utils
-----

.. attributetable:: ExtrasNamespace

.. autoclass:: ExtrasNamespace

    

Exceptions
----------

.. exception_hierarchy::

    - :exc:`~WavelinkException`
        - :exc:`~NodeException`
        - :exc:`~InvalidClientException`
        - :exc:`~AuthorizationFailedException`
        - :exc:`~InvalidNodeException`
        - :exc:`~LavalinkException`
        - :exc:`~LavalinkLoadException`
        - :exc:`~InvalidChannelStateException`
        - :exc:`~ChannelTimeoutException`
        - :exc:`~QueueEmpty`


.. py:exception:: WavelinkException

    Base wavelink Exception class.
    All wavelink exceptions derive from this exception.

.. py:exception:: NodeException

    Error raised when an Unknown or Generic error occurs on a Node.

.. py:exception:: InvalidClientException

    Exception raised when an invalid :class:`discord.Client`
    is provided while connecting a :class:`wavelink.Node`.

.. py:exception:: AuthorizationFailedException

    Exception raised when Lavalink fails to authenticate a :class:`~wavelink.Node`, with the provided password.

.. py:exception:: InvalidNodeException

    Exception raised when a :class:`Node` is tried to be retrieved from the
    :class:`Pool` without existing, or the ``Pool`` is empty.

    This exception is also raised when providing an invalid node to :meth:`Player.switch_node`.

.. py:exception:: LavalinkException

    Exception raised when Lavalink returns an invalid response.

    Attributes
    ----------
    status: int
        The response status code.
    reason: str | None
        The response reason. Could be ``None`` if no reason was provided.

.. py:exception:: LavalinkLoadException

    Exception raised when loading tracks failed via Lavalink.

.. py:exception:: InvalidChannelStateException

    Exception raised when a :class:`~wavelink.Player` tries to connect to an invalid channel or
    has invalid permissions to use this channel.

.. py:exception:: ChannelTimeoutException

    Exception raised when connecting to a voice channel times out.

.. py:exception:: QueueEmpty

    Exception raised when you try to retrieve from an empty queue via ``.get()``.