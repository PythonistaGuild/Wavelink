.. image:: https://raw.githubusercontent.com/PythonistaGuild/Wavelink/master/logo.png


.. image:: https://img.shields.io/badge/Python-3.8%20%7C%203.9%20%7C%203.10-blue.svg
    :target: https://www.python.org


.. image:: https://img.shields.io/github/license/EvieePy/Wavelink.svg
    :target: LICENSE


.. image:: https://img.shields.io/discord/490948346773635102?color=%237289DA&label=Pythonista&logo=discord&logoColor=white
   :target: https://discord.gg/RAKc3HF


.. image:: https://img.shields.io/pypi/dm/Wavelink?color=black
    :target: https://pypi.org/project/Wavelink
    :alt: PyPI - Downloads
    
    
.. image:: https://img.shields.io/maintenance/yes/2022?color=pink&style=for-the-badge
    :target: https://github.com/PythonistaGuild/Wavelink/commits/main
    :alt: Maintenance



Wavelink is a robust and powerful Lavalink wrapper for `Discord.py <https://github.com/Rapptz/discord.py>`_ and certain supported forks.
Wavelink features a fully asynchronous API that's intuitive and easy to use with built in Spotify Support and Node Pool Balancing.

Documentation
---------------------------
`Official Documentation <https://wavelink.readthedocs.io/en/latest/wavelink.html>`_

Support
---------------------------
For support using WaveLink, please join the official `support server
<https://discord.gg/RAKc3HF>`_ on `Discord <https://discordapp.com/>`_.

.. image:: https://discordapp.com/api/guilds/490948346773635102/widget.png?style=banner2
    :target: https://discord.gg/RAKc3HF


Installation
---------------------------
The following commands are currently the valid ways of installing WaveLink.

**WaveLink requires Python 3.8+**

**Windows**

.. code:: sh

    py -3.9 -m pip install -U Wavelink

**Linux**

.. code:: sh

    python3.9 -m pip install -U Wavelink

Getting Started
----------------------------

A quick and easy bot example:

.. code:: py
    
    import wavelink
    from discord.ext import commands


    class Bot(commands.Bot):

        def __init__(self):
            super().__init__(command_prefix='>?')

        async def on_ready(self):
            print('Bot is ready!')


    class Music(commands.Cog):
        """Music cog to hold Wavelink related commands and listeners."""

        def __init__(self, bot: commands.Bot):
            self.bot = bot

            bot.loop.create_task(self.connect_nodes())

        async def connect_nodes(self):
            """Connect to our Lavalink nodes."""
            await self.bot.wait_until_ready()

            await wavelink.NodePool.create_node(bot=bot,
                                                host='0.0.0.0',
                                                port=2333,
                                                password='YOUR_LAVALINK_PASSWORD')

        @commands.Cog.listener()
        async def on_wavelink_node_ready(self, node: wavelink.Node):
            """Event fired when a node has finished connecting."""
            print(f'Node: <{node.identifier}> is ready!')

        @commands.command()
        async def play(self, ctx: commands.Context, *, search: wavelink.YouTubeTrack):
            """Play a song with the given search query.

            If not connected, connect to our voice channel.
            """
            if not ctx.voice_client:
                vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
            else:
                vc: wavelink.Player = ctx.voice_client

            await vc.play(search)


    bot = Bot()
    bot.add_cog(Music(bot))
    bot.run('YOUR_BOT_TOKEN')


Lavalink Installation
---------------------

Head to the official `Lavalink repo <https://github.com/freyacodes/Lavalink#server-configuration>`_ and give it a star!

- Create a folder for storing Lavalink.jar and related files/folders.
- Copy and paste the example `application.yml <https://github.com/freyacodes/Lavalink#server-configuration>`_ to ``application.yml`` in the folder we created earlier. You can open the yml in Notepad or any simple text editor.
- Change your password in the ``application.yml`` and store it in a config for your bot.
- Set local to true in the ``application.yml`` if you wish to use ``wavelink.LocalTrack`` for local machine search options... Otherwise ignore.
- Save and exit.
- Install `Java 17(Windows) <https://download.oracle.com/java/17/latest/jdk-17_windows-x64_bin.exe>`_ or **Java 13+** on the machine you are running.
- Download `Lavalink.jar <https://ci.fredboat.com/viewLog.html?buildId=lastSuccessful&buildTypeId=Lavalink_Build&tab=artifacts&guest=1>`_ and place it in the folder created earlier.
- Open a cmd prompt or terminal and change directory ``cd`` into the folder we made earlier.
- Run: ``java -jar Lavalink.jar``

If you are having any problems installing Lavalink, please join the official Discord Server listed above for help.
