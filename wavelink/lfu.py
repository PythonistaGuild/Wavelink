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

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from .exceptions import WavelinkException


class CapacityZero(WavelinkException): ...


class _MissingSentinel:
    __slots__ = ()

    def __eq__(self, other: object) -> bool:
        return False

    def __bool__(self) -> bool:
        return False

    def __hash__(self) -> int:
        return 0

    def __repr__(self) -> str:
        return "..."


class _NotFoundSentinel(_MissingSentinel):
    def __repr__(self) -> str:
        return "NotFound"


MISSING: Any = _MissingSentinel()
NotFound: Any = _NotFoundSentinel()


class DLLNode:
    __slots__ = ("value", "previous", "later")

    def __init__(self, value: Any | None = None, previous: DLLNode | None = None, later: DLLNode | None = None) -> None:
        self.value = value
        self.previous = previous
        self.later = later


@dataclass
class DataNode:
    key: Any
    value: Any
    frequency: int
    node: DLLNode


class LFUCache:
    def __init__(self, *, capacity: int) -> None:
        self._capacity = capacity
        self._cache: dict[Any, DataNode] = {}

        self._freq_map: defaultdict[int, DLL] = defaultdict(DLL)
        self._min: int = 1
        self._used: int = 0

    def __len__(self) -> int:
        return len(self._cache)

    def __getitem__(self, key: Any) -> Any:
        if key not in self._cache:
            raise KeyError(f'"{key}" could not be found in LFU.')

        return self.get(key)

    def __setitem__(self, key: Any, value: Any) -> None:
        return self.put(key, value)

    @property
    def capacity(self) -> int:
        return self._capacity

    def get(self, key: Any, default: Any = MISSING) -> Any:
        if key not in self._cache:
            return default if default is not MISSING else NotFound

        data: DataNode = self._cache[key]
        self._freq_map[data.frequency].remove(data.node)
        self._freq_map[data.frequency + 1].append(data.node)

        self._cache[key] = DataNode(key=key, value=data.value, frequency=data.frequency + 1, node=data.node)
        self._min += self._min == data.frequency and not self._freq_map[data.frequency]

        return data.value

    def put(self, key: Any, value: Any) -> None:
        if self._capacity <= 0:
            raise CapacityZero("Unable to place item in LFU as capacity has been set to 0 or below.")

        if key in self._cache:
            self._cache[key].value = value
            self.get(key)
            return

        if self._used == self._capacity:
            least_freq: DLL = self._freq_map[self._min]
            least_freq_key: DLLNode | None = least_freq.popleft()

            if least_freq_key:
                self._cache.pop(least_freq_key.value)
                self._used -= 1

        data: DataNode = DataNode(key=key, value=value, frequency=1, node=DLLNode(key))
        self._freq_map[data.frequency].append(data.node)
        self._cache[key] = data

        self._used += 1
        self._min = 1


class DLL:
    __slots__ = ("head", "tail")

    def __init__(self) -> None:
        self.head: DLLNode = DLLNode()
        self.tail: DLLNode = DLLNode()

        self.head.later, self.tail.previous = self.tail, self.head

    def append(self, node: DLLNode) -> None:
        tail_prev: DLLNode | None = self.tail.previous
        tail: DLLNode | None = self.tail

        assert tail_prev and tail

        tail_prev.later = node
        tail.previous = node

        node.later = tail
        node.previous = tail_prev

    def popleft(self) -> DLLNode | None:
        node: DLLNode | None = self.head.later
        if node is None:
            return

        self.remove(node)
        return node

    def remove(self, node: DLLNode | None) -> None:
        if node is None:
            return

        node_prev: DLLNode | None = node.previous
        node_later: DLLNode | None = node.later

        assert node_prev and node_later

        node_prev.later = node_later
        node_later.previous = node_prev

        node.later = None
        node.previous = None

    def __bool__(self) -> bool:
        return self.head.later != self.tail
