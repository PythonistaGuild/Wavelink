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
        # 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
        return cls([(0, .0), (1, .0), (2, .0), (3, .0), (4, .0),
                    (5, .0), (6, .0), (7, .0), (8, .0), (9, .0),
                    (10, .0), (11, .0), (12, .0), (13, .0), (14, .0)])

    @classmethod
    def boost(cls):
        # -0.075 .175 .125 .125 .1 .1 .075 0 0 0 0 0 .125 .175 .1
        return cls([(0, -0.075), (1, .15), (2, .125), (3, .125), (4, .1),
                    (5, .1), (6, 0.075), (7, .0), (8, .0), (9, .0),
                    (10, .0), (11, .0), (12, .125), (13, .175), (14, .1)])

    @classmethod
    def metal(cls):
        # 0 .1 .1 .2 .16 .1 0 .15 .2 .25 .15 .15 .1 .075 .0
        return cls([(0, .0), (1, .1), (2, .1), (3, .2), (4, .16),
                    (5, .1), (6, .0), (7, .15), (8, .2), (9, .25),
                    (10, .15), (11, .15), (12, .1), (13, .075), (14, .0)])
