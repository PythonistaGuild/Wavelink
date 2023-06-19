"""
MIT License

Copyright (c) 2019-Present PythonistaGuild

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
        # Wavelink 2.0 has made connecting Nodes easier... Simply create each Node
        # and pass it to NodePool.connect with the client/bot.
        # Fill your Spotify API details and pass it to connect.
        sc = spotify.SpotifyClient(
            client_id='CLIENT_ID',
            client_secret='SECRET'
        )
        node: wavelink.Node = wavelink.Node(uri='http://localhost:2333', password='youshallnotpass')
        await wavelink.NodePool.connect(client=self, nodes=[node], spotify=sc)


bot = Bot()


@bot.command()
async def play(ctx: commands.Context, *, search: str) -> None:
    """Simple play command that accepts a Spotify song URL.

    This command enables AutoPlay. AutoPlay finds songs automatically when used with Spotify.
    Tracks added to the Queue will be played in front (Before) of those added by AutoPlay.
    """

    if not ctx.voice_client:
        vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
    else:
        vc: wavelink.Player = ctx.voice_client

    # Check the search to see if it matches a valid Spotify URL...
    decoded = spotify.decode_url(search)
    if not decoded or decoded['type'] is not spotify.SpotifySearchType.track:
        await ctx.send('Only Spotify Track URLs are valid.')
        return

    # Set autoplay to True. This can be disabled at anytime...
    vc.autoplay = True

    tracks: list[spotify.SpotifyTrack] = await spotify.SpotifyTrack.search(search)
    if not tracks:
        await ctx.send('This does not appear to be a valid Spotify URL.')
        return

    track: spotify.SpotifyTrack = tracks[0]

    # IF the player is not playing immediately play the song...
    # otherwise put it in the queue...
    if not vc.is_playing():
        await vc.play(track, populate=True)
    else:
        await vc.queue.put_wait(track)
