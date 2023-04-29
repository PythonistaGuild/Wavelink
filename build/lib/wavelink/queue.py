"""
MIT License

Copyright (c) 2019-Present PythonistaGuild

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
from collections.abc import AsyncIterator, Iterable, Iterator
from copy import copy

from .exceptions import QueueEmpty
from .tracks import Playable
from .ext import spotify


__all__ = (
    'BaseQueue',
    'Queue'
)


class BaseQueue:

    def __init__(self) -> None:
        self._queue: deque[Playable, spotify.SpotifyTrack] = deque()

    def __str__(self) -> str:
        """String showing all Playable objects appearing as a list."""
        return str([f"'{t}'" for t in self])

    def __repr__(self) -> str:
        """Official representation with max_size and member count."""
        return (
            f"Wavelink Queue: members={self.count}")

    def __bool__(self) -> bool:
        """Treats the queue as a bool, with it evaluating True when it contains members."""
        return bool(self.count)

    def __call__(self, item: Playable | spotify.SpotifyTrack) -> None:
        """Allows the queue instance to be called directly in order to add a member."""
        self.put(item)

    def __len__(self) -> int:
        """Return the number of members in the queue."""
        return self.count

    def __getitem__(self, index: int) -> Playable | spotify.SpotifyTrack:
        """Returns a member at the given position.

        Does not remove item from queue.
        """
        if not isinstance(index, int):
            raise ValueError("'int' type required.'")

        return self._queue[index]

    def __setitem__(self, index: int, item: Playable | spotify.SpotifyTrack):
        """Inserts an item at given position."""
        if not isinstance(index, int):
            raise ValueError("'int' type required.'")

        self.put_at_index(index, item)

    def __delitem__(self, index: int) -> None:
        """Delete item at given position."""
        self._queue.__delitem__(index)

    def __iter__(self) -> Iterator[Playable | spotify.SpotifyTrack]:
        """Iterate over members in the queue.
        Does not remove items when iterating.
        """
        return self._queue.__iter__()

    def __reversed__(self) -> Iterator[Playable | spotify.SpotifyTrack]:
        """Iterate over members in reverse order."""
        return self._queue.__reversed__()

    def __contains__(self, item: Playable | spotify.SpotifyTrack) -> bool:
        """Check if an item is a member of the queue."""
        return item in self._queue

    def __add__(self, other: Iterable[Playable | spotify.SpotifyTrack]):
        """Return a new queue containing all members.

        The new queue will have the same max_size as the original.
        """
        if not isinstance(other, Iterable):
            raise TypeError(f"Adding with the '{type(other)}' type is not supported.")

        new_queue = self.copy()
        new_queue.extend(other)
        return new_queue

    def __iadd__(self, other: Iterable[Playable] | Playable):
        """Add items to queue."""
        if isinstance(other, (Playable, spotify.SpotifyTrack)):
            self.put(other)

            return self

        if isinstance(other, Iterable):
            self.extend(other)
            return self

        raise TypeError(f"Adding '{type(other)}' type to the queue is not supported.")

    def _get(self) -> Playable | spotify.SpotifyTrack:
        if self.is_empty:
            raise QueueEmpty("No items currently in the queue.")

        return self._queue.popleft()

    def _drop(self) -> Playable | spotify.SpotifyTrack:
        return self._queue.pop()

    def _index(self, item: Playable | spotify.SpotifyTrack) -> int:
        return self._queue.index(item)

    def _put(self, item: Playable | spotify.SpotifyTrack) -> None:
        self._queue.append(item)

    def _insert(self, index: int, item: Playable | spotify.SpotifyTrack) -> None:
        self._queue.insert(index, item)

    @staticmethod
    def _check_playable(item: Playable | spotify.SpotifyTrack) -> Playable | spotify.SpotifyTrack:
        if not isinstance(item, (Playable, spotify.SpotifyTrack)):
            raise TypeError("Only Playable objects are supported.")

        return item

    @classmethod
    def _check_playable_container(cls, iterable: Iterable) -> list[Playable | spotify.SpotifyTrack]:
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

    def get(self) -> Playable | spotify.SpotifyTrack:
        """Return next immediately available item in queue if any.

        Raises QueueEmpty if no items in queue.
        """
        if self.is_empty:
            raise QueueEmpty("No items currently in the queue.")

        return self._get()

    def pop(self) -> Playable | spotify.SpotifyTrack:
        """Return item from the right end side of the queue.

        Raises QueueEmpty if no items in queue.
        """
        if self.is_empty:
            raise QueueEmpty("No items currently in the queue.")

        return self._queue.pop()

    def find_position(self, item: Playable | spotify.SpotifyTrack) -> int:
        """Find the position a given item within the queue.
        Raises ValueError if item is not in queue.
        """
        return self._index(self._check_playable(item))

    def put(self, item: Playable | spotify.SpotifyTrack) -> None:
        """Put the given item into the back of the queue."""
        self._put(self._check_playable(item))

    def put_at_index(self, index: int, item: Playable | spotify.SpotifyTrack) -> None:
        """Put the given item into the queue at the specified index."""
        self._insert(index, self._check_playable(item))

    def put_at_front(self, item: Playable | spotify.SpotifyTrack) -> None:
        """Put the given item into the front of the queue."""
        self.put_at_index(0, item)

    def extend(self, iterable: Iterable[Playable | spotify.SpotifyTrack], *, atomic: bool = True) -> None:
        """Add the members of the given iterable to the end of the queue.

        If atomic is set to True, no tracks will be added upon any exceptions.
        If atomic is set to False, as many tracks will be added as possible.

        """
        if atomic:
            iterable = self._check_playable_container(iterable)

        for item in iterable:
            self.put(item)

    def copy(self):
        """Create a copy of the current queue including its members."""
        new_queue = self.__class__()
        new_queue._queue = copy(self._queue)

        return new_queue

    def clear(self) -> None:
        """Remove all items from the queue."""
        self._queue.clear()


class Queue(BaseQueue):

    def __init__(self):
        super().__init__()
        self.history: BaseQueue = BaseQueue()

        self._loop: bool = False
        self._loop_all: bool = False

        self._loaded = None
        self._waiters = deque()
        self._finished = asyncio.Event()
        self._finished.set()

    async def __aiter__(self) -> AsyncIterator[Playable | spotify.SpotifyTrack]:
        """Pops members as it iterates the queue, waiting for new members when exhausted.

        Removes items when iterating.
        """
        while True:
            yield await self.get_wait()

    def get(self) -> Playable | spotify.SpotifyTrack:
        return self._get()

    def _get(self) -> Playable | spotify.SpotifyTrack:
        if self.loop and self._loaded:
            return self._loaded

        item = super()._get()
        if self.loop_all and self.is_empty:
            self._queue.extend(self.history._queue)
            self.history.clear()

        self._loaded = item
        self.history.put(item)

        return item

    def _put(self, item: Playable | spotify.SpotifyTrack) -> None:
        super()._put(item)
        self._wakeup_next()

    def _insert(self, index: int, item: Playable | spotify.SpotifyTrack) -> None:
        super()._insert(index, item)
        self._wakeup_next()

    def _wakeup_next(self) -> None:
        while self._waiters:
            waiter = self._waiters.popleft()

            if not waiter.done():
                waiter.set_result(None)
                break

    async def get_wait(self) -> Playable | spotify.SpotifyTrack:
        """|coro|

        Return the next item in queue once available.

        .. note::

            This will wait until an item is available to be retrieved.
        """
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

    async def put_wait(self, item: Playable | spotify.SpotifyTrack) -> None:
        """|coro|

        Put an item into the queue using await.
        """
        self._put(item)
        await asyncio.sleep(0)

    def reset(self) -> None:
        """Clears the state of all queues."""
        self.clear()
        self.history.clear()

        for waiter in self._waiters:
            waiter.cancel()

        self._waiters.clear()

        self._loaded = None
        self._loop = False
        self._loop_all = False

    @property
    def loop(self) -> bool:
        """Whether the queue will loop the currently playing song.

        Can be set to True or False.
        Defaults to False.

        Returns
        -------
        bool
        """
        return self._loop

    @loop.setter
    def loop(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise ValueError('The "loop" property can only be set with a bool.')

        self._loop = value

    @property
    def loop_all(self) -> bool:
        """Whether the queue will loop all songs in the history queue.

        Can be set to True or False.
        Defaults to False.

        .. note::

            If `loop` is set to True, this has no effect until `loop` is set to False.

        Returns
        -------
        bool
        """
        return self._loop_all

    @loop_all.setter
    def loop_all(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise ValueError('The "loop_all" property can only be set with a bool.')

        self._loop_all = value
