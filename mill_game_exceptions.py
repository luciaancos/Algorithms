class MillGameException(Exception):
    """ Raised when mill game logic does not approve an action """


class InvalidBoardPosition(MillGameException):
    """ Raised when trying to access an invalid cell or ring in the mill game board """


class InvalidStateException(MillGameException):
    """ Raised when the action cannot be executed because the game is in a invalid state """


class InvalidMoveException(MillGameException):
    """ Raised when the mill game board wants to be altered in a non conformant way with the rules """
