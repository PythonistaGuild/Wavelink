.. currentmodule:: wavelink


API Reference
-------------
The wavelink API Reference.

This section outlines the API and all it's components within wavelink.

Wavelink is a robust and powerful Lavalink wrapper for Discord.py. Featuring,
a fully asynchronous API that's intuitive and easy to use with built in Spotify Support, Node Pool Balancing,
advanced Queues, autoplay feature and looping features built in.

Event Reference
---------------

WaveLink Events are events dispatched when certain events happen in Lavalink and Wavelink.
All events must be coroutines.

Events are dispatched via discord.py and as such can be used with listener syntax.
All Track Events receive the :class:`payloads.TrackEventPayload` payload.

**For example:**

An event listener in a cog...

.. code-block:: python3

    @commands.Cog.listener()
    async def on_wavelink_node_ready(node: Node) -> None:
        print(f"Node {node.id} is ready!")


.. function:: on_wavelink_node_ready(node: Node)

    Called when the Node you are connecting to has initialised and successfully connected to Lavalink.

.. function:: on_wavelink_track_event(payload: TrackEventPayload)

    Called when any Track Event occurs.

.. function:: on_wavelink_track_start(payload: TrackEventPayload)

    Called when a track starts playing.

.. function:: on_wavelink_track_end(payload: TrackEventPayload)

    Called when the current track has finished playing.

.. function:: on_wavelink_websocket_closed(payload: WebsocketClosedPayload)

    Called when the websocket to the voice server is closed.


Payloads
---------
.. attributetable:: TrackEventPayload

.. autoclass:: TrackEventPayload
    :members:

.. attributetable:: WebsocketClosedPayload

.. autoclass:: WebsocketClosedPayload
    :members:


Enums
-----
.. attributetable:: NodeStatus

.. autoclass:: NodeStatus
    :members:

.. attributetable:: TrackSource

.. autoclass:: TrackSource
    :members:

.. attributetable:: LoadType

.. autoclass:: LoadType
    :members:

.. attributetable:: TrackEventType

.. autoclass:: TrackEventType
    :members:

.. attributetable:: DiscordVoiceCloseType

.. autoclass:: DiscordVoiceCloseType
    :members:


Abstract Base Classes
---------------------
.. attributetable:: wavelink.tracks.Playable

.. autoclass:: wavelink.tracks.Playable
    :members:

.. attributetable:: wavelink.tracks.Playlist

.. autoclass:: wavelink.tracks.Playlist
    :members:


NodePool
--------
.. attributetable:: NodePool

.. autoclass:: NodePool
    :members:

Node
----

.. attributetable:: Node

.. autoclass:: Node
    :members:

Tracks
------

Tracks inherit from :class:`Playable`. Not all fields will be available for each track type.

GenericTrack
~~~~~~~~~~~~

.. attributetable:: GenericTrack

.. autoclass:: GenericTrack
    :members:
    :inherited-members:

YouTubeTrack
~~~~~~~~~~~~

.. attributetable:: YouTubeTrack

.. autoclass:: YouTubeTrack
    :members:
    :inherited-members:

YouTubeMusicTrack
~~~~~~~~~~~~~~~~~

.. attributetable:: YouTubeMusicTrack

.. autoclass:: YouTubeMusicTrack
    :members:
    :inherited-members:

SoundCloudTrack
~~~~~~~~~~~~~~~

.. attributetable:: SoundCloudTrack

.. autoclass:: SoundCloudTrack
    :members:
    :inherited-members:

YouTubePlaylist
~~~~~~~~~~~~~~~

.. attributetable:: YouTubePlaylist

.. autoclass:: YouTubePlaylist
    :members:
    :inherited-members:


Player
------

.. attributetable:: Player

.. autoclass:: Player
    :members:


Queues
------

.. attributetable:: BaseQueue

.. autoclass:: BaseQueue
    :members:

.. attributetable:: Queue

.. autoclass:: Queue
    :members:

Filters
-------

.. attributetable:: Filter

.. autoclass:: Filter
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


Exceptions
----------

.. exception_hierarchy::

    - :exc:`~WavelinkException`
        - :exc:`~AuthorizationFailed`
        - :exc:`~InvalidNode`
        - :exc:`~InvalidLavalinkVersion`
        - :exc:`~InvalidLavalinkResponse`
        - :exc:`~NoTracksError`
        - :exc:`~QueueEmpty`
        - :exc:`~InvalidChannelStateError`
            - :exc:`~InvalidChannelPermissions`


.. py:exception:: WavelinkException

    Base wavelink exception.

.. py:exception:: AuthorizationFailed

    Exception raised when password authorization failed for this Lavalink node.

.. py:exception:: InvalidNode

.. py:exception:: InvalidLavalinkVersion

    Exception raised when you try to use wavelink 2 with a Lavalink version under 3.7.

.. py:exception:: InvalidLavalinkResponse

    Exception raised when wavelink receives an invalid response from Lavalink.

    status: :class:`int` | :class:`None`
        The status code. Could be :class:`None`.

.. py:exception:: NoTracksError

    Exception raised when no tracks could be found.

.. py:exception:: QueueEmpty

    Exception raised when you try to retrieve from an empty queue.

.. py:exception:: InvalidChannelStateError

    Base exception raised when an error occurs trying to connect to a :class:`discord.VoiceChannel`.

.. py:exception:: InvalidChannelPermissions

    Exception raised when the client does not have correct permissions to join the channel.

    Could also be raised when there are too many users already in a user limited channel.
