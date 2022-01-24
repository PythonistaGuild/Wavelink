import discord
import wavelink
from discord.ext import commands

class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super(Bot, self).__init__(*args, **kwargs)
    
    async def on_ready(self):
        print("-----")
        print(f"Logged in as: {self.user.name}#{self.user.discriminator}")
        print(f"ID: {self.user.id}")
        print("-----")

class FilteredMusic(commands.Cog):
    """Music cog to hold Wavelink related commands and listeners."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        bot.loop.create_task(self.connect_nodes())

        self.players = {}

    async def connect_nodes(self):
        """Connect to our Lavalink nodes."""
        await self.bot.wait_until_ready()

        await wavelink.NodePool.create_node(bot=self.bot,
                                            host='127.0.0.1',
                                            port=2233,
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

        self.players[ctx.guild.id] = vc
        await vc.play(search)

    @commands.command()
    async def vibrato(self, ctx: commands.Context, frequency: float = 2.0, depth: float = 0.5):
        """Apply a vibrato filter."""
        vc = self.players.get(ctx.guild.id)
        await vc.set_filter(wavelink.filters.Filter(vibrato=wavelink.filters.Vibrato(frequency=frequency, depth=depth)))
        return await ctx.send("Vibrato filter has been applied.", delete_after=15.0)

    @commands.command()
    async def karaoke(self, ctx: commands.Context, level: float = 1.0, mono_level: float = 1.0, filter_band: float = 220.0, filter_width: float = 100.0):
        """Apply a karaoke filter."""
        vc = self.players.get(ctx.guild.id)
        await vc.set_filter(wavelink.filters.Filter(karaoke=wavelink.filters.Karaoke(level=level, mono_level=mono_level, filter_band=filter_band, filter_width=filter_width)))
        return await ctx.send("Karaoke filter has been applied.", delete_after=15.0)

    @commands.command()
    async def timescale(self, ctx: commands.Context, speed: float = 1.0, pitch: float = 1.0, rate: float = 1.0):
        """Apply a timescale filter."""
        vc = self.players.get(ctx.guild.id)
        await vc.set_filter(wavelink.filters.Filter(timescale=wavelink.filters.Timescale(speed=speed, pitch=pitch, rate=rate)))
        return await ctx.send("Timescale filter has been applied.", delete_after=15.0)

    @commands.command()
    async def reset_filter(self, ctx: commands.Context):
        """Resets the filter."""
        vc = self.players.get(ctx.guild.id)
        await vc.set_filter(wavelink.filters.Filter())
        return await ctx.send("Reset filters.", delete_after=15.0)

bot = Bot(command_prefix=">?")
bot.add_cog(FilteredMusic(bot))
bot.run('TOKEN')
