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

from typing import TYPE_CHECKING, Any, TypeAlias, overload

import yarl

import wavelink

from .enums import TrackSource
from .utils import ExtrasNamespace


if TYPE_CHECKING:
    from collections.abc import Iterator

    from .node import Node
    from .types.tracks import (
        PlaylistInfoPayload,
        PlaylistPayload,
        TrackInfoPayload,
        TrackPayload,
    )


__all__ = ("Search", "Album", "Artist", "Playable", "Playlist", "PlaylistInfo")


_source_mapping: dict[TrackSource | str | None, str] = {
    TrackSource.YouTube: "ytsearch",
    TrackSource.SoundCloud: "scsearch",
    TrackSource.YouTubeMusic: "ytmsearch",
}


Search: TypeAlias = "list[Playable] | Playlist"


class Album:
    """Container class representing Album data received via Lavalink.

    Attributes
    ----------
    name: str | None
        The album name. Could be ``None``.
    url: str | None
        The album url. Could be ``None``.
    """

    def __init__(self, *, data: dict[Any, Any]) -> None:
        self.name: str | None = data.get("albumName")
        self.url: str | None = data.get("albumUrl")


class Artist:
    """Container class representing Artist data received via Lavalink.

    Attributes
    ----------
    url: str | None
        The artist url. Could be ``None``.
    artwork: str | None
        The artist artwork url. Could be ``None``.
    """

    def __init__(self, *, data: dict[Any, Any]) -> None:
        self.url: str | None = data.get("artistUrl")
        self.artwork: str | None = data.get("artistArtworkUrl")


