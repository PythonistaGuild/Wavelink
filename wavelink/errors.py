class WavelinkException(Exception):
    """Base Wavelink Exception."""


class NodeOccupied(WavelinkException):
    """Exception raised when node identifiers conflict."""


class InvalidIDProvided(WavelinkException):
    """Exception raised when an invalid ID is passed somewhere in Wavelink."""


class ZeroConnectedNodes(WavelinkException):
    """Exception raised when an operation is attempted with nodes, when there are None connected."""


class AuthorizationFailure(WavelinkException):
    """Exception raised when an invalid password is provided toa node."""
