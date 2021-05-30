.. image:: logo.png?raw=true
    :align: center

.. image:: https://img.shields.io/badge/Python-3.7%20%7C%203.8-blue.svg
    :target: https://www.python.org

.. image:: https://api.codacy.com/project/badge/Grade/d020ed97fd2a46fcb1f42bd3bc397e63
   :target: https://app.codacy.com/app/mysterialpy/Wavelink?utm_source=github.com&utm_medium=referral&utm_content=EvieePy/Wavelink&utm_campaign=Badge_Grade_Dashboard

.. image:: https://img.shields.io/github/license/EvieePy/Wavelink.svg
    :target: LICENSE

A robust and powerful Lavalink wrapper for `Discord.py <https://github.com/Rapptz/discord.py>`_!

Documentation
---------------------------
`Official Documentation <https://wavelink.readthedocs.io/en/latest/wavelink.html#>`_.

Support
---------------------------
For support using WaveLink, please join the official `support server
<https://discord.gg/RAKc3HF>`_ on `Discord <https://discordapp.com/>`_.

|Discord|

.. |Discord| image:: https://img.shields.io/discord/490948346773635102?color=%237289DA&label=Pythonista&logo=discord&logoColor=white
   :target: https://discord.gg/RAKc3HF

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
            await self.bot.wavelink.initiate_node(host='127.0.0.1',
                                                  port=2333,
                                                  rest_uri='http://127.0.0.1:2333',
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
