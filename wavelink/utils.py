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

--------------------------------------------------------------------------

The MIT License (MIT)

Copyright (c) 2015-present Rapptz

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations

import inspect
import json
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal, Never, overload

from .helpers import LoadBalancingStrategy, NodeStrategy


if TYPE_CHECKING:
    from collections.abc import ItemsView, Iterator, MutableMapping, ValuesView

    from .node import Node


__all__ = ("JSON_LOADS", "MISSING")


try:
    import orjson  # type: ignore

    JSON_LOADS: Any = orjson.loads  # type: ignore
except ImportError:
    JSON_LOADS: Any = json.loads  # type: ignore


class _MissingSentinel:
    __slots__ = ()

    def __eq__(self, other: object) -> bool:
        return False

    def __bool__(self) -> bool:
        return False

    def __hash__(self) -> int:
        return 0

    def __repr__(self) -> Literal["..."]:
        return "..."


MISSING: Any = _MissingSentinel()


class NodeMapping:
    __slots__ = ("_default_strategy", "_nodes")

    def __init__(self) -> None:
        self._default_strategy = LoadBalancingStrategy()
        self._nodes: dict[str, Node] = {}

    def __setitem__(self, key: str, node: Node) -> None:
        self._nodes[key] = node

    def __getitem__(self, key: str) -> Node:
        return self._nodes[key]

    def __delitem__(self, key: str) -> None:
        del self._nodes[key]

    def __iter__(self) -> Iterator[str]:
        return self._nodes.__iter__()

    def __len__(self) -> int:
        return len(self._nodes)

    def proxy(self) -> MappingProxyType[str, Node]:
        return MappingProxyType(self._nodes)

    def values(self) -> ValuesView[Node]:
        return self._nodes.values()

    def items(self) -> ItemsView[str, Node]:
        return self._nodes.items()

    def copy(self) -> MutableMapping[str, Node]:
        return dict(self._nodes)

    @overload
    def get(self, key: str, /) -> Node: ...

    @overload
    def get[DT](self, key: str, /, default: DT) -> Node | DT: ...

    @overload
    def get(self, key: str, /, default: None = None) -> Node | None: ...

    def get[DT](self, key: str, /, default: DT | None = None) -> Node | DT | None:
        return self._nodes.get(key, default)

    @overload
    def pop(self, key: str, /) -> Node: ...

    @overload
    def pop[DT](self, key: str, /, default: DT) -> Node | DT: ...

    @overload
    def pop(self, key: str, /, default: Never = MISSING) -> Node: ...

    def pop[DT](self, key: str, /, default: DT = MISSING) -> Node | DT:
        if default is not MISSING:
            return self._nodes.pop(key, default)

        return self._nodes.pop(key)

    def select(self, strategy: NodeStrategy | type[NodeStrategy] = MISSING) -> Node | None:
        if strategy is MISSING:
            return self._default_strategy.select(self.proxy())

        if inspect.isclass(strategy):
            inst = strategy()
            return inst.select(self.proxy())

        return strategy.select(self.proxy())
