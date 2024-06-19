"""
The MIT License (MIT)

Copyright (c) 2021-Present PythonistaGuild, EvieePy

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict


if TYPE_CHECKING:
    from typing_extensions import Self, Unpack

    from .types.filters import (
        ChannelMix as ChannelMixPayload,
        Distortion as DistortionPayload,
        Equalizer as EqualizerPayload,
        FilterPayload,
        Karaoke as KaraokePayload,
        LowPass as LowPassPayload,
        Rotation as RotationPayload,
        Timescale as TimescalePayload,
        Tremolo as TremoloPayload,
        Vibrato as VibratoPayload,
    )


__all__ = (
    "FiltersOptions",
    "Filters",
    "Equalizer",
    "Karaoke",
    "Timescale",
    "Tremolo",
    "Vibrato",
    "Rotation",
    "Distortion",
    "ChannelMix",
    "LowPass",
    "PluginFilters",
)


class FiltersOptions(TypedDict, total=False):
    volume: float
    equalizer: Equalizer
    karaoke: Karaoke
    timescale: Timescale
    tremolo: Tremolo
    vibrato: Vibrato
    rotation: Rotation
    distortion: Distortion
    channel_mix: ChannelMix
    low_pass: LowPass
    plugin_filters: PluginFilters
    reset: bool


class EqualizerOptions(TypedDict):
    bands: list[EqualizerPayload] | None


class KaraokeOptions(TypedDict):
    level: float | None
    mono_level: float | None
    filter_band: float | None
    filter_width: float | None


class RotationOptions(TypedDict):
    rotation_hz: float | None


class DistortionOptions(TypedDict):
    sin_offset: float | None
    sin_scale: float | None
    cos_offset: float | None
    cos_scale: float | None
    tan_offset: float | None
    tan_scale: float | None
    offset: float | None
    scale: float | None


class ChannelMixOptions(TypedDict):
    left_to_left: float | None
    left_to_right: float | None
    right_to_left: float | None
    right_to_right: float | None


class Equalizer:
    """Equalizer Filter Class.

    There are 15 bands ``0`` to ``14`` that can be changed.
    Each band has a ``gain`` which is the multiplier for the given band. ``gain`` defaults to ``0``.

    Valid ``gain`` values range from ``-0.25`` to ``1.0``, where ``-0.25`` means the given band is completely muted,
    and ``0.25`` means it will be doubled.

    Modifying the ``gain`` could also change the volume of the output.
    """

    def __init__(self, payload: list[EqualizerPayload] | None = None) -> None:
        if payload and len(payload) == 15:
            self._payload = self._set(payload)

        else:
            payload_: dict[int, EqualizerPayload] = {n: {"band": n, "gain": 0.0} for n in range(15)}
            self._payload = payload_

    def _set(self, payload: list[EqualizerPayload]) -> dict[int, EqualizerPayload]:
        default: dict[int, EqualizerPayload] = {n: {"band": n, "gain": 0.0} for n in range(15)}

        for eq in payload:
            band: int = eq["band"]
            if band > 14 or band < 0:
                continue

            default[band] = eq

        return default

    def set(self, **options: Unpack[EqualizerOptions]) -> Self:
        """Set the bands of the Equalizer class.

        Accepts a keyword argument ``bands`` which is a ``list`` of ``dict`` containing the keys ``band`` and ``gain``.

        ``band`` can be an ``int`` beteween ``0`` and ``14``.
        ``gain`` can be a float between ``-0.25`` and ``1.0``, where ``-0.25`` means the given band is completely muted,
        and ``0.25`` means it will be doubled.

        Using this method changes **all** bands, resetting any bands not provided.
        To change specific bands, consider accessing :attr:`~wavelink.Equalizer.payload` first.
        """
        default: dict[int, EqualizerPayload] = {n: {"band": n, "gain": 0.0} for n in range(15)}
        payload: list[EqualizerPayload] | None = options.get("bands", None)

        if payload is None:
            self._payload = default
            return self

        self._payload = self._set(payload)
        return self

    def reset(self) -> Self:
        """Reset this filter to its defaults."""
        self._payload: dict[int, EqualizerPayload] = {n: {"band": n, "gain": 0.0} for n in range(15)}
        return self

    @property
    def payload(self) -> dict[int, EqualizerPayload]:
        """The raw payload associated with this filter.

        This property returns a copy.
        """
        return self._payload.copy()

    def __str__(self) -> str:
        return "Equalizer"

    def __repr__(self) -> str:
        return f"<Equalizer: {self._payload}>"


class Karaoke:
    """Karaoke Filter class.

    Uses equalization to eliminate part of a band, usually targeting vocals.
    """

    def __init__(self, payload: KaraokePayload) -> None:
        self._payload = payload

    def set(self, **options: Unpack[KaraokeOptions]) -> Self:
        """Set the properties of the this filter.

        This method accepts keyword argument pairs.
        This method does not override existing settings if they are not provided.

        Parameters
        ----------
        level: Optional[float]
            The level ``0`` to ``1.0`` where ``0.0`` is no effect and ``1.0`` is full effect.
        mono_level: Optional[float]
            The mono level ``0`` to ``1.0`` where ``0.0`` is no effect and ``1.0`` is full effect.
        filter_band: Optional[float]
            The filter band in Hz.
        filter_width: Optional[float]
            The filter width.
        """
        self._payload: KaraokePayload = {
            "level": options.get("level", self._payload.get("level")),
            "monoLevel": options.get("mono_level", self._payload.get("monoLevel")),
            "filterBand": options.get("filter_band", self._payload.get("filterBand")),
            "filterWidth": options.get("filter_width", self._payload.get("filterWidth")),
        }
        return self

    def reset(self) -> Self:
        """Reset this filter to its defaults."""
        self._payload: KaraokePayload = {}
        return self

    @property
    def payload(self) -> KaraokePayload:
        """The raw payload associated with this filter.

        This property returns a copy.
        """
        return self._payload.copy()

    def __str__(self) -> str:
        return "Karaoke"

    def __repr__(self) -> str:
        return f"<Karaoke: {self._payload}>"


class Timescale:
    """Timescale Filter class.

    Changes the speed, pitch, and rate.
    """

    def __init__(self, payload: TimescalePayload) -> None:
        self._payload = payload

    def set(self, **options: Unpack[TimescalePayload]) -> Self:
        """Set the properties of the this filter.

        This method accepts keyword argument pairs.
        This method does not override existing settings if they are not provided.

        Parameters
        ----------
        speed: Optional[float]
            The playback speed.
        pitch: Optional[float]
            The pitch.
        rate: Optional[float]
            The rate.
        """
        self._payload.update(options)
        return self

    def reset(self) -> Self:
        """Reset this filter to its defaults."""
        self._payload: TimescalePayload = {}
        return self

    @property
    def payload(self) -> TimescalePayload:
        """The raw payload associated with this filter.

        This property returns a copy.
        """
        return self._payload.copy()

    def __str__(self) -> str:
        return "Timescale"

    def __repr__(self) -> str:
        return f"<Timescale: {self._payload}>"


class Tremolo:
    """The Tremolo Filter class.

    Uses amplification to create a shuddering effect, where the volume quickly oscillates.
    Demo: https://en.wikipedia.org/wiki/File:Fuse_Electronics_Tremolo_MK-III_Quick_Demo.ogv
    """

    def __init__(self, payload: TremoloPayload) -> None:
        self._payload = payload

    def set(self, **options: Unpack[TremoloPayload]) -> Self:
        """Set the properties of the this filter.

        This method accepts keyword argument pairs.
        This method does not override existing settings if they are not provided.

        Parameters
        ----------
        frequency: Optional[float]
            The frequency.
        depth: Optional[float]
            The tremolo depth.
        """
        self._payload.update(options)
        return self

    def reset(self) -> Self:
        """Reset this filter to its defaults."""
        self._payload: TremoloPayload = {}
        return self

    @property
    def payload(self) -> TremoloPayload:
        """The raw payload associated with this filter.

        This property returns a copy.
        """
        return self._payload.copy()

    def __str__(self) -> str:
        return "Tremolo"

    def __repr__(self) -> str:
        return f"<Tremolo: {self._payload}>"


class Vibrato:
    """The Vibrato Filter class.

    Similar to tremolo. While tremolo oscillates the volume, vibrato oscillates the pitch.
    """

    def __init__(self, payload: VibratoPayload) -> None:
        self._payload = payload

    def set(self, **options: Unpack[VibratoPayload]) -> Self:
        """Set the properties of the this filter.

        This method accepts keyword argument pairs.
        This method does not override existing settings if they are not provided.

        Parameters
        ----------
        frequency: Optional[float]
            The frequency.
        depth: Optional[float]
            The vibrato depth.
        """
        self._payload.update(options)
        return self

    def reset(self) -> Self:
        """Reset this filter to its defaults."""
        self._payload: VibratoPayload = {}
        return self

    @property
    def payload(self) -> VibratoPayload:
        """The raw payload associated with this filter.

        This property returns a copy.
        """
        return self._payload.copy()

    def __str__(self) -> str:
        return "Vibrato"

    def __repr__(self) -> str:
        return f"<Vibrato: {self._payload}>"


class Rotation:
    """The Rotation Filter class.

    Rotates the sound around the stereo channels/user headphones (aka Audio Panning).
    It can produce an effect similar to https://youtu.be/QB9EB8mTKcc (without the reverb).
    """

    def __init__(self, payload: RotationPayload) -> None:
        self._payload = payload

    def set(self, **options: Unpack[RotationOptions]) -> Self:
        """Set the properties of the this filter.

        This method accepts keyword argument pairs.
        This method does not override existing settings if they are not provided.

        Parameters
        ----------
        rotation_hz: Optional[float]
            The frequency of the audio rotating around the listener in Hz. ``0.2`` is similar to the example video.
        """
        self._payload: RotationPayload = {"rotationHz": options.get("rotation_hz", self._payload.get("rotationHz"))}
        return self

    def reset(self) -> Self:
        """Reset this filter to its defaults."""
        self._payload: RotationPayload = {}
        return self

    @property
    def payload(self) -> RotationPayload:
        """The raw payload associated with this filter.

        This property returns a copy.
        """
        return self._payload.copy()

    def __str__(self) -> str:
        return "Rotation"

    def __repr__(self) -> str:
        return f"<Rotation: {self._payload}>"


class Distortion:
    """The Distortion Filter class.

    According to Lavalink "It can generate some pretty unique audio effects."
    """

    def __init__(self, payload: DistortionPayload) -> None:
        self._payload = payload

    def set(self, **options: Unpack[DistortionOptions]) -> Self:
        """Set the properties of the this filter.

        This method accepts keyword argument pairs.
        This method does not override existing settings if they are not provided.

        Parameters
        ----------
        sin_offset: Optional[float]
            The sin offset.
        sin_scale: Optional[float]
            The sin scale.
        cos_offset: Optional[float]
            The cos offset.
        cos_scale: Optional[float]
            The cos scale.
        tan_offset: Optional[float]
            The tan offset.
        tan_scale: Optional[float]
            The tan scale.
        offset: Optional[float]
            The offset.
        scale: Optional[float]
            The scale.
        """
        self._payload: DistortionPayload = {
            "sinOffset": options.get("sin_offset", self._payload.get("sinOffset")),
            "sinScale": options.get("sin_scale", self._payload.get("sinScale")),
            "cosOffset": options.get("cos_offset", self._payload.get("cosOffset")),
            "cosScale": options.get("cos_scale", self._payload.get("cosScale")),
            "tanOffset": options.get("tan_offset", self._payload.get("tanOffset")),
            "tanScale": options.get("tan_scale", self._payload.get("tanScale")),
            "offset": options.get("offset", self._payload.get("offset")),
            "scale": options.get("scale", self._payload.get("scale")),
        }
        return self

    def reset(self) -> Self:
        """Reset this filter to its defaults."""
        self._payload: DistortionPayload = {}
        return self

    @property
    def payload(self) -> DistortionPayload:
        """The raw payload associated with this filter.

        This property returns a copy.
        """
        return self._payload.copy()

    def __str__(self) -> str:
        return "Distortion"

    def __repr__(self) -> str:
        return f"<Distortion: {self._payload}>"


class ChannelMix:
    """The ChannelMix Filter class.

    Mixes both channels (left and right), with a configurable factor on how much each channel affects the other.
    With the defaults, both channels are kept independent of each other.

    Setting all factors to ``0.5`` means both channels get the same audio.
    """

    def __init__(self, payload: ChannelMixPayload) -> None:
        self._payload = payload

    def set(self, **options: Unpack[ChannelMixOptions]) -> Self:
        """Set the properties of the this filter.

        This method accepts keyword argument pairs.
        This method does not override existing settings if they are not provided.

        Parameters
        ----------
        left_to_left: Optional[float]
            The left to left channel mix factor. Between ``0.0`` and ``1.0``.
        left_to_right: Optional[float]
            The left to right channel mix factor. Between ``0.0`` and ``1.0``.
        right_to_left: Optional[float]
            The right to left channel mix factor. Between ``0.0`` and ``1.0``.
        right_to_right: Optional[float]
            The right to right channel mix factor. Between ``0.0`` and ``1.0``.
        """
        self._payload: ChannelMixPayload = {
            "leftToLeft": options.get("left_to_left", self._payload.get("leftToLeft")),
            "leftToRight": options.get("left_to_right", self._payload.get("leftToRight")),
            "rightToLeft": options.get("right_to_left", self._payload.get("rightToLeft")),
            "rightToRight": options.get("right_to_right", self._payload.get("rightToRight")),
        }
        return self

    def reset(self) -> Self:
        """Reset this filter to its defaults."""
        self._payload: ChannelMixPayload = {}
        return self

    @property
    def payload(self) -> ChannelMixPayload:
        """The raw payload associated with this filter.

        This property returns a copy.
        """
        return self._payload.copy()

    def __str__(self) -> str:
        return "ChannelMix"

    def __repr__(self) -> str:
        return f"<ChannelMix: {self._payload}>"


class LowPass:
    """The LowPass Filter class.

    Higher frequencies get suppressed, while lower frequencies pass through this filter, thus the name low pass.
    Any smoothing values equal to or less than ``1.0`` will disable the filter.
    """

    def __init__(self, payload: LowPassPayload) -> None:
        self._payload = payload

    def set(self, **options: Unpack[LowPassPayload]) -> Self:
        """Set the properties of the this filter.

        This method accepts keyword argument pairs.
        This method does not override existing settings if they are not provided.

        Parameters
        ----------
        smoothing: Optional[float]
            The smoothing factor.
        """
        self._payload.update(options)
        return self

    def reset(self) -> Self:
        """Reset this filter to its defaults."""
        self._payload: LowPassPayload = {}
        return self

    @property
    def payload(self) -> LowPassPayload:
        """The raw payload associated with this filter.

        This property returns a copy.
        """
        return self._payload.copy()

    def __str__(self) -> str:
        return "LowPass"

    def __repr__(self) -> str:
        return f"<LowPass: {self._payload}>"


class PluginFilters:
    """The PluginFilters class.

    This class handles setting filters on plugins that support setting filter values.
    See the documentation of the Lavalink Plugin for more information on the values that can be set.

    This class takes in a ``dict[str, Any]`` usually in the form of:

    .. code:: python3

        {"pluginName": {"filterKey": "filterValue"}, ...}


    .. warning::

        Do NOT include the ``"pluginFilters"`` top level key when setting your values for this class.
    """

    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def set(self, **options: dict[str, Any]) -> Self:
        """Set the properties of this filter.

        This method accepts keyword argument pairs OR you can alternatively unpack a dictionary.
        See the documentation of the Lavalink Plugin for more information on the values that can be set.

        Examples
        --------

        .. code:: python3

            plugin_filters: PluginFilters = PluginFilters()
            plugin_filters.set(pluginName={"filterKey": "filterValue", ...})

            # OR...

            plugin_filters.set(**{"pluginName": {"filterKey": "filterValue", ...}})
        """
        self._payload.update(options)
        return self

    def reset(self) -> Self:
        """Reset this filter to its defaults."""
        self._payload: dict[str, Any] = {}
        return self

    @property
    def payload(self) -> dict[str, Any]:
        """The raw payload associated with this filter.

        This property returns a copy.
        """
        return self._payload.copy()

    def __str__(self) -> str:
        return "PluginFilters"

    def __repr__(self) -> str:
        return f"<PluginFilters: {self._payload}"


class Filters:
    """The wavelink Filters class.

    This class contains the information associated with each of Lavalinks filter objects, as Python classes.
    Each filter can be ``set`` or ``reset`` individually.

    Using ``set`` on an individual filter only updates any ``new`` values you pass.
    Using ``reset`` on an individual filter, resets it's payload, and can be used before ``set`` when you want a clean
    state for that filter.

    See: :meth:`~wavelink.Filters.reset` to reset **every** individual filter.

    This class is already applied an instantiated on all new :class:`~wavelink.Player`.

    See: :meth:`~wavelink.Player.set_filters` for information on applying this class to your :class:`~wavelink.Player`.
    See: :attr:`~wavelink.Player.filters` for retrieving the applied filters.

    To retrieve the ``payload`` for this Filters class, you can call an instance of this class.

    Examples
    --------

    .. code:: python3

        import wavelink

        # Create a brand new Filters and apply it...
        # You can use player.set_filters() for an easier way to reset.
        filters: wavelink.Filters = wavelink.Filters()
        await player.set_filters(filters)


        # Retrieve the payload of any Filters instance...
        filters: wavelink.Filters = player.filters
        print(filters())


        # Set some filters...
        # You can set and reset individual filters at the same time...
        filters: wavelink.Filters = player.filters
        filters.timescale.set(pitch=1.2, speed=1.1, rate=1)
        filters.rotation.set(rotation_hz=0.2)
        filters.equalizer.reset()

        await player.set_filters(filters)


        # Reset a filter...
        filters: wavelink.Filters = player.filters
        filters.timescale.reset()

        await player.set_filters(filters)


        # Reset all filters...
        filters: wavelink.Filters = player.filters
        filters.reset()

        await player.set_filters(filters)


        # Reset and apply filters easier method...
        await player.set_filters()
    """

    def __init__(self, *, data: FilterPayload | None = None) -> None:
        self._volume: float | None = None
        self._equalizer: Equalizer = Equalizer(None)
        self._karaoke: Karaoke = Karaoke({})
        self._timescale: Timescale = Timescale({})
        self._tremolo: Tremolo = Tremolo({})
        self._vibrato: Vibrato = Vibrato({})
        self._rotation: Rotation = Rotation({})
        self._distortion: Distortion = Distortion({})
        self._channel_mix: ChannelMix = ChannelMix({})
        self._low_pass: LowPass = LowPass({})
        self._plugin_filters: PluginFilters = PluginFilters({})

        if data:
            self._create_from(data)

    def _create_from(self, data: FilterPayload) -> None:
        self._volume = data.get("volume")
        self._equalizer = Equalizer(data.get("equalizer", None))
        self._karaoke = Karaoke(data.get("karaoke", {}))
        self._timescale = Timescale(data.get("timescale", {}))
        self._tremolo = Tremolo(data.get("tremolo", {}))
        self._vibrato = Vibrato(data.get("vibrato", {}))
        self._rotation = Rotation(data.get("rotation", {}))
        self._distortion = Distortion(data.get("distortion", {}))
        self._channel_mix = ChannelMix(data.get("channelMix", {}))
        self._low_pass = LowPass(data.get("lowPass", {}))
        self._plugin_filters = PluginFilters(data.get("pluginFilters", {}))

    def _set_with_reset(self, filters: FiltersOptions) -> None:
        self._volume = filters.get("volume")
        self._equalizer = filters.get("equalizer", Equalizer(None))
        self._karaoke = filters.get("karaoke", Karaoke({}))
        self._timescale = filters.get("timescale", Timescale({}))
        self._tremolo = filters.get("tremolo", Tremolo({}))
        self._vibrato = filters.get("vibrato", Vibrato({}))
        self._rotation = filters.get("rotation", Rotation({}))
        self._distortion = filters.get("distortion", Distortion({}))
        self._channel_mix = filters.get("channel_mix", ChannelMix({}))
        self._low_pass = filters.get("low_pass", LowPass({}))
        self._plugin_filters = filters.get("plugin_filters", PluginFilters({}))

    def set_filters(self, **filters: Unpack[FiltersOptions]) -> None:
        """Set multiple filters at once to a standalone Filter object.
        To set the filters to the player directly see :meth:`wavelink.Player.set_filters`

        Parameters
        ----------
        volume: float
            The Volume filter to apply to the player.
        equalizer: :class:`wavelink.Equalizer`
            The Equalizer filter to apply to the player.
        karaoke: :class:`wavelink.Karaoke`
            The Karaoke filter to apply to the player.
        timescale: :class:`wavelink.Timescale`
            The Timescale filter to apply to the player.
        tremolo: :class:`wavelink.Tremolo`
            The Tremolo filter to apply to the player.
        vibrato: :class:`wavelink.Vibrato`
            The Vibrato filter to apply to the player.
        rotation: :class:`wavelink.Rotation`
            The Rotation filter to apply to the player.
        distortion: :class:`wavelink.Distortion`
            The Distortion filter to apply to the player.
        channel_mix: :class:`wavelink.ChannelMix`
            The ChannelMix filter to apply to the player.
        low_pass: :class:`wavelink.LowPass`
            The LowPass filter to apply to the player.
        plugin_filters: :class:`wavelink.PluginFilters`
            The extra Plugin Filters to apply to the player. See :class:`~wavelink.PluginFilters` for more details.
        reset: bool
            Whether to reset all filters that were not specified.
        """

        reset: bool = filters.get("reset", False)
        if reset:
            self._set_with_reset(filters)
            return

        self._volume = filters.get("volume", self._volume)
        self._equalizer = filters.get("equalizer", self._equalizer)
        self._karaoke = filters.get("karaoke", self._karaoke)
        self._timescale = filters.get("timescale", self._timescale)
        self._tremolo = filters.get("tremolo", self._tremolo)
        self._vibrato = filters.get("vibrato", self._vibrato)
        self._rotation = filters.get("rotation", self._rotation)
        self._distortion = filters.get("distortion", self._distortion)
        self._channel_mix = filters.get("channel_mix", self._channel_mix)
        self._low_pass = filters.get("low_pass", self._low_pass)
        self._plugin_filters = filters.get("plugin_filters", self._plugin_filters)

    def _reset(self) -> None:
        self._volume = None
        self._equalizer = Equalizer(None)
        self._karaoke = Karaoke({})
        self._timescale = Timescale({})
        self._tremolo = Tremolo({})
        self._vibrato = Vibrato({})
        self._rotation = Rotation({})
        self._distortion = Distortion({})
        self._channel_mix = ChannelMix({})
        self._low_pass = LowPass({})
        self._plugin_filters = PluginFilters({})

    def reset(self) -> None:
        """Method which resets this object to an original state.

        This method will clear all individual filters, and assign the wavelink default classes.
        """
        self._reset()

    @classmethod
    def from_filters(cls, **filters: Unpack[FiltersOptions]) -> Self:
        """Creates a Filters object with specified filters.

        Parameters
        ----------
        volume: float
            The Volume filter to apply to the player.
        equalizer: :class:`wavelink.Equalizer`
            The Equalizer filter to apply to the player.
        karaoke: :class:`wavelink.Karaoke`
            The Karaoke filter to apply to the player.
        timescale: :class:`wavelink.Timescale`
            The Timescale filter to apply to the player.
        tremolo: :class:`wavelink.Tremolo`
            The Tremolo filter to apply to the player.
        vibrato: :class:`wavelink.Vibrato`
            The Vibrato filter to apply to the player.
        rotation: :class:`wavelink.Rotation`
            The Rotation filter to apply to the player.
        distortion: :class:`wavelink.Distortion`
            The Distortion filter to apply to the player.
        channel_mix: :class:`wavelink.ChannelMix`
            The ChannelMix filter to apply to the player.
        low_pass: :class:`wavelink.LowPass`
            The LowPass filter to apply to the player.
        plugin_filters: :class:`wavelink.PluginFilters`
            The extra Plugin Filters to apply to the player. See :class:`~wavelink.PluginFilters` for more details.
        reset: bool
            Whether to reset all filters that were not specified.
        """

        self = cls()
        self._set_with_reset(filters)

        return self

    @property
    def volume(self) -> float | None:
        """Property which returns the volume ``float`` associated with this Filters payload.

        Adjusts the player volume from 0.0 to 5.0, where 1.0 is 100%. Values >1.0 may cause clipping.
        """
        return self._volume

    @volume.setter
    def volume(self, value: float) -> None:
        self._volume = value

    @property
    def equalizer(self) -> Equalizer:
        """Property which returns the :class:`~wavelink.Equalizer` filter associated with this Filters payload."""
        return self._equalizer

    @property
    def karaoke(self) -> Karaoke:
        """Property which returns the :class:`~wavelink.Karaoke` filter associated with this Filters payload."""
        return self._karaoke

    @property
    def timescale(self) -> Timescale:
        """Property which returns the :class:`~wavelink.Timescale` filter associated with this Filters payload."""
        return self._timescale

    @property
    def tremolo(self) -> Tremolo:
        """Property which returns the :class:`~wavelink.Tremolo` filter associated with this Filters payload."""
        return self._tremolo

    @property
    def vibrato(self) -> Vibrato:
        """Property which returns the :class:`~wavelink.Vibrato` filter associated with this Filters payload."""
        return self._vibrato

    @property
    def rotation(self) -> Rotation:
        """Property which returns the :class:`~wavelink.Rotation` filter associated with this Filters payload."""
        return self._rotation

    @property
    def distortion(self) -> Distortion:
        """Property which returns the :class:`~wavelink.Distortion` filter associated with this Filters payload."""
        return self._distortion

    @property
    def channel_mix(self) -> ChannelMix:
        """Property which returns the :class:`~wavelink.ChannelMix` filter associated with this Filters payload."""
        return self._channel_mix

    @property
    def low_pass(self) -> LowPass:
        """Property which returns the :class:`~wavelink.LowPass` filter associated with this Filters payload."""
        return self._low_pass

    @property
    def plugin_filters(self) -> PluginFilters:
        """Property which returns the :class:`~wavelink.PluginFilters` filters associated with this Filters payload."""
        return self._plugin_filters

    def __call__(self) -> FilterPayload:
        payload: FilterPayload = {
            "volume": self._volume,
            "equalizer": list(self._equalizer._payload.values()),
            "karaoke": self._karaoke._payload,
            "timescale": self._timescale._payload,
            "tremolo": self._tremolo._payload,
            "vibrato": self._vibrato._payload,
            "rotation": self._rotation._payload,
            "distortion": self._distortion._payload,
            "channelMix": self._channel_mix._payload,
            "lowPass": self._low_pass._payload,
            "pluginFilters": self._plugin_filters._payload,
        }

        for key, value in payload.copy().items():
            if not value:
                del payload[key]

        return payload

    def __repr__(self) -> str:
        return (
            f"<Filters: volume={self._volume}, equalizer={self._equalizer!r}, karaoke={self._karaoke!r},"
            f" timescale={self._timescale!r}, tremolo={self._tremolo!r}, vibrato={self._vibrato!r},"
            f" rotation={self._rotation!r}, distortion={self._distortion!r}, channel_mix={self._channel_mix!r},"
            f" low_pass={self._low_pass!r}, plugin_filters={self._plugin_filters!r}>"
        )
