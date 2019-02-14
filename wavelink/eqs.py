import collections


class Equalizer:

    def __init__(self, levels: list):
        _dict = collections.defaultdict(int)

        _dict.update(levels)
        _dict = [{"band": i, "gain": _dict[i]} for i in range(15)]

        self.eq = _dict
        self.raw = levels

    @classmethod
    def build(cls, *, levels: list):
        return cls(levels)

    @classmethod
    def flat(cls):
        """Flat Equalizer.

        Resets your EQ to Flat.
        """
        return cls([(0, .0), (1, .0), (2, .0), (3, .0), (4, .0),
                    (5, .0), (6, .0), (7, .0), (8, .0), (9, .0),
                    (10, .0), (11, .0), (12, .0), (13, .0), (14, .0)])

    @classmethod
    def boost(cls):
        """Boost Equalizer.

        This equalizer emphasizes Punchy Bass and Crisp Mid-High tones.
        Not suitable for tracks with Deep/Low Bass.
        """
        return cls([(0, -0.075), (1, .125), (2, .125), (3, .1), (4, .1),
                    (5, .05), (6, 0.075), (7, .0), (8, .0), (9, .0),
                    (10, .0), (11, .0), (12, .125), (13, .15), (14, .05)])

    @classmethod
    def metal(cls):
        """Experimental Metal/Rock Equalizer.

        Expect clipping on Bassy songs.
        """
        return cls([(0, .0), (1, .1), (2, .1), (3, .15), (4, .13),
                    (5, .1), (6, .0), (7, .125), (8, .175), (9, .175),
                    (10, .125), (11, .125), (12, .1), (13, .075), (14, .0)])

    @classmethod
    def piano(cls):
        """Piano Equalizer.

        Suitable for Piano tracks, or tacks with an emphasis on Female Vocals.
        Could also be used as a Bass Cutoff.
        """
        return cls([(0, -0.25), (1, -0.25), (2, -0.125), (3, 0.0),
                    (4, 0.25), (5, 0.25), (6, 0.0), (7, -0.25), (8, -0.25),
                    (9, 0.0), (10, 0.0), (11, 0.5), (12, 0.25), (13, -0.025)])
