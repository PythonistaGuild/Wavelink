from typing import TYPE_CHECKING, Literal, TypedDict

if TYPE_CHECKING:
    from typing_extensions import NotRequired, TypeAlias


_TrackStartEventType = Literal["TrackStartEvent"]
_OtherEventOpType = Literal["TrackEndEvent", "TrackExceptionEvent", "TrackStuckEvent", "WebSocketClosedEvent"]

EventType = Literal[_TrackStartEventType, _OtherEventOpType]


class _BaseEventOp(TypedDict):
    op: Literal["event"]
    guildId: str

class TrackStartEvent(_BaseEventOp):
    type: _TrackStartEventType
    encodedTrack: str

class _OtherEventOp(_BaseEventOp):
    type: _OtherEventOpType

EventOp: TypeAlias = "TrackStartEvent | _OtherEventOp"


class PlayerState(TypedDict):
    time: int
    position: NotRequired[int]
    connected: bool
    ping: int


class PlayerUpdateOp(TypedDict):
    guildId: str
    state: PlayerState