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
from __future__ import annotations

from typing import Any, Dict

from .enums import ErrorSeverity

__all__ = ('WavelinkException',
           'AuthorizationFailure',
           'LoadTrackError',
           'BuildTrackError',
           'NodeOccupied',
           'InvalidIDProvided',
           'ZeroConnectedNodes')


class WavelinkException(Exception):
    """Base Wavelink Exception."""


class AuthorizationFailure(WavelinkException):
    """Exception raised when an invalid password is provided toa node."""


class LoadTrackError(WavelinkException):
    """Exception raised when an error occured when loading a track."""

    def __init__(self, data: Dict[str, Any]):
        exception = data['exception']
        self.severity = ErrorSeverity.try_value(exception['severity'])
        super().__init__(exception['message'])


class BuildTrackError(WavelinkException):
    """Exception raised when a track is failed to be decoded and re-built."""

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data['error'])


class NodeOccupied(WavelinkException):
    """Exception raised when node identifiers conflict."""


class InvalidIDProvided(WavelinkException):
    """Exception raised when an invalid ID is passed somewhere in Wavelink."""


class ZeroConnectedNodes(WavelinkException):
    """Exception raised when an operation is attempted with nodes, when there are None connected."""
