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
    """Class representing a usable equalizer.

    Parameters
    ------------
    levels: List[Tuple[int, float]]
        A list of tuple pairs containing a band int and gain float.
    name: str
        An Optional string to name this Equalizer. Defaults to 'CustomEqualizer'

    Attributes
    ------------
    eq: list
        A list of {'band': int, 'gain': float}
    raw: list
        A list of tuple pairs containing a band int and gain float.
    """
    def __init__(self, *, levels: list, name: str = 'CustomEqualizer'):
        self.eq = self._factory(levels)
        self.raw = levels

        self._name = name

    def __str__(self):
        return self._name

    def __repr__(self):
        return f'<wavelink.eqs.Equalizer: {self._name}, Raw: {self.eq}>'

    @property
    def name(self):
        """The Equalizers friendly name."""
        return self._name

    @staticmethod
    def _factory(levels: list):
        _dict = collections.defaultdict(int)

        _dict.update(levels)
        _dict = [{"band": i, "gain": _dict[i]} for i in range(15)]

        return _dict

    @classmethod
    def build(cls, *, levels: list, name: str = 'CustomEqualizer'):
        """Build a custom Equalizer class with the provided levels.

        Parameters
        ------------
        levels: List[Tuple[int, float]]
            A list of tuple pairs containing a band int and gain float.
        name: str
            An Optional string to name this Equalizer. Defaults to 'CustomEqualizer'
        """
        return cls(levels=levels, name=name)

    @classmethod
    def flat(cls):
        """Flat Equalizer.

        Resets your EQ to Flat.
        """
        levels = [(0, .0), (1, .0), (2, .0), (3, .0), (4, .0),
                  (5, .0), (6, .0), (7, .0), (8, .0), (9, .0),
                  (10, .0), (11, .0), (12, .0), (13, .0), (14, .0)]

        return cls(levels=levels, name='Flat')

    @classmethod
    def boost(cls):
        """Boost Equalizer.

        This equalizer emphasizes Punchy Bass and Crisp Mid-High tones.
        Not suitable for tracks with Deep/Low Bass.
        """
        levels = [(0, -0.075), (1, .125), (2, .125), (3, .1), (4, .1),
                  (5, .05), (6, 0.075), (7, .0), (8, .0), (9, .0),
                  (10, .0), (11, .0), (12, .125), (13, .15), (14, .05)]

        return cls(levels=levels, name='Boost')

    @classmethod
    def metal(cls):
        """Experimental Metal/Rock Equalizer.

        Expect clipping on Bassy songs.
        """
        levels = [(0, .0), (1, .1), (2, .1), (3, .15), (4, .13),
                  (5, .1), (6, .0), (7, .125), (8, .175), (9, .175),
                  (10, .125), (11, .125), (12, .1), (13, .075), (14, .0)]

        return cls(levels=levels, name='Metal')

    @classmethod
    def piano(cls):
        """Piano Equalizer.

        Suitable for Piano tracks, or tacks with an emphasis on Female Vocals.
        Could also be used as a Bass Cutoff.
        """
        levels = [(0, -0.25), (1, -0.25), (2, -0.125), (3, 0.0),
                  (4, 0.25), (5, 0.25), (6, 0.0), (7, -0.25), (8, -0.25),
                  (9, 0.0), (10, 0.0), (11, 0.5), (12, 0.25), (13, -0.025)]

        return cls(levels=levels, name='Piano')
