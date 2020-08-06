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


class Equalizer:
    """Class representing a usuable equalizer.

    .. warning::
        You can only create Equalizers through the provided class methods.

    Attributes
    ------------
    eq: list
        A list of {'band': int, 'gain': float}
    raw: list
        A list of tuple pairs containing a band int and gain float.
    """
    def __init__(self):
        raise NotImplementedError

    @staticmethod
    def _factory(levels: list):
        _dict = collections.defaultdict(int)

        _dict.update(levels)
        _dict = [{"band": i, "gain": _dict[i]} for i in range(15)]

        return _dict

    @classmethod
    def build(cls, *, levels: list):
        """Build a custom Equalizer class with the provided levels.

        Parameters
        ------------
        levels: List[Tuple[int, float]]
            A list of tuple pairs containing a band int and gain float.
        """
        self = cls.__new__(cls)
        self.eq = cls._factory(levels)
        self.raw = levels

        cls.__str__ = lambda _: 'CustomEqualizer'
        return self

    @classmethod
    def flat(cls):
        """Flat Equalizer.

        Resets your EQ to Flat.
        """
        levels = [(0, .0), (1, .0), (2, .0), (3, .0), (4, .0),
                  (5, .0), (6, .0), (7, .0), (8, .0), (9, .0),
                  (10, .0), (11, .0), (12, .0), (13, .0), (14, .0)]
        self = cls.__new__(cls)
        self.eq = cls._factory(levels)
        self.raw = levels

        cls.__str__ = lambda _: 'Flat'
        return self

    @classmethod
    def boost(cls):
        """Boost Equalizer.

        This equalizer emphasizes Punchy Bass and Crisp Mid-High tones.
        Not suitable for tracks with Deep/Low Bass.
        """
        levels = [(0, -0.075), (1, .125), (2, .125), (3, .1), (4, .1),
                  (5, .05), (6, 0.075), (7, .0), (8, .0), (9, .0),
                  (10, .0), (11, .0), (12, .125), (13, .15), (14, .05)]

        self = cls.__new__(cls)
        self.eq = cls._factory(levels)
        self.raw = levels

        cls.__str__ = lambda _: 'Boost'
        return self

    @classmethod
    def metal(cls):
        """Experimental Metal/Rock Equalizer.

        Expect clipping on Bassy songs.
        """
        levels = [(0, .0), (1, .1), (2, .1), (3, .15), (4, .13),
                  (5, .1), (6, .0), (7, .125), (8, .175), (9, .175),
                  (10, .125), (11, .125), (12, .1), (13, .075), (14, .0)]

        self = cls.__new__(cls)
        self.eq = cls._factory(levels)
        self.raw = levels

        cls.__str__ = lambda _: 'Metal'
        return self

    @classmethod
    def piano(cls):
        """Piano Equalizer.

        Suitable for Piano tracks, or tacks with an emphasis on Female Vocals.
        Could also be used as a Bass Cutoff.
        """
        levels = [(0, -0.25), (1, -0.25), (2, -0.125), (3, 0.0),
                  (4, 0.25), (5, 0.25), (6, 0.0), (7, -0.25), (8, -0.25),
                  (9, 0.0), (10, 0.0), (11, 0.5), (12, 0.25), (13, -0.025)]

        self = cls.__new__(cls)
        self.eq = cls._factory(levels)
        self.raw = levels

        cls.__str__ = lambda _: 'Piano'
        return self
