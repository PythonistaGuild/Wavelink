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

from .enums import ErrorSeverity
from discord.enums import try_enum


__all__ = (
    "WavelinkError",
    "AuthorizationFailure",
    "LavalinkException",
    "LoadTrackError",
    "BuildTrackError",
    "NodeOccupied",
    "InvalidIDProvided",
    "ZeroConnectedNodes",
    "NoMatchingNode",
    "QueueException",
    "QueueFull",
    "QueueEmpty",
)


class WavelinkError(Exception):
    """Base WaveLink Exception"""


class AuthorizationFailure(WavelinkError):
    """Exception raised when an invalid password is provided toa node."""


class LavalinkException(WavelinkError):
    """Exception raised when an error occurs talking to Lavalink."""


class LoadTrackError(LavalinkException):
    """Exception raised when an error occurred when loading a track."""

    def __init__(self, data):
        exception = data["exception"]
        self.severity: ErrorSeverity = try_enum(ErrorSeverity, exception["severity"])
        super().__init__(exception["message"])


class BuildTrackError(LavalinkException):
    """Exception raised when a track is failed to be decoded and re-built."""

    def __init__(self, data):
        super().__init__(data["error"])


class NodeOccupied(WavelinkError):
    """Exception raised when node identifiers conflict."""


class InvalidIDProvided(WavelinkError):
    """Exception raised when an invalid ID is passed somewhere in Wavelink."""


class ZeroConnectedNodes(WavelinkError):
    """Exception raised when an operation is attempted with nodes, when there are None connected."""


class NoMatchingNode(WavelinkError):
    """Exception raised when a Node is attempted to be retrieved with a incorrect identifier."""


class QueueException(WavelinkError):
    """Base WaveLink Queue exception."""

    pass


class QueueFull(QueueException):
    """Exception raised when attempting to add to a full Queue."""

    pass


class QueueEmpty(QueueException):
    """Exception raised when attempting to retrieve from an empty Queue."""

    pass
