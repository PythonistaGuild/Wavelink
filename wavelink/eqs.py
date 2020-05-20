"""MIT License

Copyright (c) 2019-2020 PythonistaGuild

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
import collections
from typing import DefaultDict, List, Tuple


class Equalizer:
    """Class representing a usuable equalizer.

    Attributes
    ------------
    eq: list
        A list of {'band': int, 'gain': float}
    raw: list
        A list of tuple pairs containing a band int and gain float.
    """

    def __init__(self, levels: List[Tuple[int, float]]):
        _band_dict: DefaultDict[int, float] = collections.defaultdict(int)

        _band_dict.update(levels)
        _dict = [{"band": i, "gain": _band_dict[i]} for i in range(15)]

        self.eq = _dict
        self.raw = levels

    @classmethod
    def build(cls, *, levels: List[Tuple[int, float]]) -> Equalizer:
        """Build an Equalizer class with the provided levels.

        Parameters
        ------------
        levels: List[Tuple[int, float]]
            A list of tuple pairs containing a band int and gain float.
        """
        return cls(levels)

    @classmethod
    def flat(cls) -> Equalizer:
        """Flat Equalizer.

        Resets your EQ to Flat.
        """
        return cls(
            [
                (0, 0.0),
                (1, 0.0),
                (2, 0.0),
                (3, 0.0),
                (4, 0.0),
                (5, 0.0),
                (6, 0.0),
                (7, 0.0),
                (8, 0.0),
                (9, 0.0),
                (10, 0.0),
                (11, 0.0),
                (12, 0.0),
                (13, 0.0),
                (14, 0.0),
            ]
        )

    @classmethod
    def boost(cls) -> Equalizer:
        """Boost Equalizer.

        This equalizer emphasizes Punchy Bass and Crisp Mid-High tones.
        Not suitable for tracks with Deep/Low Bass.
        """
        return cls(
            [
                (0, -0.075),
                (1, 0.125),
                (2, 0.125),
                (3, 0.1),
                (4, 0.1),
                (5, 0.05),
                (6, 0.075),
                (7, 0.0),
                (8, 0.0),
                (9, 0.0),
                (10, 0.0),
                (11, 0.0),
                (12, 0.125),
                (13, 0.15),
                (14, 0.05),
            ]
        )

    @classmethod
    def metal(cls) -> Equalizer:
        """Experimental Metal/Rock Equalizer.

        Expect clipping on Bassy songs.
        """
        return cls(
            [
                (0, 0.0),
                (1, 0.1),
                (2, 0.1),
                (3, 0.15),
                (4, 0.13),
                (5, 0.1),
                (6, 0.0),
                (7, 0.125),
                (8, 0.175),
                (9, 0.175),
                (10, 0.125),
                (11, 0.125),
                (12, 0.1),
                (13, 0.075),
                (14, 0.0),
            ]
        )

    @classmethod
    def piano(cls) -> Equalizer:
        """Piano Equalizer.

        Suitable for Piano tracks, or tacks with an emphasis on Female Vocals.
        Could also be used as a Bass Cutoff.
        """
        return cls(
            [
                (0, -0.25),
                (1, -0.25),
                (2, -0.125),
                (3, 0.0),
                (4, 0.25),
                (5, 0.25),
                (6, 0.0),
                (7, -0.25),
                (8, -0.25),
                (9, 0.0),
                (10, 0.0),
                (11, 0.5),
                (12, 0.25),
                (13, -0.025),
            ]
        )
