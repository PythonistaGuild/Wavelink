Recipes and Examples
=============================
Below are common short examples and recipes for use with WaveLink 1.0.
This is not an exhaustive list, for more detailed examples, see: `GitHub Examples <https://github.com/PythonistaGuild/Wavelink/tree/1.0/examples>`_


Listening to Events
-------------------
WaveLink 1.0 makes use of the built in event dispatcher of Discord.py.
This means you can listen to WaveLink events the same way you listen to discord.py events.

*All WaveLink events are prefixed with `on_wavelink_`*


**Outside of a Cog:**

.. code:: python3

    @bot.event
    async def on_wavelink_node_ready(node: Node):
        print(f"Node {node.id} is ready!")


**Inside a Cog:**

.. code:: python3

    @commands.Cog.listener()
    async def on_wavelink_node_ready(node: Node):
        print(f"Node {node.id} is ready!")



Creating and using Nodes
------------------------
Wavelink 1.0 has a more intuitive way of creating and storing Nodes.
Nodes are now stored at class level in a `NodePool`. Once a node has been created, you can access that node anywhere that
wavelink can be imported.


**Creating a Node:**

.. code:: python3

    # Creating a node is as simple as this...
    # The node will be automatically stored to the global NodePool...
    # You can create as many nodes as you like, most people only need 1...

    await wavelink.NodePool.create_node(bot=bot,
                                        host='0.0.0.0',
                                        port=2333,
                                        password='YOUR_LAVALINK_PASSWORD')


**Accessing the best Node from the NodePool:**

.. code:: python3

    # Accessing a Node is easy...
    node = wavelink.NodePool.get_node()


**Accessing a node by identifier from the NodePool:**

.. code:: python3

    node = wavelink.NodePool.get_node(identifier="MY_NODE_ID")


**Accessing a list of Players a Node contains:**

.. code:: python3

    node = wavelink.NodePool.get_node()
    print(node.players)


**Attaching Spotify support to a Node:**

.. code:: python3

    from wavelink.ext import spotify


    node = await wavelink.NodePool.create_node(bot=bot,
                                               host='0.0.0.0',
                                               port=2333,
                                               password='YOUR_LAVALINK_PASSWORD',
                                               spotify_client=spotify.SpotifyClient(client_id=..., client_secret=...))


Searching Tracks
----------------
The way you search for tracks in WaveLink 1.0 is different. Below are some common recipes for searching tracks.


**A Simple YouTube search:**

.. code:: python3

    track = await wavelink.YouTubeTrack.search(query="Ocean Drive", return_first=True)


**Returning more than one result:**

.. code:: python3

    tracks = await wavelink.YouTubeTrack.search(query="Ocean Drive")


**SoundCloud search:**

.. code:: python3

    tracks = await wavelink.SoundCloudTrack.search(query=...)


**As a Discord.py converter:**

.. code:: python3

    @commands.command()
    async def play(self, ctx: commands.Context, *, track: wavelink.YouTubeTrack):
        # The track will be the first result from what you searched when invoking the command...
        ...


**Union converter:**

.. code:: python3

    @commands.command()
    async def play(self, ctx: commands.Context, *, track: typing.Union[wavelink.SoundCloudTrack, wavelink.YouTubeTrack]):
        # The track will be the first result from what you searched when invoking the command...
        # If no soundcloud track is found, YouTube will be searched...
        ...


Partial Tracks
--------------
PartialTrack is a new way to search in WaveLink 1.0. Partial tracks are most useful when used together with the Spotify Ext.
A `PartialTrack` allows you to queue a song that will only actually be searched for and result at play time.

This behaviour allows queuing large amounts of tracks without querying the REST API continuously.


**A basic PartialTrack search:**

.. code:: python3

    @commands.command()
    async def play(self, ctx: commands.Context, *, search: str):
        partial = wavelink.PartialTrack(query=search, cls=wavelink.YouTubeTrack)

        track = await ctx.voice_client.play(partial)
        await ctx.send(f'**Now playing:** `{track.title}`')


**PartialTracks' with Spotify:**

.. code-block:: python3

    # Partial tracks makes queueing large playlists or albums super fast...
    # Partial tracks only have limited information until they are played...

    @commands.command()
    async def play(self, ctx: commands.Context, *, spotify_url: str):

        async for partial in spotify.SpotifyTrack.iterator(query=spotify_url, partial_tracks=True):
            player.queue.put(partial)

        ...


Creating Players and VoiceProtocol
----------------------------------
WaveLink 1.0 was reworked to revolve around Discord.py's new VoiceProtocol. What this means is that accessing your `Player` instance,
is easier and more intuitive. Below are some common examples of how to use the new VoiceProtocol with WaveLink.


**A Simple Player:**

.. code:: python3

    import discord
    import wavelink

    from discord.ext import commands


    @commands.command()
    async def connect(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        try:
            channel = channel or ctx.author.channel.voice
        except AttributeError:
            return await ctx.send('No voice channel to connect to. Please either provide one or join one.')

        # vc is short for voice client...
        # Our "vc" will be our wavelink.Player as typehinted below...
        # wavelink.Player is also a VoiceProtocol...

        vc: wavelink.Player = await channel.connect(cls=wavelink.Player)
        return vc


**A custom Player setup:**

.. code:: python3

    import discord
    import wavelink

    from discord.ext import commands


    class Player(wavelink.Player):
        """A Player with a DJ attribute."""

        def __init__(self, dj: discord.Member):
            self.dj = dj


    @commands.command()
    async def connect(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        try:
            channel = channel or ctx.author.channel.voice
        except AttributeError:
            return await ctx.send('No voice channel to connect to. Please either provide one or join one.')

        # vc is short for voice client...
        # Our "vc" will be our Player as type hinted below...
        # Player is also a VoiceProtocol...

        player = Player(dj=ctx.author)
        vc: Player = await channel.connect(cls=player)

        return vc


**Accessing the Player(VoiceProtocol) (with ctx or guild):**

.. code:: python3

    @commands.command()
    async def play(self, ctx: commands.Context, *, track: wavelink.YouTubeTrack):
        vc: wavelink.Player = ctx.voice_client

        if not vc:
            # Call a connect command or similar that returns a vc...
            vc = ...

        # You can also access player from anywhere you have guild...
        vc = ctx.guild.voice_client


**Accessing a Player from your Node:**

.. code:: python3

    # Could return None, if the Player was not found...

    node = wavelink.NodePool.get_node()
    player = node.get_player(ctx.guild)


Spotify
-------
See: `Spotify Documentation <https://wavelink.readthedocs.io/en/1.0/exts/spotify.html>`_


Common Operations
-----------------
Below are some common operations used with WaveLink. Most WaveLink 1.0 operations are the same as stable release.
See the documentation for more info.

.. code:: python3

    # Play a track...
    await player.play(track)

    # Pause the current song...
    await player.pause()

    # Resume the current song from pause state...
    await player.resume()

    # Stop the current song from playing...
    await player.stop()

    # Stop the current song from playing and disconnect and cleanup the player...
    await player.disconnect()

    # Move the player to another channel...
    await player.move_to(channel)

    # Set the player volume...
    await player.set_volume(30)

    # Seek the currently playing song (position is an integer of seconds)...
    await player.seek(position)

    # Check if the player is playing...
    player.is_playing()

    # Check if the player is connected...
    player.is_connected()

    # Check if the player is paused...
    player.is_paused()

    # Get the best node...
    node = wavelink.NodePool.get_node()

    # Build a track from the unique track base64 identifier...
    await node.build_track(cls=wavelink.YouTubeTrack, identifier="UNIQUE_BASE64_TRACK_IDENTIFIER")

    # Disconnect and cleanup a node and all it's current players...
    await node.disconnect()

    # Common node properties...
    node.host
    node.port
    node.region
    node.identifier
    node.players
    node.is_connected()

    # Common player properties...
    player.guild
    player.user  # The players bot/client instance...
    player.source  # The currently playing song...
    player.position  # The currently playing songs position in seconds...
