"""
MIT License

Copyright (c) 2019-Present PythonistaGuild

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

from typing import Any

__all__ = (
    'WavelinkException',
    'AuthorizationFailed',
    'InvalidNode',
    'InvalidLavalinkVersion',
    'InvalidLavalinkResponse',
    'NoTracksError',
    'QueueEmpty',
    'InvalidChannelStateError',
    'InvalidChannelPermissions',
)


class WavelinkException(Exception):
    """Base wavelink exception."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args)


class AuthorizationFailed(WavelinkException):
    """Exception raised when password authorization failed for this Lavalink node."""
    pass


class InvalidNode(WavelinkException):
    pass


class InvalidLavalinkVersion(WavelinkException):
    """Exception raised when you try to use wavelink 2 with a Lavalink version under 3.7."""
    pass


class InvalidLavalinkResponse(WavelinkException):
    """Exception raised when wavelink receives an invalid response from Lavalink.

    Attributes
    ----------
    status: int | None
        The status code. Could be None.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args)
        self.status: int | None = kwargs.get('status')


class NoTracksError(WavelinkException):
    """Exception raised when no tracks could be found."""
    pass


class QueueEmpty(WavelinkException):
    """Exception raised when you try to retrieve from an empty queue."""
    pass


class InvalidChannelStateError(WavelinkException):
    """Base exception raised when an error occurs trying to connect to a :class:`discord.VoiceChannel`."""


class InvalidChannelPermissions(InvalidChannelStateError):
    """Exception raised when the client does not have correct permissions to join the channel.

    Could also be raised when there are too many users already in a user limited channel.
    """