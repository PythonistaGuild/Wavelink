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

from typing import TYPE_CHECKING, Any

from discord.enums import try_enum

from .enums import TrackEventType, DiscordVoiceCloseType

if TYPE_CHECKING:
    from .player import Player
    from .tracks import Playable
    from .types.events import EventOp

__all__ = ('TrackEventPayload', 'WebsocketClosedPayload')


class TrackEventPayload:
    """The Wavelink Track Event Payload.

    .. warning::

        This class should not be created manually, instead you will receive it from the
        various wavelink track events.

    Attributes
    ----------
    event: :class:`TrackEventType`
        An enum of the type of event.
    track: :class:`Playable`
        The track associated with this event.
    original: Optional[:class:`Playable`]
        The original requested track before conversion. Could be None.
    player: :class:`player.Player`
        The player associated with this event.
    reason: Optional[str]
        The reason this event was fired.
    """

    def __init__(self, *, data: EventOp, track: Playable, original: Playable | None, player: Player) -> None:
        self.event: TrackEventType = try_enum(TrackEventType, data['type'])
        self.track: Playable = track
        self.original: Playable | None = original
        self.player: Player = player

        self.reason: str = data.get('reason')


class WebsocketClosedPayload:
    """The Wavelink WebsocketClosed Event Payload.

    .. warning::

        This class should not be created manually, instead you will receive it from the
        wavelink `on_wavelink_websocket_closed` event.

    Attributes
    ----------
    code: :class:`DiscordVoiceCloseType`
        An Enum representing the close code from Discord.
    reason: Optional[str]
        The reason the Websocket was closed.
    by_discord: bool
        Whether the websocket was closed by Discord.
    player: :class:`player.Player`
        The player associated with this event.
    """

    def __init__(self, *, data: dict[str, Any], player: Player) -> None:
        self.code: DiscordVoiceCloseType = try_enum(DiscordVoiceCloseType, data['code'])
        self.reason: str = data.get('reason')
        self.by_discord: bool = data.get('byRemote')
        self.player: Player = player
