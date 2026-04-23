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
import sys
from typing import TYPE_CHECKING, cast


if TYPE_CHECKING:
    from importlib.machinery import ModuleSpec


spec: ModuleSpec | None = None
cspec: ModuleSpec | None = None


for _lib in ("discord", "disnake", "nextcord"):
    spec = importlib.util.find_spec(_lib)

    if spec is not None:
        cspec = importlib.util.find_spec(f"{_lib}.ext.commands")
        break

if spec is None or cspec is None:
    raise ImportError("Unable to find a compatible discord library.")


assert spec.loader
assert cspec.loader

lib = importlib.util.module_from_spec(spec)
lib_commands = importlib.util.module_from_spec(cspec)

sys.modules[spec.name] = lib
sys.modules[cspec.name] = lib_commands

spec.loader.exec_module(lib)
cspec.loader.exec_module(lib_commands)


discord = lib
commands = lib_commands


if TYPE_CHECKING:
    if spec.name == "disnake":
        import disnake as dsna  # type: ignore
        from disnake.ext import commands as snakecom  # type: ignore

        discord = cast("dsna", lib)  # type: ignore
        commands = cast("snakecom", lib_commands)  # type: ignore

    elif spec.name == "nextcord":
        import nextcord as nxtc  # type: ignore
        from nextcord.ext import commands as nextcom  # type: ignore

        discord = cast("nxtc", lib)  # type: ignore
        commands = cast("nextcom", lib_commands)  # type: ignore
    else:
        import discord as disco  # type: ignore
        from discord.ext import commands as discocom  # type: ignore

        discord = cast("disco", lib)  # type: ignore
        commands = cast("discocom", lib_commands)  # type: ignore


# has_discord = False


# try:
#     import discord

#     has_discord = True
# except ImportError:
#     pass

# if not has_discord:
#     try:
#         import disnake as discord

#         has_discord = True
#     except ImportError:
#         pass

# if not has_discord:
#     try:
#         import nextcord as discord

#         has_discord = True
#     except ImportError:
#         pass


# if not has_discord:
#     raise ImportError("Unable to find a compatible discord library.")

# from discord.ext import commands  # type: ignore
