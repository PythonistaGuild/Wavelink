.. currentmodule:: wavelink


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

.. attributeable:: Filter

.. autoclass:: Filter
    :members:

.. attributeable:: Equalizer

.. autoclass:: Equalizer
    :members:

.. attributeable:: Karaoke

.. autoclass:: Karaoke
    :members:

.. attributeable:: Timescale

.. autoclass:: Timescale
    :members:

.. attributeable:: Tremolo

.. autoclass:: Tremolo
    :members:

.. attributeable:: Vibrato

.. autoclass:: Vibrato
    :members:

.. attributeable:: Rotation

.. autoclass:: Rotation
    :members:

.. attributeable:: Distortion

.. autoclass:: Distortion
    :members:

.. attributeable:: ChannelMix

.. autoclass:: ChannelMix
    :members:

.. attributeable:: LowPass

.. autoclass:: LowPass
    :members:


Exceptions
----------

.. py:exception:: WavelinkException
.. py:exception:: AuthorizationFailed
.. py:exception:: InvalidNode
.. py:exception:: InvalidLavalinkVersion
.. py:exception:: InvalidLavalinkResponse
.. py:exception:: NoTracksError
.. py:exception:: QueueEmpty