class Playable:
    """The Wavelink Playable object which represents all tracks in Wavelink 3.

    .. note::

        You should not construct this class manually.

    .. container:: operations

        .. describe:: str(track)

            The title of this playable.

        .. describe:: repr(track)

            The official string representation of this playable.

        .. describe:: track == other

            Whether this track is equal to another. Checks both the track encoding and identifier.
    """

    def __init__(self, data: TrackPayload, *, playlist: PlaylistInfo | None = None) -> None:
        info: TrackInfoPayload = data["info"]

        self._encoded: str = data["encoded"]
        self._identifier: str = info["identifier"]
        self._is_seekable: bool = info["isSeekable"]
        self._author: str = info["author"]
        self._length: int = info["length"]
        self._is_stream: bool = info["isStream"]
        self._position: int = info["position"]
        self._title: str = info["title"]
        self._uri: str | None = info.get("uri")
        self._artwork: str | None = info.get("artworkUrl")
        self._isrc: str | None = info.get("isrc")
        self._source: str = info["sourceName"]

        plugin: dict[Any, Any] = data["pluginInfo"]
        self._album: Album = Album(data=plugin)
        self._artist: Artist = Artist(data=plugin)

        self._preview_url: str | None = plugin.get("previewUrl")
        self._is_preview: bool | None = plugin.get("isPreview")

        self._playlist = playlist
        self._recommended: bool = False

        self._extras: ExtrasNamespace = ExtrasNamespace(data.get("userData", {}))

        self._raw_data = data

    def __hash__(self) -> int:
        return hash(self.encoded)

    def __str__(self) -> str:
        return self.title

    def __repr__(self) -> str:
        return f"Playable(source={self.source}, title={self.title}, identifier={self.identifier})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Playable):
            return NotImplemented

        return self.encoded == other.encoded or self.identifier == other.identifier

    @property
    def encoded(self) -> str:
        """Property returning the encoded track string from Lavalink."""
        return self._encoded

    @property
    def identifier(self) -> str:
        """Property returning the identifier of this track from its source.

        E.g. YouTube ID or Spotify ID.
        """
        return self._identifier

    @property
    def is_seekable(self) -> bool:
        """Property returning a bool whether this track can be used in seeking."""
        return self._is_seekable

    @property
    def author(self) -> str:
        """Property returning the name of the author of this track."""
        return self._author

    @property
    def length(self) -> int:
        """Property returning the tracks duration in milliseconds as an int."""
        return self._length

    @property
    def is_stream(self) -> bool:
        """Property returning a bool indicating whether this track is a stream."""
        return self._is_stream

    @property
    def position(self) -> int:
        """Property returning starting position of this track in milliseconds as an int."""
        return self._position

    @property
    def title(self) -> str:
        """Property returning the title/name of this track."""
        return self._title

    @property
    def uri(self) -> str | None:
        """Property returning the URL to this track. Could be ``None``."""
        return self._uri

    @property
    def artwork(self) -> str | None:
        """Property returning the URL of the artwork of this track. Could be ``None``."""
        return self._artwork

    @property
    def isrc(self) -> str | None:
        """Property returning the ISRC (International Standard Recording Code) of this track. Could be ``None``."""
        return self._isrc

    @property
    def source(self) -> str:
        """Property returning the source of this track as a ``str``.

        E.g. "spotify" or "youtube".
        """
        return self._source

    @property
    def album(self) -> Album:
        """Property returning album data for this track."""
        return self._album

    @property
    def artist(self) -> Artist:
        """Property returning artist data for this track."""
        return self._artist

    @property
    def preview_url(self) -> str | None:
        """Property returning the preview URL for this track. Could be ``None``."""
        return self._preview_url

    @property
    def is_preview(self) -> bool | None:
        """Property returning a bool indicating if this track is a preview. Could be ``None`` if unknown."""
        return self._is_preview

    @property
    def playlist(self) -> PlaylistInfo | None:
        """Property returning a :class:`wavelink.PlaylistInfo`. Could be ``None``
        if this track is not a part of a playlist.
        """
        return self._playlist

    @property
    def recommended(self) -> bool:
        """Property returning a bool indicating whether this track was recommended via AutoPlay."""
        return self._recommended

    @property
    def extras(self) -> ExtrasNamespace:
        """Property returning a :class:`~wavelink.ExtrasNamespace` of extras for this :class:`Playable`.

        You can set this property with a :class:`dict` of valid :class:`str` keys to any valid ``JSON`` value,
        or a :class:`~wavelink.ExtrasNamespace`.

        If a dict is passed, it will be converted into an :class:`~wavelink.ExtrasNamespace`,
        which can be converted back to a dict with dict(...). Additionally, you can also use list or tuple on
        :class:`~wavelink.ExtrasNamespace`.

        The extras dict will be sent to Lavalink as the ``userData`` field.


        .. warning::

            This is only available when using Lavalink 4+ (**Non BETA**) versions.


        Examples
        --------

            .. code:: python

                track: wavelink.Playable = wavelink.Playable.search("QUERY")
                track.extras = {"requester_id": 1234567890}

                # later...
                print(track.extras.requester_id)
                # or
                print(dict(track.extras)["requester_id"])


        .. versionadded:: 3.1.0
        """
        return self._extras

    @extras.setter
    def extras(self, __value: ExtrasNamespace | dict[str, Any]) -> None:
        if isinstance(__value, ExtrasNamespace):
            self._extras = __value
        else:
            self._extras = ExtrasNamespace(__value)

    @property
    def raw_data(self) -> TrackPayload:
        """The raw data for this ``Playable`` received via ``Lavalink``.

        You can use this data to reconstruct this ``Playable`` object.


        Examples
        --------

            .. code:: python3

                # For example purposes...
                old_data = track.raw_data

                # Later...
                track: wavelink.Playable = wavelink.Playable(old_data)


        .. versionadded:: 3.2.0
        """
        return self._raw_data

    @classmethod
    async def search(
        cls, query: str, /, *, source: TrackSource | str | None = TrackSource.YouTubeMusic, node: Node | None = None
    ) -> Search:
        """Search for a list of :class:`~wavelink.Playable` or a :class:`~wavelink.Playlist`, with the given query.

        .. note::

            This method differs from :meth:`wavelink.Pool.fetch_tracks` in that it will apply a relevant search prefix
            for you when a URL is **not** provided. This prefix can be controlled via the ``source`` keyword argument.


        .. note::

            This method of searching is preferred over, :meth:`wavelink.Pool.fetch_tracks`.


        Parameters
        ----------
        query: str
            The query to search tracks for. If this is **not** a URL based search this method will provide an
            appropriate search prefix based on what is provided to the ``source`` keyword only parameter,
            or it's default.

            If this query **is a URL**, a search prefix will **not** be used.
        source: :class:`TrackSource` | str | None
            This parameter determines which search prefix to use when searching for tracks.
            If ``None`` is provided, no prefix will be used, however this behaviour is default regardless of what
            is provided **when a URL is found**.

            For basic searches, E.g. YouTube, YouTubeMusic and SoundCloud, see: :class:`wavelink.TrackSource`.
            Otherwise, a ``str`` may be provided for plugin based searches, E.g. "spsearch:" for the
            LavaSrc Spotify based search.

            Defaults to :attr:`wavelink.TrackSource.YouTubeMusic` which is equivalent to "ytmsearch:".
        node: :class:`~wavelink.Node` | None
            An optional :class:`~wavelink.Node` to use when searching for tracks. Defaults to ``None``, which uses
            the :class:`~wavelink.Pool`'s automatic node selection.


        Returns
        -------
        :class:`wavelink.Search`
            A union of either list[:class:`Playable`] or :class:`Playlist`. Could return and empty list,
            if no tracks or playlist were found.

        Raises
        ------
        LavalinkLoadException
            Exception raised when Lavalink fails to load results based on your query.


        Examples
        --------

        .. code:: python3

            # Search for tracks, with the default "ytsearch:" prefix.
            tracks: wavelink.Search = await wavelink.Playable.search("Ocean Drive")
            if not tracks:
                # No tracks were found...
                ...

            # Search for tracks, with a URL.
            tracks: wavelink.Search = await wavelink.Playable.search("https://www.youtube.com/watch?v=KDxJlW6cxRk")
            ...

            # Search for tracks, using Spotify and the LavaSrc Plugin.
            tracks: wavelink.Search = await wavelink.Playable.search("4b93D55xv3YCH5mT4p6HPn", source="spsearch")
            ...

            # Search for tracks, using Spotify and the LavaSrc Plugin, with a URL.
            tracks: wavelink.Search = await wavelink.Playable.search("https://open.spotify.com/track/4b93D55xv3YCH5mT4p6HPn")
            ...

            # Search for a playlist, using Spotify and the LavaSrc Plugin.
            # or alternatively any other playlist URL from another source like YouTube.
            tracks: wavelink.Search = await wavelink.Playable.search("https://open.spotify.com/playlist/37i9dQZF1DWXRqgorJj26U")
            ...


        .. versionchanged:: 3.0.0

            This method has been changed significantly in version ``3.0.0``. This method has been simplified to provide
            an easier interface for searching tracks. See the above documentation and examples.

            You can no longer provide a :class:`wavelink.Node` to use for searching as this method will now select the
            most appropriate node from the :class:`wavelink.Pool`.
        """
        prefix: TrackSource | str | None = _source_mapping.get(source, source)
        check = yarl.URL(query)

        if check.host:
            tracks: Search = await wavelink.Pool.fetch_tracks(query, node=node)
            return tracks

        if not prefix:
            term: str = query
        else:
            assert not isinstance(prefix, TrackSource)
            term: str = f"{prefix.removesuffix(':')}:{query}"

        tracks: Search = await wavelink.Pool.fetch_tracks(term, node=node)
        return tracks


