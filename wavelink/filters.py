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

import abc
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

__all__ = [
    'BaseFilter',
    'Tremolo',
    'Equalizer',
    'Distortion',
    'Timescale',
    'Karaoke',
    'ChannelMix',
    'Vibrato',
    'Rotation',
    'LowPass',
    'Filter'
]


class BaseFilter(abc.ABC):
    """
    An abstract base class that all filter objects must inherit from.
    """

    def __init__(self) -> None:
        self._name = 'BaseFilter'

    def __repr__(self) -> str:
        return f'wavelink.BaseFilter name=\'{self.name}\''

    def __str__(self) -> str:
        return self._name

    @property
    def name(self) -> str:
        """
        :py:class:`str`:
            The name of this filter.
        """
        return self._name

    @property
    @abc.abstractmethod
    def _payload(self) -> Any:
        raise NotImplementedError


class Equalizer(BaseFilter):

    def __init__(self, *, levels: List[Tuple[int, float]], name='Equalizer') -> None:
        super().__init__()

        self.levels: List[Tuple[int, float]] = levels
        self.eq: List[Dict[str, float]] = self._factory(levels)

        self._name = name

    def __repr__(self) -> str:
        return f'<wavelink.Equalizer name=\'{self._name}\' gains={self.eq}>'

    @staticmethod
    def _factory(levels: List[Tuple[int, float]]) -> List[Dict[str, int]]:

        _dict = defaultdict(int)

        _dict.update(levels)
        _dict = [{'band': i, 'gain': _dict[i]} for i in range(15)]

        return _dict

    @property
    def _payload(self) -> List[Dict[str, float]]:
        return self.eq

    #

    @classmethod
    def flat(cls) -> Equalizer:

        levels = [
            (0, 0.0), (1, 0.0), (2, 0.0), (3, 0.0), (4, 0.0), (5, 0.0), (6, 0.0),
            (7, 0.0), (8, 0.0), (9, 0.0), (10, 0.0), (11, 0.0), (12, 0.0), (13, 0.0), (14, 0.0)
        ]

        return cls(levels=levels, name='Flat')

    @classmethod
    def boost(cls) -> Equalizer:

        levels = [
            (0, -0.075), (1, 0.125), (2, 0.125), (3, 0.1), (4, 0.1), (5, 0.05), (6, 0.075),
            (7, 0.0), (8, 0.0), (9, 0.0), (10, 0.0), (11, 0.0), (12, 0.125), (13, 0.15), (14, 0.05)
        ]

        return cls(levels=levels, name='Boost')

    @classmethod
    def metal(cls) -> Equalizer:

        levels = [
            (0, 0.0), (1, 0.1), (2, 0.1), (3, 0.15), (4, 0.13), (5, 0.1), (6, 0.0),
            (7, 0.125), (8, 0.175), (9, 0.175), (10, 0.125), (11, 0.125), (12, 0.1), (13, 0.075), (14, 0.0)
        ]

        return cls(levels=levels, name='Metal')

    @classmethod
    def piano(cls) -> Equalizer:

        levels = [
            (0, -0.25), (1, -0.25), (2, -0.125), (3, 0.0), (4, 0.25), (5, 0.25), (6, 0.0),
            (7, -0.25), (8, -0.25), (9, 0.0), (10, 0.0), (11, 0.5), (12, 0.25), (13, -0.025)
        ]

        return cls(levels=levels, name='Piano')


class Karaoke(BaseFilter):

    def __init__(
            self, *, level: float = 1.0, mono_level: float = 1.0, filter_band: float = 220.0,
            filter_width: float = 100.0
    ) -> None:
        super().__init__()

        self.level: float = level
        self.mono_level: float = mono_level
        self.filter_band: float = filter_band
        self.filter_width: float = filter_width

        self._name = 'Karaoke'

    def __repr__(self) -> str:
        return f'<wavelink.Karaoke level={self.level} mono_level={self.mono_level} filter_band={self.filter_band} ' \
               f'filter_width={self.filter_width}>'

    @property
    def _payload(self) -> Dict[str, float]:
        return {
            'level': self.level, 'mono_level': self.mono_level, 'filter_band': self.filter_band,
            'filter_width': self.filter_width
        }


