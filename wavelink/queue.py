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

import asyncio
from collections import deque
from random import Random
from typing import TYPE_CHECKING

from .tracks import Search


if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from .tracks import Track


class Queue:
    __slots__ = ("_getters", "_items")

    def __init__(self, tracks: Iterable[Track] | None = None) -> None:
        self._items: deque[Track] = deque(tracks or ())
        self._getters: deque[asyncio.Future[Track]] = deque()

    def __repr__(self) -> str:
        return f"Queue(size={len(self._items)})"

    def __bool__(self) -> bool:
        return bool(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[Track]:
        return iter(self._items)

    def __contains__(self, track: object) -> bool:
        return track in self._items

    def __getitem__(self, index: int | slice) -> Track | list[Track]:
        if isinstance(index, slice):
            return list(self._items)[index]

        return self._items[index]

    def __call__(self, item: Track | Search) -> None:
        self.put(item)

    @property
    def is_empty(self) -> bool:
        return not self._items

    def clear(self) -> None:
        self._items.clear()

    def _wake_getters(self) -> None:
        while self._items and self._getters:
            getter = self._getters.popleft()
            if getter.done():
                continue

            getter.set_result(self._items.popleft())

    # TODO accommodate Search returning Playlist once implemented using .extend()
    def put(self, item: Track | Search) -> None:
        if isinstance(item, Search):
            if item.first is None:
                return
            self._items.append(item.first)
        else:
            self._items.append(item)
        self._wake_getters()

    def prepend(self, item: Track | Search) -> None:
        if isinstance(item, Search):
            if item.first is None:
                return
            self._items.appendleft(item.first)
        else:
            self._items.appendleft(item)
        self._wake_getters()

    def extend(self, tracks: Iterable[Track] | Search) -> None:
        self._items.extend(tracks)
        self._wake_getters()

    def extend_prepend(self, tracks: Iterable[Track] | Search) -> None:
        buffered = list(tracks)
        self._items.extendleft(reversed(buffered))
        self._wake_getters()

    async def get_wait(self) -> Track:
        if self._items:
            return self._items.popleft()

        loop = asyncio.get_running_loop()
        getter: asyncio.Future[Track] = loop.create_future()
        self._getters.append(getter)

        try:
            return await getter
        except asyncio.CancelledError:
            if not getter.done():
                getter.cancel()

            try:
                self._getters.remove(getter)
            except ValueError:
                pass

            raise

    def get(self) -> Track:
        return self.popleft()

    def peek(self, index: int = 0) -> Track:
        if not self._items:
            raise IndexError("peek from an empty Queue")

        return self._items[index]

    def popleft(self) -> Track:
        if not self._items:
            raise IndexError("pop from an empty Queue")

        return self._items.popleft()

    def pop(self, index: int = -1) -> Track:
        if not self._items:
            raise IndexError("pop from an empty Queue")

        size = len(self._items)
        resolved = index + size if index < 0 else index
        if resolved < 0 or resolved >= size:
            raise IndexError("Queue index out of range")

        if resolved == 0:
            return self._items.popleft()

        if resolved == size - 1:
            return self._items.pop()

        self._items.rotate(-resolved)
        item = self._items.popleft()
        self._items.rotate(resolved)
        return item

    def shuffle(self) -> None:
        if len(self._items) < 2:
            return

        items = list(self._items)
        Random().shuffle(items)
        self._items = deque(items)

    def to_list(self) -> list[Track]:
        return list(self._items)
