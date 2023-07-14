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


__all__ = (
    "WavelinkException",
    "InvalidClientException",
    "AuthorizationFailedException",
    "InvalidNodeException",
    "LavalinkException",
    "InvalidChannelStateException",
)


class WavelinkException(Exception):
    """Base wavelink Exception class.

    All wavelink exceptions derive from this exception.
    """


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

    def __init__(self, message: str, /, *, status: int, reason: str | None) -> None:
        self.status = status
        self.reason = reason

        super().__init__(message)


class InvalidChannelStateException(WavelinkException):
    """Exception raised when a :class:`~wavelink.Player` tries to connect to an invalid channel or
    has invalid permissions to use this channel.
    """
