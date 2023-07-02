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
import random

from .exceptions import QueueEmpty
from .tracks import Playable, YouTubePlaylist, SoundCloudPlaylist
from .ext import spotify


__all__ = (
    'BaseQueue',
    'Queue'
)


class BaseQueue:
    """BaseQueue for wavelink.

    All queues inherit from this queue.

    See :class:`Queue` for the default :class:`~wavelink.Player` queue.
    Internally this queue uses a :class:`collections.deque`.

    .. warning::

        It is not advisable to edit the internal :class:`collections.deque` directly.


    .. container:: operations

        .. describe:: str(queue)

            Returns a string showing all Playable objects appearing as a list in the queue.

        .. describe:: repr(queue)

            Returns an official string representation of this queue.

        .. describe:: if queue

            Returns True if members are in the queue. False if the queue is empty.

        .. describe:: queue(track)

            Adds a member to the queue.

        .. describe:: len(queue)

            Returns an int with the count of members in this queue.

        .. describe:: queue[2]

            Returns a member at the given position.
            Does **not** remove the item from queue.

        .. describe:: queue[4] = track

            Inserts an item into the queue at the given position.

        .. describe:: del queue[1]

            Deletes a member from the queue at the given position.

        .. describe:: for track in queue

            Iterates over the queue.
            Does **not** remove items when iterating.

        .. describe:: reversed(queue)

            Reverse a reversed version of the queue.

        .. describe:: if track in queue

            Checks whether a track is in the queue.

        .. describe:: queue = queue + [track, track1, track2, ...]

            Return a new queue containing all new and old members from the given iterable.

        .. describe:: queue += [track, track1, track2, ...]

            Add items to queue from the given iterable.
    """

    def __init__(self) -> None:
        self._queue: deque[Playable, spotify.SpotifyTrack] = deque()

    def __str__(self) -> str:
        """String showing all Playable objects appearing as a list."""
        return str([f"'{t}'" for t in self])

    def __repr__(self) -> str:
        """Official representation displaying member count."""
        return (
            f"BaseQueue(member_count={self.count})")

    def __bool__(self) -> bool:
        """Treats the queue as a ``bool``, with it evaluating ``True`` when it contains members.

        Example
        -------

        .. code:: python3

            if player.queue:
                # queue contains members, do something...
        """
        return bool(self.count)

    def __call__(self, item: Playable | spotify.SpotifyTrack) -> None:
        """Allows the queue instance to be called directly in order to add a member.

        Example
        -------

        .. code:: python3

            player.queue(track)  # adds track to the queue...
        """
        self.put(item)

    def __len__(self) -> int:
        """Return the number of members in the queue.

        Example
        -------

        .. code:: python3

            print(len(player.queue))
        """
        return self.count

    def __getitem__(self, index: int) -> Playable | spotify.SpotifyTrack:
        """Returns a member at the given position.

        Does **not** remove the item from queue.

        Example
        -------

        .. code:: python3

            track = player.queue[2]
        """
        if not isinstance(index, int):
            raise ValueError("'int' type required.'")

        return self._queue[index]

    def __setitem__(self, index: int, item: Playable | spotify.SpotifyTrack):
        """Inserts an item at the given position.

        Example
        -------

        .. code:: python3

            player.queue[4] = track
        """
        if not isinstance(index, int):
            raise ValueError("'int' type required.'")

        self.put_at_index(index, item)

    def __delitem__(self, index: int) -> None:
        """Delete item at given position.

        Example
        -------

        .. code:: python3

            del player.queue[1]
        """
        self._queue.__delitem__(index)

    def __iter__(self) -> Iterator[Playable | spotify.SpotifyTrack]:
        """Iterate over members in the queue.

        Does **not** remove items when iterating.

        Example
        -------

        .. code:: python3

            for track in player.queue:
                print(track)
        """
        return self._queue.__iter__()

    def __reversed__(self) -> Iterator[Playable | spotify.SpotifyTrack]:
        """Iterate over members in a reverse order.

        Example
        -------

        .. code:: python3

            for track in reversed(player.queue):
                print(track)
        """
        return self._queue.__reversed__()

    def __contains__(self, item: Playable | spotify.SpotifyTrack) -> bool:
        """Check if a track is a member of the queue.

        Example
        -------

        .. code:: python3

            if track in player.queue:
                # track is in the queue...
        """
        return item in self._queue

    def __add__(self, other: Iterable[Playable | spotify.SpotifyTrack]):
        """Return a new queue containing all members, including old members.

        Example
        -------

        .. code:: python3

            player.queue = player.queue + [track1, track2, ...]
        """
        if not isinstance(other, Iterable):
            raise TypeError(f"Adding with the '{type(other)}' type is not supported.")

        new_queue = self.copy()
        new_queue.extend(other)
        return new_queue

    def __iadd__(self, other: Iterable[Playable] | Playable):
        """Add items to queue from an iterable.

        Example
        -------

        .. code:: python3

            player.queue += [track1, track2, ...]
        """
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
        """Returns ``True`` if queue has no members."""
        return not bool(self.count)

    def get(self) -> Playable | spotify.SpotifyTrack:
        """Return next immediately available item in queue if any.

        Raises :exc:`~wavelink.QueueEmpty` if no items in queue.
        """
        if self.is_empty:
            raise QueueEmpty("No items currently in the queue.")

        return self._get()

    def pop(self) -> Playable | spotify.SpotifyTrack:
        """Return item from the right end side of the queue.

        Raises :exc:`~wavelink.QueueEmpty` if no items in queue.
        """
        if self.is_empty:
            raise QueueEmpty("No items currently in the queue.")

        return self._queue.pop()

    def find_position(self, item: Playable | spotify.SpotifyTrack) -> int:
        """Find the position a given item within the queue.

        Raises :exc:`ValueError` if item is not in the queue.
        """
        return self._index(self._check_playable(item))

    def put(self, item: Playable | spotify.SpotifyTrack) -> None:
        """Put the given item into the back of the queue.

        If the provided ``item`` is a :class:`~wavelink.YouTubePlaylist` or :class:`~wavelink.SoundCloudPlaylist`, all
        tracks from this playlist will be put into the queue.


        .. note::

            Inserting playlists is currently only supported via this method, which means you can only insert them into
            the back of the queue. Future versions of wavelink may add support for inserting playlists from a specific
            index, or at the front of the queue.


        .. versionchanged:: 2.6.0

            Added support for directly adding a :class:`~wavelink.YouTubePlaylist` to the queue.
        """
        self._check_playable(item)

        if isinstance(item, (YouTubePlaylist, SoundCloudPlaylist)):
            for track in item.tracks:
                self._put(track)
        else:
            self._put(item)

    def put_at_index(self, index: int, item: Playable | spotify.SpotifyTrack) -> None:
        """Put the given item into the queue at the specified index."""
        self._insert(index, self._check_playable(item))

    def put_at_front(self, item: Playable | spotify.SpotifyTrack) -> None:
        """Put the given item into the front of the queue."""
        self.put_at_index(0, item)

    def shuffle(self) -> None:
        """Shuffles the queue in place. This does **not** return anything.

        Example
        -------

        .. code:: python3

            player.queue.shuffle()
            # Your queue has now been shuffled...


        .. versionadded:: 2.5
        """
        random.shuffle(self._queue)

    def extend(self, iterable: Iterable[Playable | spotify.SpotifyTrack], *, atomic: bool = True) -> None:
        """Add the members of the given iterable to the end of the queue.

        If atomic is set to ``True``, no tracks will be added upon any exceptions.

        If atomic is set to ``False``, as many tracks will be added as possible.
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
        """Remove all items from the queue.


        .. note::

            This does not reset the queue. See :meth:`~Queue.reset` for resetting the :class:`Queue` assigned to the
            player.
        """
        self._queue.clear()


class Queue(BaseQueue):
    """Main Queue class.

    **All** :class:`~wavelink.Player` have this queue assigned to them.

    .. note::

        This queue inherits from :class:`BaseQueue` but has access to special async methods and loop logic.

    .. warning::

        The :attr:`.history` queue is a :class:`BaseQueue` and has **no** access to async methods or loop logic.


    .. container:: operations

        .. describe:: async for track in queue

            Pops members as it iterates the queue asynchronously, waiting for new members when exhausted.
            **Does** remove items when iterating.


    Attributes
    ----------
    history: :class:`BaseQueue`
        The history queue stores information about all previous played tracks for the :class:`~wavelink.Player`'s
        session.
    """

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

        **Does** remove items when iterating.

        Example
        -------

        .. code:: python3

            async for track in player.queue:
                # If there is no item in the queue, this will wait for an item to be inserted.

                # Do something with track here...
        """
        while True:
            yield await self.get_wait()

    def get(self) -> Playable | spotify.SpotifyTrack:
        return self._get()

    def _get(self) -> Playable | spotify.SpotifyTrack:
        if self.loop and self._loaded:
            return self._loaded

        if self.loop_all and self.is_empty:
            self._queue.extend(self.history._queue)
            self.history.clear()

        item = super()._get()

        self._loaded = item
        return item

    async def _put(self, item: Playable | spotify.SpotifyTrack) -> None:
        self._check_playable(item)

        if isinstance(item, (YouTubePlaylist, SoundCloudPlaylist)):
            for track in item.tracks:
                super()._put(track)
                await asyncio.sleep(0)
        else:
            super()._put(item)
            await asyncio.sleep(0)

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

        Put an item into the queue asynchronously using ``await``.

        If the provided ``item`` is a :class:`~wavelink.YouTubePlaylist` or :class:`~wavelink.SoundCloudPlaylist`, all
        tracks from this playlist will be put into the queue.


        .. note::

            Inserting playlists is currently only supported via this method, which means you can only insert them into
            the back of the queue. Future versions of wavelink may add support for inserting playlists from a specific
            index, or at the front of the queue.


        .. versionchanged:: 2.6.0

            Added support for directly adding a :class:`~wavelink.YouTubePlaylist` to the queue.
        """
        await self._put(item)

    def put(self, item: Playable | spotify.SpotifyTrack) -> None:
        """Put the given item into the back of the queue.

        If the provided ``item`` is a :class:`~wavelink.YouTubePlaylist`, all tracks from this playlist will be put
        into the queue.


        .. note::

            Inserting playlists is currently only supported via this method, which means you can only insert them into
            the back of the queue. Future versions of wavelink may add support for inserting playlists from a specific
            index, or at the front of the queue.


        .. versionchanged:: 2.6.0

            Added support for directly adding a :class:`~wavelink.YouTubePlaylist` to the queue.
        """
        self._check_playable(item)

        if isinstance(item, YouTubePlaylist):
            for track in item.tracks:
                super()._put(track)
        else:
            super()._put(item)

        self._wakeup_next()

    def reset(self) -> None:
        """Clears the state of all queues, including the history queue.

        - sets loop and loop_all to ``False``.
        - removes all items from the queue and history queue.
        - cancels any waiting queues.
        """
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


        .. versionadded:: 2.0
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


        .. versionadded:: 2.0
        """
        return self._loop_all

    @loop_all.setter
    def loop_all(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise ValueError('The "loop_all" property can only be set with a bool.')

        self._loop_all = value
