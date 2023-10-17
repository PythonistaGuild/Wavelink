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

import asyncio
from collections import deque
from typing import Any, Iterator, overload

from .exceptions import QueueEmpty
from .tracks import *

__all__ = ("Queue",)


class _Queue:
    def __init__(self) -> None:
        self._queue: deque[Playable] = deque()

    def __str__(self) -> str:
        return ", ".join([f'"{p}"' for p in self])

    def __repr__(self) -> str:
        return f"BaseQueue(items={len(self._queue)})"

    def __bool__(self) -> bool:
        return bool(self._queue)

    def __call__(self, item: Playable | Playlist) -> None:
        self.put(item)

    def __len__(self) -> int:
        return len(self._queue)

    @overload
    def __getitem__(self, index: int) -> Playable:
        ...

    @overload
    def __getitem__(self, index: slice) -> list[Playable]:
        ...

    def __getitem__(self, index: int | slice) -> Playable | list[Playable]:
        if isinstance(index, slice):
            return list(self._queue)[index]

        return self._queue[index]

    def __iter__(self) -> Iterator[Playable]:
        return self._queue.__iter__()

    def __contains__(self, item: Any) -> bool:
        return item in self._queue

    @staticmethod
    def _check_compatability(item: Any) -> None:
        if not isinstance(item, Playable):
            raise TypeError("This queue is restricted to Playable objects.")

    def _get(self) -> Playable:
        if not self:
            raise QueueEmpty("There are no items currently in this queue.")

        return self._queue.popleft()

    def get(self) -> Playable:
        return self._get()

    def _check_atomic(self, item: list[Playable] | Playlist) -> None:
        for track in item:
            self._check_compatability(track)

    def _put(self, item: Playable) -> None:
        self._check_compatability(item)
        self._queue.append(item)

    def put(self, item: Playable | Playlist, /, *, atomic: bool = True) -> int:
        added: int = 0

        if isinstance(item, Playlist):
            if atomic:
                self._check_atomic(item)

            for track in item:
                try:
                    self._put(track)
                    added += 1
                except TypeError:
                    pass

        else:
            self._put(item)
            added += 1

        return added


class Queue(_Queue):
    def __init__(self) -> None:
        super().__init__()
        self.history: _Queue = _Queue()

        self._waiters: deque[asyncio.Future[None]] = deque()
        self._finished: asyncio.Event = asyncio.Event()
        self._finished.set()

        self._lock: asyncio.Lock = asyncio.Lock()

    def __str__(self) -> str:
        return ", ".join([f'"{p}"' for p in self])

    def __repr__(self) -> str:
        return f"Queue(items={len(self)}, history={self.history!r})"

    def _wakeup_next(self) -> None:
        while self._waiters:
            waiter = self._waiters.popleft()

            if not waiter.done():
                waiter.set_result(None)
                break

    def _get(self) -> Playable:
        # TODO ... Looping Logic, history Logic.
        return super()._get()

    def get(self) -> Playable:
        return self._get()

    async def get_wait(self) -> Playable:
        while not self:
            loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
            waiter: asyncio.Future[None] = loop.create_future()

            self._waiters.append(waiter)

            try:
                await waiter
            except:  # noqa
                waiter.cancel()

                try:
                    self._waiters.remove(waiter)
                except ValueError:  # pragma: no branch
                    pass

                if self and not waiter.cancelled():  # pragma: no cover
                    # something went wrong with this waiter, move on to next
                    self._wakeup_next()
                raise

        return self.get()

    def put(self, item: Playable | Playlist, /, *, atomic: bool = True) -> int:
        added: int = super().put(item, atomic=atomic)

        self._wakeup_next()
        return added

    async def put_wait(self, item: list[Playable] | Playable | Playlist, /, *, atomic: bool = True) -> int:
        added: int = 0

        async with self._lock:
            if isinstance(item, (list, Playlist)):
                if atomic:
                    super()._check_atomic(item)

                for track in item:
                    try:
                        super()._put(track)
                        added += 1
                    except TypeError:
                        pass

                    await asyncio.sleep(0)

            else:
                super()._put(item)
                added += 1
                await asyncio.sleep(0)

        self._wakeup_next()
        return added

    async def delete(self, index: int, /) -> None:
        async with self._lock:
            self._queue.__delitem__(index)
