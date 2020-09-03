Wavelink
================
Welcome to WaveLink's Documentation. WaveLink is a robust and powerful Lavalink wrapper for discord.py.

Support
---------------------------
For support using WaveLink, please join the official `support server
<http://discord.gg/RAKc3HF>`_ on `Discord <https://discordapp.com/>`_.

Installation
---------------------------
The following commands are currently the valid ways of installing WaveLink.

**WaveLink requires Python 3.7+**

**Windows**

.. code:: sh

    py -3.7 -m pip install Wavelink

**Linux**

.. code:: sh

    python3.7 -m pip install Wavelink

Getting Started
----------------------------

A quick and easy bot example:

.. code:: py

    import discord
    import wavelink
    from discord.ext import commands


    class Bot(commands.Bot):

        def __init__(self):
            super(Bot, self).__init__(command_prefix=['audio ', 'wave ','aw '])

            self.add_cog(Music(self))

        async def on_ready(self):
            print(f'Logged in as {self.user.name} | {self.user.id}')


    class Music(commands.Cog):

        def __init__(self, bot):
            self.bot = bot

            if not hasattr(bot, 'wavelink'):
                self.bot.wavelink = wavelink.Client(bot=self.bot)

            self.bot.loop.create_task(self.start_nodes())

        async def start_nodes(self):
            await self.bot.wait_until_ready()

            # Initiate our nodes. For this example we will use one server.
            # Region should be a discord.py guild.region e.g sydney or us_central (Though this is not technically required)
            await self.bot.wavelink.initiate_node(host='0.0.0.0',
                                                  port=2333,
                                                  rest_uri='http://0.0.0.0:2333',
                                                  password='youshallnotpass',
                                                  identifier='TEST',
                                                  region='us_central')

        @commands.command(name='connect')
        async def connect_(self, ctx, *, channel: discord.VoiceChannel=None):
            if not channel:
                try:
                    channel = ctx.author.voice.channel
                except AttributeError:
                    raise discord.DiscordException('No channel to join. Please either specify a valid channel or join one.')

            player = self.bot.wavelink.get_player(ctx.guild.id)
            await ctx.send(f'Connecting to **`{channel.name}`**')
            await player.connect(channel.id)

        @commands.command()
        async def play(self, ctx, *, query: str):
            tracks = await self.bot.wavelink.get_tracks(f'ytsearch:{query}')

            if not tracks:
                return await ctx.send('Could not find any songs with that query.')

            player = self.bot.wavelink.get_player(ctx.guild.id)
            if not player.is_connected:
                await ctx.invoke(self.connect_)

            await ctx.send(f'Added {str(tracks[0])} to the queue.')
            await player.play(tracks[0])


    bot = Bot()
    bot.run('TOKEN')

Client
----------------------------

.. autoclass:: wavelink.client.Client
    :members:


Node
----------------------------

.. autoclass:: wavelink.node.Node
    :members:


Player
----------------------------
.. autoclass:: wavelink.player.Player
    :members:


Track
----------------------------
.. autoclass:: wavelink.player.Track
    :members:

.. autoclass:: wavelink.player.TrackPlaylist
    :members:


Equalizer
----------------------------
.. autoclass:: wavelink.eqs.Equalizer
    :members:


Event Payloads
----------------------------

.. autoclass:: wavelink.events.TrackStart
    :members:

.. autoclass:: wavelink.events.TrackEnd
    :members:

.. autoclass:: wavelink.events.TrackException
    :members:

.. autoclass:: wavelink.events.TrackStuck
    :members:


WavelinkMixin
-----------------------

.. warning::
    Listeners must be used with a `wavelink.WavelinkMixin.listener()` decorator to work.

.. warning::
    Listeners must be coroutines.

.. autoclass:: wavelink.meta.WavelinkMixin
    :members:


Errors
-----------------------

.. autoexception:: wavelink.errors.WavelinkException

.. autoexception:: wavelink.errors.NodeOccupied

.. autoexception:: wavelink.errors.InvalidIDProvided

.. autoexception:: wavelink.errors.ZeroConnectedNodes

.. autoexception:: wavelink.errors.AuthorizationFailure
