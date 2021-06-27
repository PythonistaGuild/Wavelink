.. currentmodule:: wavelink.ext.spotify


Spotify Extension
=================
The Spotify extension is a QoL extension that helps in searching for and queueing tracks from Spotify URL's or ID's.
Currently the Spotify extension only supports searching singular tracks, but playlists and albums are coming soon.

To get started create a SpotifyClient and pass in your credentials. You then pass this to your Node(s). An example:

.. code-block:: python3

    import wavelink
    from wavelink.ext import spotify


    async def create_nodes(...):
        await wavelink.NodePool.create_node(...,
                                            spotify_client=spotify.SpotifyClient(client_id=..., client_secret=...))


Once your Node has a SpotifyClient attached, you can use `await spotify.SpotifyTrack.search(query=SPOTIFY_URL)` to search
for an appropriate YouTube Track.


Reference
=========

.. autoclass:: SpotifyClient
    :members:

.. autoclass:: SpotifySearchType
    :members:

.. autoclass:: SpotifyTrack
    :members:

.. autoexception:: SpotifyRequestError
    :members:
