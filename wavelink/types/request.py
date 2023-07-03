from __future__ import annotations

from typing import Optional, TypedDict, Union, TYPE_CHECKING

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
    encodedTrack: Optional[str]


class IdentifierRequest(_BaseRequest):
    identifier: str


Request: TypeAlias = Union[_BaseRequest, EncodedTrackRequest, IdentifierRequest]
