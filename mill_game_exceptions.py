class MillGameException(Exception):
    """Raised when mill game logic does not approve an action."""


class InvalidBoardPosition(MillGameException):
    """Raised when trying to access an invalid cell or ring in the mill game
    board."""


class InvalidStateException(MillGameException):
    """Raised when the action cannot be executed because the game is in a
    invalid state."""


class InvalidMoveException(MillGameException):
    """Raised when the mill game board wants to be altered in a non conformant
    way with the rules."""


class InvalidJSONFormatException(Exception):
    """Raised when a string being encoded/decoded as JSON is not formatted
    correctly as JSON."""


class InvalidSucesorFormatException(Exception):
    """Raised when a dictionary obtained with JSON functions is not formatted
    correctly as a successor."""