class Timescale(BaseFilter):

    def __init__(
            self, *, pitch: float = 1.0, pitch_octaves: Optional[float] = None,
            pitch_semi_tones: Optional[float] = None, rate: float = 1.0, rate_change: Optional[float] = None,
            speed: float = 1.0, speed_change: Optional[float] = None
    ) -> None:
        super().__init__()

        if (pitch_octaves and pitch) or (pitch_semi_tones and pitch) or (pitch_octaves and pitch_semi_tones):
            raise ValueError('Only one of \'pitch\', \'pitch_octaves\' and \'pitch_semi_tones\' may be set.')
        if rate and rate_change:
            raise ValueError('Only one of \'rate\' and \'rate_change\' may be set.')
        if speed and speed_change:
            raise ValueError('Only one of \'speed\' and \'speed_change\' may be set.')

        self.pitch: float = pitch
        self.pitch_octaves: Optional[float] = pitch_octaves
        self.pitch_semi_tones: Optional[float] = pitch_semi_tones

        self.rate: float = rate
        self.rate_change: Optional[float] = rate_change

        self.speed: float = speed
        self.speed_change: Optional[float] = speed_change

        self._name = 'Timescale'

    def __repr__(self) -> str:
        return f'<wavelink.Timescale pitch={self.pitch} pitch_octaves={self.pitch_octaves} ' \
               f'pitch_semi_tones={self.pitch_semi_tones} rate={self.rate} rate_change={self.rate_change} ' \
               f'speed={self.speed} speed_change={self.speed_change}>'

    @property
    def _payload(self) -> Dict[str, Optional[float]]:
        return {
            'pitch': self.pitch, 'pitch_octaves': self.pitch_octaves, 'pitch_semi_tones': self.pitch_semi_tones,
            'rate': self.rate, 'rate_change': self.rate_change, 'speed': self.speed, 'speed_change': self.speed_change
        }


class Tremolo(BaseFilter):

    def __init__(self, *, frequency: float = 2.0, depth: float = 0.5) -> None:
        super().__init__()

        if frequency < 0:
            raise ValueError('Frequency must be more than 0.0')
        if not 0 < depth <= 1:
            raise ValueError('Depth must be more than 0.0 and less than or equal to 1.0')

        self.frequency: float = frequency
        self.depth: float = depth

        self._name: str = 'Tremolo'

    def __repr__(self) -> str:
        return f'<wavelink.Tremolo frequency={self.frequency} depth={self.depth}>'

    @property
    def _payload(self) -> Dict[str, float]:
        return {'frequency': self.frequency, 'depth': self.depth}


class Vibrato(BaseFilter):

    def __init__(self, *, frequency: float = 2.0, depth: float = 0.5) -> None:
        super().__init__()

        if not 0 < frequency <= 14:
            raise ValueError('Frequency must be more than 0.0 and less than or equal to 14.0')
        if not 0 < depth <= 1:
            raise ValueError('Depth must be more than 0.0 and less than or equal to 1.0')

        self.frequency: float = frequency
        self.depth: float = depth

        self._name = 'Vibrato'

    def __repr__(self) -> str:
        return f'<wavelink.Vibrato frequency={self.frequency} depth={self.depth}>'

    #

    @property
    def _payload(self) -> Dict[str, float]:
        return {'frequency': self.frequency, 'depth': self.depth}


class Rotation(BaseFilter):

    def __init__(self, *, rotation_hertz: float = 5) -> None:
        super().__init__()

        self.rotation_hertz: float = rotation_hertz

        self._name = 'Rotation'

    def __repr__(self) -> str:
        return f'<wavelink.Rotation rotation_hertz={self.rotation_hertz}>'

    @property
    def _payload(self) -> Dict[str, float]:
        return {'rotationHz': self.rotation_hertz}


class Distortion(BaseFilter):

    def __init__(
            self, *, sin_offset: int = 0, sin_scale: int = 1, cos_offset: int = 0, cos_scale: int = 1,
            tan_offset: int = 0, tan_scale: int = 1, offset: int = 0, scale: int = 1
    ) -> None:
        super().__init__()

        self.sin_offset: int = sin_offset
        self.sin_scale: int = sin_scale
        self.cos_offset: int = cos_offset
        self.cos_scale: int = cos_scale
        self.tan_offset: int = tan_offset
        self.tan_scale: int = tan_scale
        self.offset: int = offset
        self.scale: int = scale

        self._name = 'Distortion'

    def __repr__(self) -> str:
        return f'<wavelink.Distortion sin_offset={self.sin_offset} sin_scale={self.sin_scale} ' \
               f'cos_offset={self.cos_offset} cos_scale={self.cos_scale} tan_offset={self.tan_offset} ' \
               f'tan_scale={self.tan_scale}' \
               f'offset={self.offset} scale={self.scale}>'

    @property
    def _payload(self) -> Dict[str, float]:
        return {
            'sinOffset': self.sin_offset, 'sinScale': self.sin_scale, 'cosOffset': self.cos_offset,
            'cosScale': self.cos_scale, 'tanOffset': self.tan_offset, 'tanScale': self.tan_scale,
            'offset': self.offset, 'scale': self.scale
        }


