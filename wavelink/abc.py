"""MIT License
Copyright (c) 2019-2020 PythonistaGuild
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
from __future__ import annotations

import abc

from typing import Any, Dict, List, Type, TypeVar, TYPE_CHECKING


if TYPE_CHECKING:
    from .node import Node


class Playable(metaclass=abc.ABCMeta):
    def __init__(self, id: str, data: Dict[str, Any]):
        self.id = id


class Playlist(metaclass=abc.ABCMeta):
    def __init__(self, data: Dict[str, Any]):
        raise NotImplementedError


T = TypeVar('T', bound='Searchable')


class Searchable(Playable):
    _search_type: str = None  # type: ignore

    @classmethod
    @abc.abstractmethod
    async def search(cls: Type[T], node: Node, query: str) -> List[T]:
        ...
