.. image:: https://raw.githubusercontent.com/PythonistaGuild/Wavelink/master/logo.png


.. image:: https://img.shields.io/badge/Python-3.10%20%7C%203.11-blue.svg
    :target: https://www.python.org


.. image:: https://img.shields.io/github/license/EvieePy/Wavelink.svg
    :target: LICENSE


.. image:: https://img.shields.io/discord/490948346773635102?color=%237289DA&label=Pythonista&logo=discord&logoColor=white
   :target: https://discord.gg/RAKc3HF


.. image:: https://img.shields.io/pypi/dm/Wavelink?color=black
    :target: https://pypi.org/project/Wavelink
    :alt: PyPI - Downloads


.. image:: https://img.shields.io/maintenance/yes/2023?color=pink&style=for-the-badge
    :target: https://github.com/PythonistaGuild/Wavelink/commits/main
    :alt: Maintenance



Wavelink is a robust and powerful Lavalink wrapper for `Discord.py <https://github.com/Rapptz/discord.py>`_.
Wavelink features a fully asynchronous API that's intuitive and easy to use with built in Spotify Support and Node Pool Balancing.


**Features:**

- Fully Asynchronous
- Auto-Play and Looping (With the inbuilt Queue system)
- Spotify Support
- Node Balancing and Fail-over
- Supports Lavalink 3.7+


Documentation
---------------------------
`Official Documentation <https://wavelink.dev/>`_

Support
---------------------------
For support using WaveLink, please join the official `support server
<https://discord.gg/RAKc3HF>`_ on `Discord <https://discordapp.com/>`_.

.. image:: https://discordapp.com/api/guilds/490948346773635102/widget.png?style=banner2
    :target: https://discord.gg/RAKc3HF


Installation
---------------------------
The following commands are currently the valid ways of installing WaveLink.

**WaveLink 2 requires Python 3.10+**

**Windows**

.. code:: sh

    py -3.10 -m pip install -U Wavelink

**Linux**

.. code:: sh

    python3.10 -m pip install -U Wavelink

Getting Started
----------------------------

**See also:** `Examples <https://github.com/PythonistaGuild/Wavelink/tree/main/examples>`_

.. code:: py

    import discord
    import wavelink
    from discord.ext import commands


    class Bot(commands.Bot):

        def __init__(self) -> None:
            intents = discord.Intents.default()
            intents.message_content = True

            super().__init__(intents=intents, command_prefix='?')

        async def on_ready(self) -> None:
            print(f'Logged in {self.user} | {self.user.id}')

        async def setup_hook(self) -> None:
            # Wavelink 2.0 has made connecting Nodes easier... Simply create each Node
            # and pass it to NodePool.connect with the client/bot.
            node: wavelink.Node = wavelink.Node(uri='http://localhost:2333', password='youshallnotpass')
            await wavelink.NodePool.connect(client=self, nodes=[node])


    bot = Bot()


    @bot.command()
    async def play(ctx: commands.Context, *, search: str) -> None:
        """Simple play command."""

        if not ctx.voice_client:
            vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = ctx.voice_client

        tracks = await wavelink.YouTubeTrack.search(search)
        if not tracks:
            await ctx.send(f'No tracks found with query: `{search}`')
            return

        track = tracks[0]
        await vc.play(track)


    @bot.command()
    async def disconnect(ctx: commands.Context) -> None:
        """Simple disconnect command.

        This command assumes there is a currently connected Player.
        """
        vc: wavelink.Player = ctx.voice_client
        await vc.disconnect()


Lavalink Installation
---------------------

Head to the official `Lavalink repo <https://github.com/lavalink-devs/Lavalink>`_ and give it a star!

- Create a folder for storing Lavalink.jar and related files/folders.
- Copy and paste the example `application.yml <https://github.com/freyacodes/Lavalink#server-configuration>`_ to ``application.yml`` in the folder we created earlier. You can open the yml in Notepad or any simple text editor.
- Change your password in the ``application.yml`` and store it in a config for your bot.
- Set local to true in the ``application.yml`` if you wish to use ``wavelink.LocalTrack`` for local machine search options... Otherwise ignore.
- Save and exit.
- Install `Java 17(Windows) <https://download.oracle.com/java/17/latest/jdk-17_windows-x64_bin.exe>`_ or **Java 13+** on the machine you are running.
- Download `Lavalink.jar <https://github.com/lavalink-devs/Lavalink/releases>`_ and place it in the folder created earlier.
- Open a cmd prompt or terminal and change directory ``cd`` into the folder we made earlier.
- Run: ``java -jar Lavalink.jar``

If you are having any problems installing Lavalink, please join the official Discord Server listed above for help.
