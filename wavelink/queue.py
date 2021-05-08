"""MIT License

Copyright (c) 2019-2021 PythonistaGuild

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
from copy import copy
from typing import AsyncIterator, Iterable, Iterator, List, Optional, Union

from .abc import Playable
from .errors import *


class Queue(Iterable[Playable]):
    """
    Basic Queue implementation for Playable objects.

    `max_size=None` allows for no maximum.

    `overflow=False` sets QueueFull to be raised when max_size is reached.

    Pass alternative queue containers to `queue_cls` to replace default of `collections.deque`.
    """

    __slots__ = ("max_size", "_queue", "_overflow")

    def __init__(self, max_size: Optional[int] = None, *, overflow=True, queue_cls: type = deque):
        self.max_size = max_size
        self._queue = queue_cls()
        self._overflow = overflow

    def __str__(self) -> str:
        """String showing all members appearing as a list."""
        return str(list(f"'{t}'" for t in self))

    def __repr__(self) -> str:
        """Official representation with max_size and member count. <BaseQueue max_size=None members=32>"""
        return f"<{self.__class__.__name__} max_size={self.max_size} members={self.count}>"

    def __bool__(self) -> bool:
        """Treats the queue as a bool, with it evaluating True when it contains members."""
        return bool(self.count)

    def __call__(self, item):
        """Allows the queue instance to be called directly in order to add a member."""
        self.put(item)

    def __len__(self) -> int:
        """Return the number of members in the queue."""
        return self.count

    def __getitem__(self, index: int) -> Playable:
        """Returns a member at the given position.

        Does not remove item from queue.
        """
        if not isinstance(index, int):
            raise ValueError("'int' type required.'")

        return self._queue[index]

    def __setitem__(self, index: int, item: Playable):
        """Inserts an item at given position."""
        if not isinstance(index, int):
            raise ValueError("'int' type required.'")

        self.put_at_index(index, item)

    def __delitem__(self, index: int):
        """Delete item at given position."""
        self._queue.__delitem__(index)

    def __iter__(self) -> Iterator[Playable]:
        """Iterate over members in the queue.

        Does not remove items when iterating.
        """
        return self._queue.__iter__()

    def __reversed__(self) -> Iterator[Playable]:
        """Iterate over members in reverse order."""
        return self._queue.__reversed__()

    def __contains__(self, item: Playable) -> bool:
        """Check if an item is a member of the queue."""
        return item in self._queue

    def __add__(self, other: Iterable[Playable]) -> Queue:
        """Return a new queue containing all members.

        The new queue will have the same max_size as the original.
        """
        if not isinstance(other, Iterable):
            raise TypeError(f"Adding with the '{type(other)}' type is not supported.")

        new_queue = self.copy()
        new_queue.extend(other)
        return new_queue

    def __iadd__(self, other: Union[Iterable[Playable], Playable]) -> Queue:
        """Add items to queue."""
        if isinstance(other, Playable):
            self.put(other)
            return self

        if isinstance(other, Iterable):
            self.extend(other)
            return self

        raise TypeError(f"Adding '{type(other)}' type to the queue is not supported.")

    def _get(self):
        """Get an item from the internal queue.

        Suitable for overriding in subclasses to change get behaviour.
        """
        return self._queue.popleft()

    def _drop(self) -> Playable:
        """Drop an item from the end of the internal queue.

        Suitable for overriding in subclasses to change drop behaviour.
        """
        return self._queue.pop()

    def _index(self, item: Playable) -> int:
        """Get the index of an item in the internal queue.

        Suitable for overriding in subclasses to change index behaviour.
        """
        return self._queue.index(item)

    def _put(self, item: Playable):
        """Add an item to the internal queue.

        Suitable for overriding in subclasses to change put behaviour.
        """
        self._queue.append(item)

    def _insert(self, index: int, item: Playable):
        """Inserts an item at a given index to the internal queue.

        Suitable for overriding in subclasses to change insert behaviour.
        """
        self._queue.insert(index, item)

    @staticmethod
    def _check_playable(item) -> Playable:
        """Check if an item is a Playable object."""
        if not isinstance(item, Playable):
            raise TypeError("Only Playable objects are supported.")

        return item

    @classmethod
    def _check_playable_container(cls, iterable: Iterable) -> List[Playable]:
        """Check if an iterable has only Playable objects."""
        iterable = list(iterable)
        for item in iterable:
            cls._check_playable(item)

        return iterable

    @property
    def count(self) -> int:
        """Returns queue member count."""
        return len(self._queue)

    @property
    def is_empty(self) -> bool:
        """Returns True if queue has no members."""
        return not bool(self.count)

    @property
    def is_full(self) -> bool:
        """Returns True if queue item count has reached max_size."""
        return False if self.max_size is None else self.count >= self.max_size

    def get(self) -> Playable:
        """Return next immediately available item in queue if any.

        Raises QueueEmpty if no items in queue.
        """
        if self.is_empty:
            raise QueueEmpty("No items in the queue.")

        return self._get()

    def find_position(self, item: Playable) -> int:
        """Find the position a given item within the queue.

        Raises ValueError if item is not in queue.
        """
        return self._index(self._check_playable(item))

    def put(self, item):
        """Put the given item into the back of the queue."""
        if self.is_full:
            if not self._overflow:
                raise QueueFull(f"Queue max_size of {self.max_size} has been reached.")

            self._drop()

        return self._put(self._check_playable(item))

    def put_at_index(self, index: int, item: Playable):
        """Put the given item into the queue at the specified index.
        """
        if self.is_full:
            if not self._overflow:
                raise QueueFull(f"Queue max_size of {self.max_size} has been reached.")

            self._drop()

        return self._insert(index, self._check_playable(item))

    def put_at_front(self, item):
        """Put the given item into the front of the queue."""
        return self.put_at_index(0, item)

    def extend(self, iterable: Iterable, *, atomic=True):
        """
        Add the members of the given iterable to the end of the queue.

        If atomic is set to True, no tracks will be added upon any exceptions.

        If atomic is set to False, as many tracks will be added as possible.

        When overflow is enabled for the queue, `atomic=True` won't prevent dropped items.
        """
        if atomic:
            iterable = self._check_playable_container(iterable)

            if not self._overflow and self.max_size is not None:
                new_len = len(iterable)

                if (new_len + self.count) > self.max_size:
                    raise QueueFull(
                        f"Queue has {self.count}/{self.max_size} items, "
                        f"cannot add {new_len} more."
                    )

        for item in iterable:
            self.put(item)

    def copy(self) -> Queue:
        """Create a copy of the current queue including it's members."""
        new_queue = self.__class__(max_size=self.max_size)
        new_queue._queue = copy(self._queue)

        return new_queue

    def clear(self):
        """Remove all items from the queue."""
        self._queue.clear()


