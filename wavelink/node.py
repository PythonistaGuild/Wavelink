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

from types import MappingProxyType
from typing import Any
from functools import cached_property

import aiohttp

from wavelink._lib import discord, commands

from .utils import MISSING

class Node: ...


class Pool:
    def __init__(self, client: discord.Client | commands.Bot, *, context_attr: str | None = MISSING, session: aiohttp.ClientSession = MISSING, password: str) -> None:
        self._password = password
        self._client = client
        self._session = session if session is not MISSING else aiohttp.ClientSession()

        # if context_attr is not None:
        #     self._ctx_di(context_attr if context_attr is not MISSING else "wave")
    
    @cached_property
    def headers(self) -> MappingProxyType[str, str]:
        return MappingProxyType({"Authorization": self._password})

    # def _ctx_di(self, attr: str) -> None:
    #     meth = getattr(self._client, "get_context", None)
    #     if not meth:
    #         return

    #     async def injected(*args: Any, **kwargs: Any) -> Any:
    #         nonlocal attr

    #         ctx = await meth(*args, **kwargs)
    #         if hasattr(ctx, attr):
    #             msg = (
    #                 f"The provided 'context_attr' parameter passed to {self.__class__.__name__!r}, "
    #                 "conflicts with an existing Context attribute."
    #             )
    #             raise AttributeError(msg)

    #         setattr(ctx, attr, self)
    #         return ctx

    #     setattr(self._client, "get_context", injected)

    def add_node(self) -> ...: ...

    async def create_node(self) -> Node:
        ...
    
    # /loadtracks
    async def load_tracks(self, identifier: str) -> ...: ...
    
    # /decodetrack
    async def decode_track(self, encoded: str) -> ...: ...
    
    # /decodetracks
    async def decode_tracks(self, encoded: list[str]) -> ...: ...
    
    # /sessions/{sessionId}/players
    async def get_players(self) -> ...: ...
    
    # /sessions/{sessionId}/players/{guildId}
    async def get_player(self) -> ...: ...