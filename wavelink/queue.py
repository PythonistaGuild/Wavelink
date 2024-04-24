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

    .. note::

        :class:`~wavelink.Player` implements this queue by default.
        You can access it via :attr:`wavelink.Player.queue`.

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

        .. describe:: queue[1] = track

            Set a track in the queue at a specific index.

        .. describe:: del queue[1]

            Delete a track from the queue at a specific index.

        .. describe:: reversed(queue)

            Return a reversed iterator of the queue.

    Attributes
    ----------
    history: :class:`wavelink.Queue`
        A queue of tracks that have been added to history. Tracks are added to history when they are played.
    """

    def __init__(self, *, history: bool = True) -> None:
        self._items: list[Playable] = []

        self._history: Queue | None = Queue(history=False) if history else None
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
        """The queue member count.

        Returns
        -------
        int
            The amount of tracks in the queue.


        .. versionadded:: 3.2.0
        """

        return len(self)

    @property
    def is_empty(self) -> bool:
        """Whether the queue has no members.

        Returns
        -------
        bool
            Whether the queue is empty.


        .. versionadded:: 3.2.0
        """

        return not bool(self)

    def __str__(self) -> str:
        joined: str = ", ".join([f'"{p}"' for p in self])
        return f"Queue([{joined}])"

    def __repr__(self) -> str:
        return f"Queue(items={len(self)}, history={self.history!r})"

    def __call__(self, item: Playable) -> None:
        self.put(item)

    def __bool__(self) -> bool:
        return bool(self._items)

    @overload
    def __getitem__(self, __index: SupportsIndex, /) -> Playable: ...

    @overload
    def __getitem__(self, __index: slice, /) -> list[Playable]: ...

    def __getitem__(self, __index: SupportsIndex | slice, /) -> Playable | list[Playable]:
        return self._items[__index]

    def __setitem__(self, __index: SupportsIndex, __value: Playable, /) -> None:
        self._check_compatibility(__value)
        self._items[__index] = __value
        self._wakeup_next()

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
    def _check_compatibility(item: object) -> TypeGuard[Playable]:
        if not isinstance(item, Playable):
            raise TypeError("This queue is restricted to Playable objects.")
        return True

    @classmethod
    def _check_atomic(cls, item: Iterable[object]) -> TypeGuard[Iterable[Playable]]:
        for track in item:
            cls._check_compatibility(track)
        return True

    def get(self) -> Playable:
        """Retrieve a track from the left side of the queue. E.g. the first.

        This method does not block.

        .. warning::

            Due to the way the queue loop works, this method will return the same track if the queue is in loop mode.
            You can use :meth:`wavelink.Player.skip` with ``force=True`` to skip the current track.

            Do **NOT** use this method to remove tracks from the queue, use either:

            - ``del queue[index]``
            - :meth:`wavelink.Queue.remove`
            - :meth:`wavelink.Queue.delete`


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

        .. warning::

            Due to the way the queue loop works, this method will load the retrieved track for looping.

            Do **NOT** use this method to remove tracks from the queue, use either:

            - ``del queue[index]``
            - :meth:`wavelink.Queue.remove`
            - :meth:`wavelink.Queue.delete`

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


        .. versionadded:: 3.2.0
        """

        if not self:
            raise QueueEmpty("There are no items currently in this queue.")

        track: Playable = self._items.pop(index)
        self._loaded = track

        return track

    def put_at(self, index: int, value: Playable, /) -> None:
        """Put a track into the queue at a given index.

        .. note::

            This method doesn't replace the track at the index but rather inserts one there, similar to a list.

        Parameters
        ----------
        index: int
            The index to put the track at.
        value: :class:`wavelink.Playable`
            The track to put.

        Raises
        ------
        TypeError
            The track was not a :class:`wavelink.Playable`.


        .. versionadded:: 3.2.0
        """
        self._check_compatibility(value)
        self._items.insert(index, value)
        self._wakeup_next()

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
            except:
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

    def put(self, item: list[Playable] | Playable | Playlist, /, *, atomic: bool = True) -> int:
        """Put an item into the end of the queue.

        Accepts a :class:`wavelink.Playable`, :class:`wavelink.Playlist` or list[:class:`wavelink.Playble`].

        Parameters
        ----------
        item: :class:`wavelink.Playable` | :class:`wavelink.Playlist` | list[:class:`wavelink.Playble`]
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
                        return self._check_compatibility(track)
                    except TypeError:
                        return False

                passing_items = [track for track in item if try_compatibility(track)]
                self._items.extend(passing_items)
                added = len(passing_items)
        else:
            self._check_compatibility(item)
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
                    self._wakeup_next()
                    return len(item)

                for track in item:
                    try:
                        self._check_compatibility(track)
                    except TypeError:
                        pass
                    else:
                        self._items.append(track)
                        added += 1

                    await asyncio.sleep(0)

            else:
                self._check_compatibility(item)
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

            # Deletes the track at index 1 (The second track).
            queue.delete(1)


        .. versionchanged:: 3.2.0

            The method is no longer a coroutine.
        """

        del self._items[index]

    def peek(self, index: int = 0, /) -> Playable:
        """Method to peek at an item in the queue by index.

        .. note::

            This does not change the queue or remove the item.

        Parameters
        ----------
        index: int
            The index to peek at. Defaults to ``0`` which is the next item in the queue.

        Returns
        -------
        :class:`wavelink.Playable`
            The track at the given index.

        Raises
        ------
        QueueEmpty
            There are no items currently in this queue.
        IndexError
            No track exists at the given index.


        .. versionadded:: 3.2.0
        """
        if not self:
            raise QueueEmpty("There are no items currently in this queue.")

        return self[index]

    def swap(self, first: int, second: int, /) -> None:
        """Swap two items in the queue by index.

        Parameters
        ----------
        first: int
            The first index to swap with.
        second: int
            The second index to swap with.

        Returns
        -------
        None

        Raises
        ------
        IndexError
            No track exists at the given index.

        Example
        -------

        .. code:: python3

            # Swap the first and second tracks in the queue.
            queue.swap(0, 1)


        .. versionadded:: 3.2.0
        """
        self[first], self[second] = self[second], self[first]

    def index(self, item: Playable, /) -> int:
        """Return the index of the first occurence of a :class:`wavelink.Playable` in the queue.

        Parameters
        ----------
        item: :class:`wavelink.Playable`
            The item to search the index for.

        Returns
        -------
        int
            The index of the item in the queue.

        Raises
        ------
        ValueError
            The item was not found in the queue.


        .. versionadded:: 3.2.0
        """
        return self._items.index(item)

    def shuffle(self) -> None:
        """Shuffles the queue in place. This does **not** return anything.

        Example
        -------

        .. code:: python3

            player.queue.shuffle()
            # Your queue has now been shuffled...

        Returns
        -------
        None
        """

        random.shuffle(self._items)

    def clear(self) -> None:
        """Remove all items from the queue.

        .. note::

            This does not reset the queue or clear history. Use this method on queue.history to clear history.

        Example
        -------
        .. code:: python3

            player.queue.clear()
            # Your queue is now empty...

        Returns
        -------
        None
        """

        self._items.clear()

    def copy(self) -> Queue:
        """Create a shallow copy of the queue.

        Returns
        -------
        :class:`wavelink.Queue`
            A shallow copy of the queue.
        """

        copy_queue = Queue(history=self.history is not None)
        copy_queue._items = self._items.copy()
        return copy_queue

    def reset(self) -> None:
        """Reset the queue to its default state. This will clear the queue and history.

        .. note::

            This will cancel any waiting futures on the queue. E.g. :meth:`wavelink.Queue.get_wait`.

        Returns
        -------
        None
        """
        self.clear()
        if self.history is not None:
            self.history.clear()

        for waiter in self._waiters:
            waiter.cancel()

        self._waiters.clear()

        self._mode: QueueMode = QueueMode.normal
        self._loaded = None

    def remove(self, item: Playable, /, count: int | None = 1) -> int:
        """Remove a specific track from the queue up to a given count or all instances.

        .. note::

            This method starts from the left hand side of the queue E.g. the beginning.

        .. warning::

            Setting count to ``<= 0`` is equivalent to setting it to ``1``.

        Parameters
        ----------
        item: :class:`wavelink.Playable`
            The item to remove from the queue.
        count: int
            The amount of times to remove the item from the queue. Defaults to ``1``.
            If set to ``None`` this will remove all instances of the item.

        Returns
        -------
        int
            The amount of times the item was removed from the queue.

        Raises
        ------
        ValueError
            The item was not found in the queue.


        .. versionadded:: 3.2.0
        """
        deleted_count: int = 0

        for track in self._items.copy():
            if track == item:
                self._items.remove(track)
                deleted_count += 1

                if count is not None and deleted_count >= count:
                    break

        return deleted_count

    @property
    def loaded(self) -> Playable | None:
        """The currently loaded track that will repeat when the queue is set to :attr:`wavelink.QueueMode.loop`.

        This track will be retrieved when using :meth:`wavelink.Queue.get` if the queue is in loop mode.
        You can unload the track by setting this property to ``None`` or by using :meth:`wavelink.Player.skip` with
        ``force=True``.

        Setting this property to a new :class:`wavelink.Playable` will replace the currently loaded track, but will not
        add it to the queue; or history until the track is played.

        Returns
        -------
        :class:`wavelink.Playable` | None
            The currently loaded track or ``None`` if there is no track ready to repeat.

        Raises
        ------
        TypeError
            The track was not a :class:`wavelink.Playable` or ``None``.


        .. versionadded:: 3.2.0
        """
        return self._loaded

    @loaded.setter
    def loaded(self, value: Playable | None) -> None:
        if value is not None:
            self._check_compatibility(value)

        self._loaded = value