class ChannelMix(BaseFilter):

    def __init__(
            self, *, left_to_left: float = 1, right_to_right: float = 1, left_to_right: float = 0,
            right_to_left: float = 0
    ) -> None:
        super().__init__()

        if 0 > left_to_left > 1:
            raise ValueError('\'left_to_left\' value must be more than or equal to 0 or less than or equal to 1.')
        if 0 > right_to_right > 1:
            raise ValueError('\'right_to_right\' value must be more than or equal to 0 or less than or equal to 1.')
        if 0 > left_to_right > 1:
            raise ValueError('\'left_to_right\' value must be more than or equal to 0 or less than or equal to 1.')
        if 0 > right_to_left > 1:
            raise ValueError('\'right_to_left\' value must be more than or equal to 0 or less than or equal to 1.')

        self.left_to_left: float = left_to_left
        self.right_to_right: float = right_to_right
        self.left_to_right: float = left_to_right
        self.right_to_left: float = right_to_left

        self._name = 'Channel Mix'

    def __repr__(self) -> str:
        return f'<wavelink.ChannelMix left_to_left={self.left_to_left} right_to_right{self.right_to_right} ' \
               f'left_to_right={self.left_to_right} right_to_left={self.right_to_left}>'

    @property
    def _payload(self) -> Dict[str, float]:
        return {
            'left_to_left': self.left_to_left, 'right_to_right': self.right_to_right,
            'left_to_right': self.left_to_right, 'right_to_left': self.right_to_left
        }


class LowPass(BaseFilter):

    def __init__(self, *, smoothing: float = 20) -> None:
        super().__init__()

        self.smoothing: float = smoothing

        self._name = 'Low Pass'

    def __repr__(self) -> str:
        return f'<wavelink.LowPass smoothing={self.smoothing}>'

    @property
    def _payload(self) -> Dict[str, float]:
        return {'smoothing': self.smoothing}


class Filter:

    def __init__(
            self, filter: Optional[Filter] = None, *, volume: Optional[float] = None,
            tremolo: Optional[Tremolo] = None, equalizer: Optional[Equalizer] = None,
            distortion: Optional[Distortion] = None, timescale: Optional[Timescale] = None,
            karaoke: Optional[Karaoke] = None, channel_mix: Optional[ChannelMix] = None,
            vibrato: Optional[Vibrato] = None, rotation: Optional[Rotation] = None,
            low_pass: Optional[LowPass] = None
    ) -> None:

        self.filter: Optional[Filter] = filter

        self.volume: Optional[float] = volume
        self.tremolo: Optional[Tremolo] = tremolo
        self.equalizer: Optional[Equalizer] = equalizer
        self.distortion: Optional[Distortion] = distortion
        self.timescale: Optional[Timescale] = timescale
        self.karaoke: Optional[Karaoke] = karaoke
        self.channel_mix: Optional[ChannelMix] = channel_mix
        self.vibrato: Optional[Vibrato] = vibrato
        self.rotation: Optional[Rotation] = rotation
        self.low_pass: Optional[LowPass] = low_pass

    def __repr__(self) -> str:
        return f'<wavelink.Filter>'

    @property
    def _payload(self):

        payload = self.filter._payload.copy() if self.filter else {}

        if self.volume:
            payload['volume'] = self.volume
        if self.equalizer:
            payload['equalizer'] = self.equalizer._payload
        if self.karaoke:
            payload['karaoke'] = self.karaoke._payload
        if self.timescale:
            payload['timescale'] = self.timescale._payload
        if self.tremolo:
            payload['tremolo'] = self.tremolo._payload
        if self.vibrato:
            payload['vibrato'] = self.vibrato._payload
        if self.rotation:
            payload['rotation'] = self.rotation._payload
        if self.distortion:
            payload['distortion'] = self.distortion._payload
        if self.channel_mix:
            payload['channel_mix'] = self.channel_mix._payload
        if self.low_pass:
            payload['low_pass'] = self.low_pass._payload

        return payload