class WaitQueue(Queue):
    """
    Queue for Playable objects designed for Player that allows waiting for new items with `get_wait`.

    `max_size=None` allows for no maximum.

    Pass alternative history queues to `history_cls` to replace default of `Queue`.
    """

    __slots__ = ("history", "_waiters", "_finished")

    def __init__(self, max_size: Optional[int] = None, history_max_size: Optional[int] = None, history_cls=Queue):
        super().__init__(max_size, overflow=False)
        self.history = history_cls(history_max_size)

        self._waiters = deque()
        self._finished = asyncio.Event()
        self._finished.set()

    async def __aiter__(self) -> AsyncIterator[Playable]:
        """Pops members as it iterates the queue, waiting for new members when exhausted.

        Removes items when iterating.
        """
        while True:
            yield await self.get_wait()

    def _get(self) -> Playable:
        """Get an item from the end of the internal queue and adds item to history queue."""
        item = super()._get()
        self.history.put(item)

        return item

    def _put(self, item):
        """Add an item to the internal queue and wake up next waiter."""
        super()._put(item)
        self._wakeup_next()

    def _insert(self, index: int, item: Playable):
        """Inserts an item at a given index to the internal queue.

        Suitable for overriding in subclasses to change insert behaviour.
        """
        super()._queue.insert(index, item)
        self._wakeup_next()

    def _wakeup_next(self):
        """Wake up next get waiter."""
        while self._waiters:
            waiter = self._waiters.popleft()
            if not waiter.done():
                waiter.set_result(None)
                break

    async def get_wait(self) -> Playable:
        """Return the next item in queue once available."""
        while self.is_empty:
            loop = asyncio.get_event_loop()
            waiter = loop.create_future()

            self._waiters.append(waiter)

            try:
                await waiter
            except:  # noqa
                waiter.cancel()

                try:
                    self._waiters.remove(waiter)
                except ValueError:  # pragma: no branch
                    pass

                if not self.is_empty and not waiter.cancelled():  # pragma: no cover
                    # something went wrong with this waiter, move on to next
                    self._wakeup_next()
                raise

        return self.get()

    async def put_wait(self, item: Playable):
        """Put an item into the queue using await."""
        self._put(item)
        await asyncio.sleep(0)

    def reset(self):
        """Clears the state of all queues."""
        self.clear()
        self.history.clear()

        for waiter in self._waiters:
            waiter.cancel()

        self._waiters.clear()

    def shuffle(self):
        """Rearrange items in queue to be in a random-like order."""
        pass
