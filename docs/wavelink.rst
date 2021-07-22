.. currentmodule:: wavelink


Event Reference
---------------

WaveLink Events are events dispatched when certain events happen in Lavalink and Wavelink.
All events must be coroutines.

Events are dispatched via discord.py and as such can be used with listener syntax.

**For example:**

An event listener in a cog...

.. code-block:: python3

    @commands.Cog.listener()
    async def on_wavelink_node_ready(node: Node):
        print(f"Node {node.id} is ready!")


.. function:: on_wavelink_node_ready(node: Node)

    Called when the Node you are connecting to has initialised and successfully connected to Lavalink.

.. function:: on_wavelink_websocket_closed(player: Player, reason, code)

    Called when the Node websocket has been closed by Lavalink.

.. function:: on_wavelink_track_start(player: Player, track: Track)

    Called when a track starts playing.

.. function:: on_wavelink_track_end(player: player, track: Track, reason)

    Called when the current track has finished playing.

.. function:: on_wavelink_track_exception(player: Player, track: Track, error)

    Called when a TrackException occurs in Lavalink.

.. function:: on_wavelink_track_stuck(player: Player, track: Track, threshold)

    Called when a TrackStuck occurs in Lavalink.


Abstract Base Classes
---------------------

.. autoclass:: wavelink.abc.Playable
    :members:

.. autoclass:: wavelink.abc.Searchable
    :members:

.. autoclass:: wavelink.abc.Playlist
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

Track
~~~~~

.. attributetable:: Track

.. autoclass:: Track
    :members:

SearchableTrack
~~~~~~~~~~~~~~~

.. attributetable:: SearchableTrack

.. autoclass:: SearchableTrack
    :members:

YouTubeTrack
~~~~~~~~~~~~

.. attributetable:: YouTubeTrack

.. autoclass:: YouTubeTrack
    :members:

YouTubeMusicTrack
~~~~~~~~~~~~~~~~~

.. attributetable:: YouTubeMusicTrack

.. autoclass:: YouTubeMusicTrack
    :members:

SoundCloudTrack
~~~~~~~~~~~~~~~

.. attributetable:: SoundCloudTrack

.. autoclass:: SoundCloudTrack
    :members:

YouTubePlaylist
~~~~~~~~~~~~~~~

.. attributetable:: YouTubePlaylist

.. autoclass:: YouTubePlaylist
    :members:

PartialTrack
~~~~~~~~~~~~

.. attributetable:: PartialTrack

.. autoclass:: PartialTrack

Player
------

.. attributetable:: Player

.. autoclass:: Player
    :members:

Queues
------

.. attributetable:: Queue

.. autoclass:: Queue
    :members:

.. attributetable:: WaitQueue

.. autoclass:: WaitQueue
    :members:

Exceptions
----------

.. py:exception:: WavelinkError
.. py:exception:: AuthorizationFailure
.. py:exception:: LavalinkException
.. py:exception:: LoadTrackError
.. py:exception:: BuildTrackError
.. py:exception:: NodeOccupied
.. py:exception:: InvalidIDProvided
.. py:exception:: ZeroConnectedNodes
.. py:exception:: NoMatchingNode
.. py:exception:: QueueException
.. py:exception:: QueueFull
.. py:exception:: QueueEmpty