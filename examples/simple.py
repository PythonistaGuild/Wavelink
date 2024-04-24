"""
MIT License

Copyright (c) 2019-Current PythonistaGuild, EvieePy

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import asyncio
import logging
from typing import cast

import discord
from discord.ext import commands

import wavelink


class Bot(commands.Bot):
    def __init__(self) -> None:
        intents: discord.Intents = discord.Intents.default()
        intents.message_content = True

        discord.utils.setup_logging(level=logging.INFO)
        super().__init__(command_prefix="?", intents=intents)

    async def setup_hook(self) -> None:
        nodes = [wavelink.Node(uri="...", password="...")]

        # cache_capacity is EXPERIMENTAL. Turn it off by passing None
        await wavelink.Pool.connect(nodes=nodes, client=self, cache_capacity=100)

    async def on_ready(self) -> None:
        logging.info("Logged in: %s | %s", self.user, self.user.id)

    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload) -> None:
        logging.info("Wavelink Node connected: %r | Resumed: %s", payload.node, payload.resumed)

    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        player: wavelink.Player | None = payload.player
        if not player:
            # Handle edge cases...
            return

        original: wavelink.Playable | None = payload.original
        track: wavelink.Playable = payload.track

        embed: discord.Embed = discord.Embed(title="Now Playing")
        embed.description = f"**{track.title}** by `{track.author}`"

        if track.artwork:
            embed.set_image(url=track.artwork)

        if original and original.recommended:
            embed.description += f"\n\n`This track was recommended via {track.source}`"

        if track.album.name:
            embed.add_field(name="Album", value=track.album.name)

        await player.home.send(embed=embed)


bot: Bot = Bot()


@bot.command()
async def play(ctx: commands.Context, *, query: str) -> None:
    """Play a song with the given query."""
    if not ctx.guild:
        return

    player: wavelink.Player
    player = cast(wavelink.Player, ctx.voice_client)  # type: ignore

    if not player:
        try:
            player = await ctx.author.voice.channel.connect(cls=wavelink.Player)  # type: ignore
        except AttributeError:
            await ctx.send("Please join a voice channel first before using this command.")
            return
        except discord.ClientException:
            await ctx.send("I was unable to join this voice channel. Please try again.")
            return

    # Turn on AutoPlay to enabled mode.
    # enabled = AutoPlay will play songs for us and fetch recommendations...
    # partial = AutoPlay will play songs for us, but WILL NOT fetch recommendations...
    # disabled = AutoPlay will do nothing...
    player.autoplay = wavelink.AutoPlayMode.enabled

    # Lock the player to this channel...
    if not hasattr(player, "home"):
        player.home = ctx.channel
    elif player.home != ctx.channel:
        await ctx.send(f"You can only play songs in {player.home.mention}, as the player has already started there.")
        return

    # This will handle fetching Tracks and Playlists...
    # Seed the doc strings for more information on this method...
    # If spotify is enabled via LavaSrc, this will automatically fetch Spotify tracks if you pass a URL...
    # Defaults to YouTube for non URL based queries...
    tracks: wavelink.Search = await wavelink.Playable.search(query)
    if not tracks:
        await ctx.send(f"{ctx.author.mention} - Could not find any tracks with that query. Please try again.")
        return

    if isinstance(tracks, wavelink.Playlist):
        # tracks is a playlist...
        added: int = await player.queue.put_wait(tracks)
        await ctx.send(f"Added the playlist **`{tracks.name}`** ({added} songs) to the queue.")
    else:
        track: wavelink.Playable = tracks[0]
        await player.queue.put_wait(track)
        await ctx.send(f"Added **`{track}`** to the queue.")

    if not player.playing:
        # Play now since we aren't playing anything...
        await player.play(player.queue.get(), volume=30)

    # Optionally delete the invokers message...
    try:
        await ctx.message.delete()
    except discord.HTTPException:
        pass


@bot.command()
async def skip(ctx: commands.Context) -> None:
    """Skip the current song."""
    player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
    if not player:
        return

    await player.skip(force=True)
    await ctx.message.add_reaction("\u2705")


@bot.command()
async def nightcore(ctx: commands.Context) -> None:
    """Set the filter to a nightcore style."""
    player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
    if not player:
        return

    filters: wavelink.Filters = player.filters
    filters.timescale.set(pitch=1.2, speed=1.2, rate=1)
    await player.set_filters(filters)

    await ctx.message.add_reaction("\u2705")


@bot.command(name="toggle", aliases=["pause", "resume"])
async def pause_resume(ctx: commands.Context) -> None:
    """Pause or Resume the Player depending on its current state."""
    player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
    if not player:
        return

    await player.pause(not player.paused)
    await ctx.message.add_reaction("\u2705")


@bot.command()
async def volume(ctx: commands.Context, value: int) -> None:
    """Change the volume of the player."""
    player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
    if not player:
        return

    await player.set_volume(value)
    await ctx.message.add_reaction("\u2705")


@bot.command(aliases=["dc"])
async def disconnect(ctx: commands.Context) -> None:
    """Disconnect the Player."""
    player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
    if not player:
        return

    await player.disconnect()
    await ctx.message.add_reaction("\u2705")


async def main() -> None:
    async with bot:
        await bot.start("BOT_TOKEN_HERE")


asyncio.run(main())
