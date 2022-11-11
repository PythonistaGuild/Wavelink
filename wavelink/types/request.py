from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from .state import VoiceState

if TYPE_CHECKING:
    from typing_extensions import TypeAlias


class Filters(TypedDict):
    ...


class _BaseRequest(TypedDict, total=False):
    voice: VoiceState
    position: int
    endTime: int
    volume: int
    paused: bool
    filters: Filters
    voice: VoiceState


class EncodedTrackRequest(_BaseRequest):
    encodedTrack: str | None


class IdentifierRequest(_BaseRequest):
    identifier: str


Request: TypeAlias = '_BaseRequest | EncodedTrackRequest | IdentifierRequest'
