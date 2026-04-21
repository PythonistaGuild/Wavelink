"""Copyright 2026 Evie. P. <evieepy@gmail.com>, PythonistaGuild

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

has_discord = False


try:
    import discord

    has_discord = True
except ImportError:
    pass

if not has_discord:
    try:
        import disnake as discord

        has_discord = True
    except ImportError:
        pass

if not has_discord:
    try:
        import nextcord as discord

        has_discord = True
    except ImportError:
        pass


if not has_discord:
    raise ImportError("Unable to find a compatible discord library.")

from discord.ext import commands  # type: ignore # noqa: F401 E402
