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

from __future__ import annotations

import importlib
import importlib.util
from typing import TYPE_CHECKING


__all__ = (
    "Client",
    "Connectable",
    "Guild",
    "GuildChannel",
    "GuildVoiceStatePayload",
    "StageChannel",
    "VoiceChannel",
    "VoiceProtocol",
    "VoiceServerUpdatePayload",
    "commands",
)


if TYPE_CHECKING:
    from importlib.machinery import ModuleSpec


spec: ModuleSpec | None = None
cspec: ModuleSpec | None = None

found = None
for _lib in ("discord", "disnake", "nextcord"):
    spec = importlib.util.find_spec(_lib)

    if spec is not None:
        found = _lib
        cspec = importlib.util.find_spec(f"{_lib}.ext.commands")
        break

if spec is None or cspec is None:
    raise ImportError("Unable to find a compatible discord library.")


if found == "nextcord":
    from nextcord import Client, Guild, StageChannel, VoiceChannel, VoiceProtocol, version_info
    from nextcord.abc import Connectable, GuildChannel
    from nextcord.ext import commands

    if TYPE_CHECKING:
        from nextcord.types.voice import (
            GuildVoiceState as GuildVoiceStatePayload,
            VoiceServerUpdate as VoiceServerUpdatePayload,
        )

elif found == "disnake":
    from disnake import Client, Guild, StageChannel, VoiceChannel, VoiceProtocol, version_info
    from disnake.abc import Connectable, GuildChannel
    from disnake.ext import commands

    if TYPE_CHECKING:
        if version_info >= (2, 6):
            from disnake.types.gateway import VoiceServerUpdateEvent as VoiceServerUpdatePayload
        else:
            from disnake.types.voice import VoiceServerUpdate as VoiceServerUpdatePayload  # type: ignore
        from disnake.types.voice import GuildVoiceState as GuildVoiceStatePayload

else:
    from discord import Client, Guild, StageChannel, VoiceChannel, VoiceProtocol, version_info
    from discord.abc import Connectable, GuildChannel
    from discord.ext import commands

    if TYPE_CHECKING:
        from discord.types.voice import (
            GuildVoiceState as GuildVoiceStatePayload,  # noqa: TC004
            VoiceServerUpdate as VoiceServerUpdatePayload,  # noqa: TC004
        )
