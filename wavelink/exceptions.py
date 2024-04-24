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

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .types.response import ErrorResponse, LoadedErrorPayload


__all__ = (
    "WavelinkException",
    "NodeException",
    "InvalidClientException",
    "AuthorizationFailedException",
    "InvalidNodeException",
    "LavalinkException",
    "LavalinkLoadException",
    "InvalidChannelStateException",
    "ChannelTimeoutException",
    "QueueEmpty",
)


class WavelinkException(Exception):
    """Base wavelink Exception class.

    All wavelink exceptions derive from this exception.
    """


class NodeException(WavelinkException):
    """Error raised when an Unknown or Generic error occurs on a Node.

    This exception may be raised when an error occurs reaching your Node.

    Attributes
    ----------
    status: int | None
        The status code received when making a request. Could be None.
    """

    def __init__(self, msg: str | None = None, status: int | None = None) -> None:
        super().__init__(msg)

        self.status = status


class InvalidClientException(WavelinkException):
    """Exception raised when an invalid :class:`discord.Client`
    is provided while connecting a :class:`wavelink.Node`.
    """


class AuthorizationFailedException(WavelinkException):
    """Exception raised when Lavalink fails to authenticate a :class:`~wavelink.Node`, with the provided password."""


class InvalidNodeException(WavelinkException):
    """Exception raised when a :class:`Node` is tried to be retrieved from the
    :class:`Pool` without existing, or the ``Pool`` is empty.
    """


class LavalinkException(WavelinkException):
    """Exception raised when Lavalink returns an invalid response.

    Attributes
    ----------
    status: int
        The response status code.
    reason: str | None
        The response reason. Could be ``None`` if no reason was provided.
    """

    def __init__(self, msg: str | None = None, /, *, data: ErrorResponse) -> None:
        self.timestamp: int = data["timestamp"]
        self.status: int = data["status"]
        self.error: str = data["error"]
        self.trace: str | None = data.get("trace")
        self.path: str = data["path"]

        if not msg:
            msg = f"Failed to fulfill request to Lavalink: status={self.status}, reason={self.error}, path={self.path}"

        super().__init__(msg)


class LavalinkLoadException(WavelinkException):
    """Exception raised when an error occurred loading tracks via Lavalink.

    Attributes
    ----------
    error: str
        The error message from Lavalink.
    severity: str
        The severity of this error sent via Lavalink.
    cause: str
        The cause of this error sent via Lavalink.
    """

    def __init__(self, msg: str | None = None, /, *, data: LoadedErrorPayload) -> None:
        self.error: str = data["message"]
        self.severity: str = data["severity"]
        self.cause: str = data["cause"]

        if not msg:
            msg = f"Failed to Load Tracks: error={self.error}, severity={self.severity}, cause={self.cause}"

        super().__init__(msg)


class InvalidChannelStateException(WavelinkException):
    """Exception raised when a :class:`~wavelink.Player` tries to connect to an invalid channel or
    has invalid permissions to use this channel.
    """


class ChannelTimeoutException(WavelinkException):
    """Exception raised when connecting to a voice channel times out."""


class QueueEmpty(WavelinkException):
    """Exception raised when you try to retrieve from an empty queue."""
