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
import random
from collections import deque
from collections.abc import Iterable, Iterator
from typing import SupportsIndex, TypeGuard, overload

from .enums import QueueMode
from .exceptions import QueueEmpty
from .tracks import Playable, Playlist

__all__ = ("Queue",)


class Queue:
    """The default custom wavelink Queue designed specifically for :class:`wavelink.Player`.

    .. container:: operations

        .. describe:: str(queue)

            A string representation of this queue.

        .. describe:: repr(queue)

            The official string representation of this queue.

        .. describe:: if queue

            Bool check whether this queue has items or not.

        .. describe:: queue(track)

            Put a track in the queue.

        .. describe:: len(queue)

            The amount of tracks in the queue.

        .. describe:: queue[1]

            Peek at an item in the queue. Does not change the queue.

        .. describe:: for item in queue

            Iterate over the queue.

        .. describe:: if item in queue

            Check whether a specific track is in the queue.

    Attributes
    ----------
    history: :class:`wavelink.Queue`
        A queue of tracks that have been added to history.
    """

    def __init__(self, *, max_retention: int = 500, history: bool = True) -> None:
        self._items: list[Playable] = []
        self.max_retention = max_retention

        self._history: Queue | None = None if not history else Queue(history=False)
        self._mode: QueueMode = QueueMode.normal
        self._loaded: Playable | None = None

        self._waiters: deque[asyncio.Future[None]] = deque()
        self._lock = asyncio.Lock()

    @property
    def mode(self) -> QueueMode:
        """Property which returns a :class:`~wavelink.QueueMode` indicating which mode the
        :class:`~wavelink.Queue` is in.

        This property can be set with any :class:`~wavelink.QueueMode`.

        .. versionadded:: 3.0.0
        """
        return self._mode

    @mode.setter
    def mode(self, value: QueueMode) -> None:
        self._mode = value

    @property
    def history(self) -> Queue | None:
        return self._history

    @property
    def count(self) -> int:
        """The queue member count."""

        return len(self)

    @property
    def is_empty(self) -> bool:
        """Whether the queue has no members."""

        return not bool(self)

    def __str__(self) -> str:
        return ", ".join([f'"{p}"' for p in self])

    def __repr__(self) -> str:
        return f"Queue(items={len(self)}, history={self.history!r})"

    def __call__(self, item: Playable) -> None:
        self.put(item)

    def __bool__(self) -> bool:
        return bool(self._items)

    @overload
    def __getitem__(self, __index: SupportsIndex, /) -> Playable:
        ...

    @overload
    def __getitem__(self, __index: slice, /) -> list[Playable]:
        ...

    def __getitem__(self, __index: SupportsIndex | slice, /) -> Playable | list[Playable]:
        return self._items[__index]

    @overload
    def __setitem__(self, __index: SupportsIndex, __value: Playable, /) -> None:
        ...

    @overload
    def __setitem__(self, __index: slice, __value: Iterable[Playable], /) -> None:
        ...

    def __setitem__(self, __index: SupportsIndex | slice, __value: Playable | Iterable[Playable], /) -> None:
        self._items[__index] = __value

    def __delitem__(self, __index: int | slice, /) -> None:
        del self._items[__index]

    def __contains__(self, __other: Playable) -> bool:
        return __other in self._items

    def __len__(self) -> int:
        return len(self._items)

    def __reversed__(self) -> Iterator[Playable]:
        return reversed(self._items)

    def __iter__(self) -> Iterator[Playable]:
        return iter(self._items)

    def _wakeup_next(self) -> None:
        while self._waiters:
            waiter = self._waiters.popleft()

            if not waiter.done():
                waiter.set_result(None)
                break

    @staticmethod
    def _check_compatability(item: object) -> TypeGuard[Playable]:
        if not isinstance(item, Playable):
            raise TypeError("This queue is restricted to Playable objects.")
        return True

    @classmethod
    def _check_atomic(cls, item: Iterable[object]) -> TypeGuard[Iterable[Playable]]:
        for track in item:
            cls._check_compatability(track)
        return True

    def get(self) -> Playable:
        """Retrieve a track from the left side of the queue. E.g. the first.

        This method does not block.

        Returns
        -------
        :class:`wavelink.Playable`
            The track retrieved from the queue.

        Raises
        ------
        QueueEmpty
            The queue was empty when retrieving a track.
        """

        if self.mode is QueueMode.loop and self._loaded:
            return self._loaded

        if self.mode is QueueMode.loop_all and not self:
            assert self.history is not None

            self._items.extend(self.history._items)
            self.history.clear()

        if not self:
            raise QueueEmpty("There are no items currently in this queue.")

        track: Playable = self._items.pop(0)
        self._loaded = track

        return track

    def get_at(self, index: int, /) -> Playable:
        """Retrieve a track from the queue at a given index.

        Parameters
        ----------
        index: int
            The index of the track to get.

        Returns
        -------
        :class:`wavelink.Playable`
            The track retrieved from the queue.

        Raises
        ------
        QueueEmpty
            The queue was empty when retrieving a track.
        IndexError
            The index was out of range for the current queue.
        """

        if not self:
            raise QueueEmpty("There are no items currently in this queue.")

        return self._items.pop(index)

    def put_at(self, index: int, value: Playable, /) -> None:
        """Put a track into the queue at a given index.

        .. note::

            This method doesn't replace the track at the index but rather inserts one there.

        Parameters
        ----------
        index: int
            The index to put the track at.
        value: :class:`wavelink.Playable`
            The track to put.
        """

        self._items.insert(index, value)

    async def get_wait(self) -> Playable:
        """This method returns the first :class:`wavelink.Playable` if one is present or
        waits indefinitely until one is.

        This method is asynchronous.

        Returns
        -------
        :class:`wavelink.Playable`
            The track retrieved from the queue.
        """

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
        """Put an item into the end of the queue.

        Accepts a :class:`wavelink.Playable` or :class:`wavelink.Playlist`.

        Parameters
        ----------
        item: :class:`wavelink.Playable` | :class:`wavelink.Playlist`
            The item to enter into the queue.
        atomic: bool
            Whether the items should be inserted atomically. If set to ``True`` this method won't enter any tracks if
            it encounters an error. Defaults to ``True``.

        Returns
        -------
        int
            The number of tracks added to the queue.
        """

        added = 0

        if isinstance(item, Iterable):
            if atomic:
                self._check_atomic(item)
                self._items.extend(item)
                added = len(item)
            else:

                def try_compatibility(track: object) -> bool:
                    try:
                        return self._check_compatability(track)
                    except TypeError:
                        return False

                passing_items = [track for track in item if try_compatibility(track)]
                self._items.extend(passing_items)
                added = len(passing_items)
        else:
            self._check_compatability(item)
            self._items.append(item)
            added = 1

        self._wakeup_next()

        return added

    async def put_wait(self, item: list[Playable] | Playable | Playlist, /, *, atomic: bool = True) -> int:
        """Put an item or items into the end of the queue asynchronously.

        Accepts a :class:`wavelink.Playable` or :class:`wavelink.Playlist` or list[:class:`wavelink.Playable`].

        .. note::

            This method implements a lock to preserve insert order.

        Parameters
        ----------
        item: :class:`wavelink.Playable` | :class:`wavelink.Playlist` | list[:class:`wavelink.Playable`]
            The item or items to enter into the queue.
        atomic: bool
            Whether the items should be inserted atomically. If set to ``True`` this method won't enter any tracks if
            it encounters an error. Defaults to ``True``.

        Returns
        -------
        int
            The number of tracks added to the queue.
        """

        added: int = 0

        async with self._lock:
            if isinstance(item, Iterable):
                if atomic:
                    self._check_atomic(item)
                    self._items.extend(item)
                    return len(item)

                for track in item:
                    try:
                        self._check_compatability(track)
                    except TypeError:
                        pass
                    else:
                        self._items.append(track)
                        added += 1

                    await asyncio.sleep(0)

            else:
                self._check_compatability(item)
                self._items.append(item)
                added += 1
                await asyncio.sleep(0)

        self._wakeup_next()
        return added

    def delete(self, index: int, /) -> None:
        """Method to delete an item in the queue by index.

        Raises
        ------
        IndexError
            No track exists at this index.

        Examples
        --------

        .. code:: python3

            queue.delete(1)
            # Deletes the track at index 1 (The second track).
        """

        del self._items[index]

    def peek(self, index: int, /) -> Playable:
        if not self:
            raise QueueEmpty("There are no items currently in this queue.")

        return self[index]

    def swap(self, first: int, second: int, /) -> None:
        self[first], self[second] = self[second], self[first]

    def index(self, item: Playable, /) -> int:
        return self._items.index(item)

    def shuffle(self) -> None:
        """Shuffles the queue in place. This does **not** return anything.

        Example
        -------

        .. code:: python3

            player.queue.shuffle()
            # Your queue has now been shuffled...
        """

        random.shuffle(self._items)

    def clear(self) -> None:
        """Remove all items from the queue.

        .. note::

            This does not reset the queue.

        Example
        -------
        .. code:: python3

            player.queue.clear()
            # Your queue is now empty...
        """

        self._items.clear()

    def copy(self) -> Queue:
        """Return a shallow copy of the queue."""

        copy_queue = Queue(max_retention=self.max_retention, history=self.history is not None)
        copy_queue._items = self._items.copy()
        return copy_queue

    def reset(self) -> None:
        self.clear()
        if self.history is not None:
            self.history.clear()

        for waiter in self._waiters:
            waiter.cancel()

        self._waiters.clear()

        self._mode: QueueMode = QueueMode.normal
        self._loaded = None

    def remove(self, item: Playable, /, count: int = 1) -> int:
        deleted_count = 0
        for track in reversed(self):
            if deleted_count >= count:
                break
            if item == track:
                del track
                deleted_count += 1
        return deleted_count