class Playlist:
    """The wavelink Playlist container class.

    This class is created and returned via both :meth:`Playable.search` and :meth:`wavelink.Pool.fetch_tracks`.

    It contains various information about the playlist and a list of :class:`Playable` that can be used directly in
    :meth:`wavelink.Player.play`. See below for various supported operations.


    .. warning::

        You should not instantiate this class manually,
        use :meth:`Playable.search` or :meth:`wavelink.Pool.fetch_tracks` instead.


    .. warning::

        You can not use ``.search`` directly on this class, see: :meth:`Playable.search`.


    .. note::

        This class can be directly added to :class:`wavelink.Queue` identical to :class:`Playable`. When added,
        all tracks contained in this playlist, will be individually added to the :class:`wavelink.Queue`.


    .. container:: operations

        .. describe:: str(x)

            Return the name associated with this playlist.

        .. describe:: repr(x)

            Return the official string representation of this playlist.

        .. describe:: x == y

            Compare the equality of playlist.

        .. describe:: len(x)

            Return an integer representing the amount of tracks contained in this playlist.

        .. describe:: x[0]

            Return a track contained in this playlist with the given index.

        .. describe:: x[0:2]

            Return a slice of tracks contained in this playlist.

        .. describe:: for x in y

            Iterate over the tracks contained in this playlist.

        .. describe:: reversed(x)

            Reverse the tracks contained in this playlist.

        .. describe:: x in y

            Check if a :class:`Playable` is contained in this playlist.


    Attributes
    ----------
    name: str
        The name of this playlist.
    selected: int
        The index of the selected track from Lavalink.
    tracks: list[:class:`Playable`]
        A list of :class:`Playable` contained in this playlist.
    type: str | None
        An optional ``str`` identifying the type of playlist this is. Only available when a plugin is used.
    url: str | None
        An optional ``str`` to the URL of this playlist. Only available when a plugin is used.
    artwork: str | None
        An optional ``str`` to the artwork of this playlist. Only available when a plugin is used.
    author: str | None
        An optional ``str`` of the author of this playlist. Only available when a plugin is used.
    """

    def __init__(self, data: PlaylistPayload) -> None:
        info: PlaylistInfoPayload = data["info"]
        self.name: str = info["name"]
        self.selected: int = info["selectedTrack"]

        playlist_info: PlaylistInfo = PlaylistInfo(data)
        self.tracks: list[Playable] = [Playable(data=track, playlist=playlist_info) for track in data["tracks"]]

        plugin: dict[Any, Any] = data["pluginInfo"]
        self.type: str | None = plugin.get("type")
        self.url: str | None = plugin.get("url")
        self.artwork: str | None = plugin.get("artworkUrl")
        self.author: str | None = plugin.get("author")

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Playlist(name={self.name}, tracks={len(self.tracks)})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Playlist):
            return NotImplemented

        return self.name == other.name and self.tracks == other.tracks

    def __len__(self) -> int:
        return len(self.tracks)

    @overload
    def __getitem__(self, index: int) -> Playable: ...

    @overload
    def __getitem__(self, index: slice) -> list[Playable]: ...

    def __getitem__(self, index: int | slice) -> Playable | list[Playable]:
        return self.tracks[index]

    def __iter__(self) -> Iterator[Playable]:
        return self.tracks.__iter__()

    def __reversed__(self) -> Iterator[Playable]:
        return self.tracks.__reversed__()

    def __contains__(self, item: Playable) -> bool:
        return item in self.tracks

    def pop(self, index: int = -1) -> Playable:
        return self.tracks.pop(index)

    def track_extras(self, **attrs: object) -> None:
        """Method which sets attributes to all :class:`Playable` in this playlist, with the provided keyword arguments.

        This is useful when you need to attach state to your :class:`Playable`, E.g. create a requester attribute.

        .. warning::

            If you try to override any existing property of :class:`Playable` this method will fail.


        Parameters
        ----------
        **attrs
            The keyword arguments to set as attribute name=value on each :class:`Playable`.

        Examples
        --------

            .. code:: python3

                playlist.track_extras(requester=ctx.author)

                track: wavelink.Playable = playlist[0]
                print(track.requester)
        """
        for track in self.tracks:
            for name, value in attrs.items():
                setattr(track, name, value)

    @property
    def extras(self) -> ExtrasNamespace:
        """Property returning a :class:`~wavelink.ExtrasNamespace` of extras for this :class:`Playlist`.

        You can set this property with a :class:`dict` of valid :class:`str` keys to any valid ``JSON`` value,
        or a :class:`~wavelink.ExtrasNamespace`.

        If a dict is passed, it will be converted into an :class:`~wavelink.ExtrasNamespace`,
        which can be converted back to a dict with ``dict(...)``. Additionally, you can also use list or tuple on
        :class:`~wavelink.ExtrasNamespace`.

        The extras dict will be sent to Lavalink as the ``userData`` field for each track in the playlist.


        .. warning::

            This is only available when using Lavalink 4+ (**Non BETA**) versions.


        Examples
        --------

            .. code:: python

                playlist: wavelink.Search = wavelink.Playable.search("QUERY")
                playlist.extras = {"requester_id": 1234567890}

                # later...
                print(track.extras.requester_id)
                # or
                print(dict(track.extras)["requester_id"])


        .. versionadded:: 3.2.0
        """
        return self._extras

    @extras.setter
    def extras(self, __value: ExtrasNamespace | dict[str, Any]) -> None:
        if isinstance(__value, ExtrasNamespace):
            self._extras = __value
        else:
            self._extras = ExtrasNamespace(__value)

        for track in self.tracks:
            track.extras = __value


