from typing import Any


__all__ = ("MISSING",)


class _MissingSentinel:
    def __repr__(self) -> str:
        return "MISSING"

    def __bool__(self) -> bool:
        return False


MISSING: Any = _MissingSentinel()
