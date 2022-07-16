"""MIT License

Copyright (c) 2019-2022 PythonistaGuild

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

import abc
import collections
from typing import Any, Dict, List, Optional, Tuple


__all__ = (
    "BaseFilter",
    "Equalizer",
    "Karaoke",
    "Timescale",
    "Tremolo",
    "Vibrato",
    "Rotation",
    "Distortion",
    "ChannelMix",
    "LowPass",
    "Filter",
)


class BaseFilter(abc.ABC):

    def __init__(self, name: Optional[str] = None) -> None:
        self.name: str = name or "Unknown"

    def __repr__(self) -> str:
        return f"<wavelink.BaseFilter name={self.name}>"

    @property
    @abc.abstractmethod
    def _payload(self) -> Any:
        raise NotImplementedError


class Equalizer(BaseFilter):
    """An equalizer filter.

    Parameters
    ----------
    name: str
        The name of this filter. Can be used to differentiate between equalizer filters.
    bands: List[Dict[str, int]]
        A list of equalizer bands, each item is a dictionary with "band" and "gain" keys.
    """

    def __init__(
        self,
        name: str = "CustomEqualizer",
        *,
        bands: List[Tuple[int, float]]
    ) -> None:
        super().__init__(name=name)

        if any((band, gain) for band, gain in bands if band < 0 or band > 15 or gain < -0.25 or gain > 1.0):
            raise ValueError("Equalizer bands must be between 0 and 15 and gains between -0.25 and 1.0")

        _dict = collections.defaultdict(float)
        _dict.update(bands)

        self.bands = [{"band": band, "gain": _dict[band]} for band in range(15)]

    def __repr__(self) -> str:
        return f"<wavelink.Equalizer name={self.name}>"

    @property
    def _payload(self) -> List[Dict[str, float]]:
        return self.bands

    @classmethod
    def flat(cls) -> Equalizer:
        """A flat equalizer."""

        bands = [
            (0, 0.0), (1, 0.0), (2, 0.0), (3, 0.0), (4, 0.0),
            (5, 0.0), (6, 0.0), (7, 0.0), (8, 0.0), (9, 0.0),
            (10, 0.0), (11, 0.0), (12, 0.0), (13, 0.0), (14, 0.0)
        ]
        return cls(name="Flat EQ", bands=bands)

    @classmethod
    def boost(cls) -> Equalizer:
        """A boost equalizer."""

        bands = [
            (0, -0.075), (1, 0.125), (2, 0.125), (3, 0.1), (4, 0.1),
            (5, .05), (6, 0.075), (7, 0.0), (8, 0.0), (9, 0.0),
            (10, 0.0), (11, 0.0), (12, 0.125), (13, 0.15), (14, 0.05)
        ]
        return cls(name="Boost EQ", bands=bands)

    @classmethod
    def metal(cls) -> Equalizer:
        """A metal equalizer."""

        bands = [
            (0, 0.0), (1, 0.1), (2, 0.1), (3, 0.15), (4, 0.13),
            (5, 0.1), (6, 0.0), (7, 0.125), (8, 0.175), (9, 0.175),
            (10, 0.125), (11, 0.125), (12, 0.1), (13, 0.075), (14, 0.0)
        ]

        return cls(name="Metal EQ", bands=bands)

    @classmethod
    def piano(cls) -> Equalizer:
        """A piano equalizer."""

        bands = [
            (0, -0.25), (1, -0.25), (2, -0.125), (3, 0.0),
            (4, 0.25), (5, 0.25), (6, 0.0), (7, -0.25), (8, -0.25),
            (9, 0.0), (10, 0.0), (11, 0.5), (12, 0.25), (13, -0.025)
        ]
        return cls(name="Piano EQ", bands=bands)


class Karaoke(BaseFilter):
    """
    A Karaoke filter.

    The default values provided for all the parameters will play the track normally.

    Parameters
    ----------
    level: float
        How much of an effect this filter should have.
    mono_level: float
        How much of an effect this filter should have on mono tracks.
    filter_band: float
        The band this filter should target.
    filter_width: float
        The width of the band this filter should target.
    """

    def __init__(
        self,
        *,
        level: float = 1.0,
        mono_level: float = 1.0,
        filter_band: float = 220.0,
        filter_width: float = 100.0
    ) -> None:
        super().__init__(name="Karaoke")

        self.level: float = level
        self.mono_level: float = mono_level
        self.filter_band: float = filter_band
        self.filter_width: float = filter_width

    def __repr__(self) -> str:
        return f"<wavelink.Karaoke level={self.level}, mono_level={self.mono_level}, " \
               f"filter_band={self.filter_band}, filter_width={self.filter_width}>"

    @property
    def _payload(self) -> Dict[str, float]:
        return {
            "level":       self.level,
            "monoLevel":   self.mono_level,
            "filterBand":  self.filter_band,
            "filterWidth": self.filter_width
        }


class Timescale(BaseFilter):
    """A timescale filter.

    Increases or decreases the speed, pitch, and/or rate of tracks.

    The default values provided for ``speed``, ``pitch`` and ``rate`` will play the track normally.

    Parameters
    ----------
    speed: float
        A multiplier for the track playback speed. Should be more than or equal to 0.0.
    pitch: float
        A multiplier for the track pitch. Should be more than or equal to 0.0.
    rate: float
        A multiplier for the track rate (pitch + speed). Should be more than or equal to 0.0.
    """

    def __init__(
        self,
        *,
        speed: float = 1.0,
        pitch: float = 1.0,
        rate: float = 1.0,
    ) -> None:

        if speed < 0:
            raise ValueError("'speed' must be more than or equal to 0.")
        if pitch < 0:
            raise ValueError("'pitch' must be more than or equal to 0.")
        if rate < 0:
            raise ValueError("'rate' must be more than or equal to 0.")

        super().__init__(name="Timescale")

        self.speed: float = speed
        self.pitch: float = pitch
        self.rate: float = rate

    def __repr__(self) -> str:
        return f"<wavelink.Timescale speed={self.speed}, pitch={self.pitch}, rate={self.rate}>"

    @property
    def _payload(self) -> Dict[str, float]:
        return {
            "speed": self.speed,
            "pitch": self.pitch,
            "rate":  self.rate,
        }


class Tremolo(BaseFilter):
    """A tremolo filter.

    Creates a shuddering effect by quickly changing the volume.

    The default values provided for ``frequency`` and ``depth`` will play the track normally.

    Parameters
    ----------
    frequency: float
        How quickly the volume should change. Should be more than 0.0.
    depth: float
        How much the volume should change. Should be more than 0.0 and less than or equal to 1.0.
    """

    def __init__(
        self,
        *,
        frequency: float = 2.0,
        depth: float = 0.5
    ) -> None:

        if frequency < 0:
            raise ValueError("'frequency' must be more than 0.0.")
        if not 0 < depth <= 1:
            raise ValueError("'depth' must be more than 0.0 and less than or equal to 1.0.")

        super().__init__(name="Tremolo")

        self.frequency: float = frequency
        self.depth: float = depth

    def __repr__(self) -> str:
        return f"<wavelink.Tremolo frequency={self.frequency}, depth={self.depth}>"

    @property
    def _payload(self) -> Dict[str, float]:
        return {
            "frequency": self.frequency,
            "depth":     self.depth
        }


class Vibrato(BaseFilter):
    """A vibrato filter.

    Creates a vibrating effect by quickly changing the pitch.

    The default values provided for ``frequency`` and ``depth`` will play the track normally.

    Parameters
    ----------
    frequency: float
        How quickly the pitch should change. Should be more than 0.0 and less than or equal to 14.0.
    depth: float
        How much the pitch should change. Should be more than 0.0 and less than or equal to 1.0.
    """

    def __init__(
        self,
        *,
        frequency: float = 2.0,
        depth: float = 0.5
    ) -> None:

        if not 0 < frequency <= 14:
            raise ValueError("'frequency' must be more than 0.0 and less than or equal to 14.0.")
        if not 0 < depth <= 1:
            raise ValueError("'depth' must be more than 0.0 and less than or equal to 1.0.")

        super().__init__(name="Vibrato")

        self.frequency: float = frequency
        self.depth: float = depth

    def __repr__(self) -> str:
        return f"<wavelink.Vibrato frequency={self.frequency}, depth={self.depth}>"

    @property
    def _payload(self) -> Dict[str, float]:
        return {
            "frequency": self.frequency,
            "depth":     self.depth
        }


class Rotation(BaseFilter):
    """A rotation filter.

    Rotates the audio around stereo channels which can be used to create a 3D effect.

    The default value provided for ``speed`` will play the track normally.

    Parameters
    ----------
    speed: float
        The speed at which the audio should rotate.
    """

    def __init__(self, speed: float = 5) -> None:
        super().__init__(name="Rotation")

        self.speed: float = speed

    def __repr__(self) -> str:
        return f"<wavelink.Rotation speed={self.speed}>"

    @property
    def _payload(self) -> Dict[str, float]:
        return {
            "rotationHz": self.speed,
        }


class Distortion(BaseFilter):
    """A distortion filter."""

    def __init__(
        self,
        *,
        sin_offset: float = 0.0,
        sin_scale: float = 1.0,
        cos_offset: float = 0.0,
        cos_scale: float = 1.0,
        tan_offset: float = 0.0,
        tan_scale: float = 1.0,
        offset: float = 0.0,
        scale: float = 1.0
    ) -> None:
        super().__init__(name="Distortion")

        self.sin_offset: float = sin_offset
        self.sin_scale: float = sin_scale
        self.cos_offset: float = cos_offset
        self.cos_scale: float = cos_scale
        self.tan_offset: float = tan_offset
        self.tan_scale: float = tan_scale
        self.offset: float = offset
        self.scale: float = scale

    def __repr__(self) -> str:
        return f"<wavelink.Distortion " \
               f"sin_offset={self.sin_offset}, " \
               f"sin_scale={self.sin_scale}, cos_offset={self.cos_offset}, " \
               f"cos_scale={self.cos_scale}, tan_offset={self.tan_offset}, " \
               f"tan_scale={self.tan_scale}, offset={self.offset}, " \
               f"scale={self.scale}>"

    @property
    def _payload(self) -> Dict[str, float]:
        return {
            "sinOffset": self.sin_offset,
            "sinScale":  self.sin_scale,
            "cosOffset": self.cos_offset,
            "cosScale":  self.cos_scale,
            "tanOffset": self.tan_offset,
            "tanScale":  self.tan_scale,
            "offset":    self.offset,
            "scale":     self.scale
        }


class ChannelMix(BaseFilter):
    """A channel mix filter.

    Allows you to control what channel audio from the track is actually played on.

    Setting `left_to_left` and `right_to_right` to 1.0 will result in no change.
    Setting all channels to 0.5 will result in all channels receiving the same audio.

    The default values provided for all the parameters will play the track normally.

    Parameters
    ----------
    left_to_left: float
        The "percentage" of audio from the left channel that should actually get played on the left channel.
    left_to_right: float
        The "percentage" of audio from the left channel that should play on the right channel.
    right_to_left: float
        The "percentage" of audio from the right channel that should actually get played on the right channel.
    right_to_right: float
        The "percentage" of audio from the right channel that should play on the left channel.
    """

    def __init__(
        self,
        *,
        left_to_left: float = 1.0,
        left_to_right: float = 0.0,
        right_to_left: float = 0.0,
        right_to_right: float = 1.0,
    ) -> None:

        _all = (left_to_left, left_to_right, right_to_left, right_to_right)

        if any(value for value in _all if value < 0 or value > 1):
            raise ValueError(
                "'left_to_left', 'left_to_right', "
                "'right_to_left', and 'right_to_right' "
                "must all be between 0.0 and 1.0"
            )

        super().__init__(name="Channel Mix")

        self.left_to_left: float = left_to_left
        self.right_to_right: float = right_to_right
        self.left_to_right: float = left_to_right
        self.right_to_left: float = right_to_left

    def __repr__(self) -> str:
        return f"<wavelink.ChannelMix " \
               f"left_to_left={self.left_to_left}, " \
               f"right_to_right{self.right_to_right}, " \
               f"left_to_right={self.left_to_right}, " \
               f"right_to_left={self.right_to_left}>"

    @property
    def _payload(self) -> Dict[str, float]:
        return {
            "leftToLeft":   self.left_to_left,
            "leftToRight":  self.left_to_right,
            "rightToLeft":  self.right_to_left,
            "rightToRight": self.right_to_right,
        }

    @classmethod
    def mono(cls) -> ChannelMix:
        """Returns a ChannelMix filter that will play the track in mono."""
        return cls(left_to_left=0.5, left_to_right=0.5, right_to_left=0.5, right_to_right=0.5)

    @classmethod
    def only_left(cls) -> ChannelMix:
        """Returns a ChannelMix filter that will only play the tracks left channel."""
        return cls(left_to_left=1, left_to_right=0, right_to_left=0, right_to_right=0)

    @classmethod
    def full_left(cls) -> ChannelMix:
        """
        Returns a ChannelMix filter that will play the tracks left and right channels together only on the left channel.
        """
        return cls(left_to_left=1, left_to_right=0, right_to_left=1, right_to_right=0)

    @classmethod
    def only_right(cls) -> ChannelMix:
        """Returns a ChannelMix filter that will only play the tracks right channel."""
        return cls(left_to_left=0, left_to_right=0, right_to_left=0, right_to_right=1)

    @classmethod
    def full_right(cls) -> ChannelMix:
        """
        Returns a ChannelMix filter that will play the tracks left and right channels together only on the right channel.
        """
        return cls(left_to_left=0, left_to_right=1, right_to_left=0, right_to_right=1)

    @classmethod
    def switch(cls) -> ChannelMix:
        """Returns a ChannelMix filter that will switch the tracks left and right channels."""
        return cls(left_to_left=0, left_to_right=1, right_to_left=1, right_to_right=0)


class LowPass(BaseFilter):
    """A low pass filter.

    Suppresses higher frequencies while allowing lower frequencies to pass through.

    The default value provided for ``smoothing`` will play the track normally.

    Parameters
    ----------
    smoothing: float
        The factor by which the filter will block higher frequencies.
    """

    def __init__(
        self,
        *,
        smoothing: float = 20
    ) -> None:
        super().__init__(name="Low Pass")

        self.smoothing: float = smoothing

    def __repr__(self) -> str:
        return f"<wavelink.LowPass smoothing={self.smoothing}>"

    @property
    def _payload(self) -> Dict[str, float]:
        return {
            "smoothing": self.smoothing,
        }


class Filter:
    """A filter that can be applied to a track.

    This filter accepts an instance of itself as a parameter which allows
    you to keep previous filters while also applying new ones or overwriting old ones.

    Parameters
    ----------
    filter: wavelink.Filter
        An instance of this filter class.
    equalizer: wavelink.Equalizer
        An equalizer to apply to the track.
    karaoke: wavelink.Karaoke
        A karaoke filter to apply to the track.
    timescale: wavelink.Timescale
        A timescale filter to apply to the track.
    tremolo: wavelink.Tremolo
        A tremolo filter to apply to the track.
    vibrato: wavelink.Vibrato
        A vibrato filter to apply to the track.
    rotation: wavelink.Rotation
        A rotation filter to apply to the track.
    distortion: wavelink.Distortion
        A distortion filter to apply to the track.
    channel_mix: wavelink.ChannelMix
        A channel mix filter to apply to the track.
    low_pass: wavelink.LowPass
        A low pass filter to apply to the track.

    """

    def __init__(
        self,
        _filter: Optional[Filter] = None,
        /, *,
        equalizer: Optional[Equalizer] = None,
        karaoke: Optional[Karaoke] = None,
        timescale: Optional[Timescale] = None,
        tremolo: Optional[Tremolo] = None,
        vibrato: Optional[Vibrato] = None,
        rotation: Optional[Rotation] = None,
        distortion: Optional[Distortion] = None,
        channel_mix: Optional[ChannelMix] = None,
        low_pass: Optional[LowPass] = None
    ) -> None:

        self.filter: Optional[Filter] = _filter

        self.equalizer: Optional[Equalizer] = equalizer
        self.karaoke: Optional[Karaoke] = karaoke
        self.timescale: Optional[Timescale] = timescale
        self.tremolo: Optional[Tremolo] = tremolo
        self.vibrato: Optional[Vibrato] = vibrato
        self.rotation: Optional[Rotation] = rotation
        self.distortion: Optional[Distortion] = distortion
        self.channel_mix: Optional[ChannelMix] = channel_mix
        self.low_pass: Optional[LowPass] = low_pass

    def __repr__(self) -> str:
        return f"<wavelink.Filter equalizer={self.equalizer}, " \
               f"karaoke={self.karaoke}, timescale={self.timescale}, tremolo={self.tremolo}, " \
               f"vibrato={self.vibrato}, rotation={self.rotation}, distortion={self.distortion}, " \
               f"channel_mix={self.channel_mix}, low_pass={self.low_pass}>"

    @property
    def _payload(self) -> Dict[str, Any]:

        payload = self.filter._payload.copy() if self.filter else {}

        if self.equalizer:
            payload["equalizer"] = self.equalizer._payload
        if self.karaoke:
            payload["karaoke"] = self.karaoke._payload
        if self.timescale:
            payload["timescale"] = self.timescale._payload
        if self.tremolo:
            payload["tremolo"] = self.tremolo._payload
        if self.vibrato:
            payload["vibrato"] = self.vibrato._payload
        if self.rotation:
            payload["rotation"] = self.rotation._payload
        if self.distortion:
            payload["distortion"] = self.distortion._payload
        if self.channel_mix:
            payload["channelMix"] = self.channel_mix._payload
        if self.low_pass:
            payload["lowPass"] = self.low_pass._payload

        return payload
