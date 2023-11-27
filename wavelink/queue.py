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
from collections.abc import Iterator
from typing import overload

from .enums import QueueMode
from .exceptions import QueueEmpty
from .tracks import Playable, Playlist

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

    def __contains__(self, item: object) -> bool:
        return item in self._queue

    @staticmethod
    def _check_compatability(item: object) -> None:
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

        Even though the history queue is the same class as this Queue some differences apply.
        Mainly you can not set the ``mode``.
    """

    def __init__(self, history: bool = True) -> None:
        super().__init__()
        self.history: Queue | None = None

        if history:
            self.history = Queue(history=False)

        self._loaded: Playable | None = None
        self._mode: QueueMode = QueueMode.normal
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
        if self.mode is QueueMode.loop and self._loaded:
            return self._loaded

        if self.mode is QueueMode.loop_all and not self:
            assert self.history is not None

            self._queue.extend(self.history._queue)
            self.history.clear()

        track: Playable = super()._get()
        self._loaded = track

        return track

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
        return self._get()

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

        Accepts a :class:`wavelink.Playable` or :class:`wavelink.Playlist`

        Parameters
        ----------
        item: :class:`wavelink.Playable` | :class:`wavelink.Playlist`
            The item to enter into the queue.
        atomic: bool
            Whether the items should be inserted atomically. If set to ``True`` this method won't enter any tracks if
            it encounters an error. Defaults to ``True``


        Returns
        -------
        int
            The amount of tracks added to the queue.
        """
        added: int = super().put(item, atomic=atomic)

        self._wakeup_next()
        return added

    async def put_wait(self, item: list[Playable] | Playable | Playlist, /, *, atomic: bool = True) -> int:
        """Put an item or items into the end of the queue asynchronously.

        Accepts a :class:`wavelink.Playable` or :class:`wavelink.Playlist` or list[:class:`wavelink.Playable`]

        .. note::

            This method implements a lock to preserve insert order.

        Parameters
        ----------
        item: :class:`wavelink.Playable` | :class:`wavelink.Playlist` | list[:class:`wavelink.Playable`]
            The item or items to enter into the queue.
        atomic: bool
            Whether the items should be inserted atomically. If set to ``True`` this method won't enter any tracks if
            it encounters an error. Defaults to ``True``


        Returns
        -------
        int
            The amount of tracks added to the queue.
        """
        added: int = 0

        async with self._lock:
            if isinstance(item, list | Playlist):
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
        """Method to delete an item in the queue by index.

        This method is asynchronous and implements/waits for a lock.

        Raises
        ------
        IndexError
            No track exists at this index.


        Examples
        --------

        .. code:: python3

            await queue.delete(1)
            # Deletes the track at index 1 (The second track).
        """
        async with self._lock:
            self._queue.__delitem__(index)

    def shuffle(self) -> None:
        """Shuffles the queue in place. This does **not** return anything.

        Example
        -------

        .. code:: python3

            player.queue.shuffle()
            # Your queue has now been shuffled...
        """
        random.shuffle(self._queue)

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
        self._queue.clear()

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
        if not hasattr(self, "_mode"):
            raise AttributeError("This queues mode can not be set.")

        self._mode = value