class PlaylistInfo:
    """The wavelink PlaylistInfo container class.

    It contains various information about the playlist but **does not** contain the tracks associated with this
    playlist.

    This class is used to provided information about the original :class:`wavelink.Playlist` on tracks.

    Attributes
    ----------
    name: str
        The name of this playlist.
    selected: int
        The index of the selected track from Lavalink.
    tracks: int
        The amount of tracks this playlist originally contained.
    type: str | None
        An optional ``str`` identifying the type of playlist this is. Only available when a plugin is used.
    url: str | None
        An optional ``str`` to the URL of this playlist. Only available when a plugin is used.
    artwork: str | None
        An optional ``str`` to the artwork of this playlist. Only available when a plugin is used.
    author: str | None
        An optional ``str`` of the author of this playlist. Only available when a plugin is used.
    """

    __slots__ = ("name", "selected", "tracks", "type", "url", "artwork", "author")

    def __init__(self, data: PlaylistPayload) -> None:
        info: PlaylistInfoPayload = data["info"]
        self.name: str = info["name"]
        self.selected: int = info["selectedTrack"]

        self.tracks: int = len(data["tracks"])

        plugin: dict[Any, Any] = data["pluginInfo"]
        self.type: str | None = plugin.get("type")
        self.url: str | None = plugin.get("url")
        self.artwork: str | None = plugin.get("artworkUrl")
        self.author: str | None = plugin.get("author")

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"PlaylistInfo(name={self.name}, tracks={self.tracks})"

    def __len__(self) -> int:
        return self.tracks
