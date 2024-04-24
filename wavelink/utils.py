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

from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any


__all__ = (
    "Namespace",
    "ExtrasNamespace",
)


class Namespace(SimpleNamespace):
    def __iter__(self) -> Iterator[tuple[str, Any]]:
        return iter(self.__dict__.items())


class ExtrasNamespace(Namespace):
    """A subclass of :class:`types.SimpleNameSpace`.

    You can construct this namespace with a :class:`dict` of `str` keys and `Any` value, or with keyword pairs or
    with a mix of both.

    You can access a dict version of this namespace by calling `dict()` on an instance.


    Examples
    --------

        .. code:: python

            ns: ExtrasNamespace = ExtrasNamespace({"hello": "world!"}, stuff=1)

            # Later...
            print(ns.hello)
            print(ns.stuff)
            print(dict(ns))
    """

    def __init__(self, __dict: dict[str, Any] = {}, /, **kwargs: Any) -> None:
        updated = __dict | kwargs
        super().__init__(**updated)
