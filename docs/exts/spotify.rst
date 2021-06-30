.. currentmodule:: wavelink.ext.spotify


Spotify Extension
=================
The Spotify extension is a QoL extension that helps in searching for and queueing tracks from Spotify URL's or ID's.
To get started create a SpotifyClient and pass in your credentials. You then pass this to your Node(s). An example:

.. code-block:: python3

    import wavelink
    from wavelink.ext import spotify


    async def create_nodes(...):
        await wavelink.NodePool.create_node(...,
                                            spotify_client=spotify.SpotifyClient(client_id=..., client_secret=...))


Once your Node has a SpotifyClient attached, you can use `await spotify.SpotifyTrack.search(query=SPOTIFY_URL)` to search
for an appropriate YouTube Track.


Recipes
~~~~~~~

**Searching for a singular track:**

.. code-block:: python3

    # If an ID is passed you must provide a spotify.SpotifySearchType
    # In this case type=spotify.SpotifySearchType.track
    # This is not needed with full URL's

    track = await spotify.SpotifyTrack.search(query="SPOTIFY_TRACK_URL_OR_ID", return_first=True)



**Searching for an album (Flattened to a list):**

.. code-block:: python3

    # If an ID is passed you must provide a spotify.SpotifySearchType
    # In this case type=spotify.SpotifySearchType.album
    # This is not needed with full URL's

    tracks = await spotify.SpotifyTrack.search(query="SPOTIFY_ALBUM_URL_OR_ID")


**Searching for an album (As an async iterator):**

.. code-block:: python3

    async for track in spotify.SpotifyTrack.iterator(query="SPOTIFY_ALBUM_URL_OR_ID", type=spotify.SpotifySearchType.album)
        print(track)


**Searching for a playlist (With PartialTrack's):**

.. code-block:: python3

    # Partial tracks makes queueing large playlists or albums super fast...
    # Partial tracks only have limited information until they are played...

    async for partial in spotify.SpotifyTrack.iterator(query="SPOTIFY_PLAYLIST_URL_OR_ID", partial_tracks=True):
        player.queue.put(partial)


**Decoding a Spotify URL:**

.. code-block:: python3

    # Useful for determining the type of search and the ID...
    # If the URL decoded is an unusable type e.g artist, spotify.SpotifySearchType.unusable will be returned...
    # If the URL is not a valid Spotify URL, None is returned.

    decoded = spotify.decode_url("SPOTIFY_URL")
    if decoded is not None:
        print(decoded['type'], decoded['id'])


Reference
~~~~~~~~~

.. autofunction:: decode_url

.. autoclass:: SpotifyClient
    :members:

.. autoclass:: SpotifySearchType
    :members:

.. autoclass:: SpotifyTrack
    :members:

.. autoexception:: SpotifyRequestError
    :members:
