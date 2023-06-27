.. currentmodule:: wavelink.ext.spotify


Intro
-----
The Spotify extension is a QoL extension that helps in searching for and queueing tracks from Spotify URLs. To get started create a :class:`~SpotifyClient` and pass in your credentials. You then pass this to your :class:`wavelink.Node`'s.

An example:

.. code-block:: python3

    import discord
    import wavelink
    from discord.ext import commands
    from wavelink.ext import spotify


    class Bot(commands.Bot):

        def __init__(self) -> None:
            intents = discord.Intents.default()
            intents.message_content = True

            super().__init__(intents=intents, command_prefix='?')

        async def on_ready(self) -> None:
            print(f'Logged in {self.user} | {self.user.id}')

        async def setup_hook(self) -> None:
            sc = spotify.SpotifyClient(
                client_id='CLIENT_ID',
                client_secret='CLIENT_SECRET'
            )

            node: wavelink.Node = wavelink.Node(uri='http://127.0.0.1:2333', password='youshallnotpass')
            await wavelink.NodePool.connect(client=self, nodes=[node], spotify=sc)


    bot = Bot()


    @bot.command()
    @commands.is_owner()
    async def play(ctx: commands.Context, *, search: str) -> None:

        try:
            vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        except discord.ClientException:
            vc: wavelink.Player = ctx.voice_client

        vc.autoplay = True

        track: spotify.SpotifyTrack = await spotify.SpotifyTrack.search(search)

        if not vc.is_playing():
            await vc.play(track, populate=True)
        else:
            await vc.queue.put_wait(track)


Helpers
-------
.. autofunction:: decode_url


Payloads
--------
.. attributetable:: SpotifyDecodePayload

.. autoclass:: SpotifyDecodePayload


Client
------
.. attributetable:: SpotifyClient

.. autoclass:: SpotifyClient
    :members:


Enums
-----
.. attributetable:: SpotifySearchType

.. autoclass:: SpotifySearchType
    :members:


Spotify Tracks
--------------
.. attributetable:: SpotifyTrack

.. autoclass:: SpotifyTrack
    :members:


Exceptions
----------
.. py:exception:: SpotifyRequestError

    Base error for Spotify requests.

    status: :class:`int`
        The status code returned from the request.
    reason: Optional[:class:`str`]
        The reason the request failed. Could be ``None``.
