"""
"Nine men's morris" Game.

This program implements an intelligent agent which knows how to play the
"Nine men's morris" game against other players by using a randomized algorithm
and dynamic programming.

Authors:
    Lucía de Ancos Villa
    Pablo del Hoyo Abad
    Israel Mateos Aparicio Ruiz Santa Quiteria
"""

import random

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional

from board import Board, CellState

NUM_PIECES_PER_PLAYER = 9

class MillGameException(Exception):
    """ Raised when mill game logic does not approve an action """

class InvalidStateException(MillGameException):
    """ Raised when the action cannot be executed because the game is in a invalid state """

class InvalidMoveException(MillGameException):
    """ Raised when the mill game board wants to be altered in a non conformant way with the rules """

class GameMode(Enum):
    """Represents the mode in which the game is in a given moment."""
    PLACE = auto()
    MOVE = auto()

class Turn(Enum):
    """Represents the turn of the game in a given moment, that is, who is the
    active player."""
    WHITE = 0
    BLACK = 1

@dataclass
class Player:
    associated_cell_state: CellState
    remaining_pieces: int = field(default=NUM_PIECES_PER_PLAYER)
    killed_pieces: int = field(default=0)

class MillGame:
    """
    Class which contains the game logic.

    In the initial stage, each player places his/her chips alternatively, which
    is achieved with the attribute 'turn'. At any moment, if the active player
    forms a mill, that is, three chips in adjacent/connected cells, he/she is
    allowed to remove a chip placed on the board by the other player. Once all
    chips of a player are placed on the board, he/she can only move his/her
    chips to adjacent cells. The player who has two chips left on the board loses.
    """

    def __init__(self, turn: Optional[Turn] = None):
        """ turn is the turn of the one who starts the game. If None is given, it is chosen randomly """

        self.turn = turn if turn is not None else Turn(random.randint(0, 1))
        self.mode = GameMode.PLACE
        self.has_to_delete = False
        self.board = Board()

        self._players = [Player(CellState.WHITE), Player(CellState.BLACK)]

    def place(self, ring: int, cell: int):
        """Place the next chip of the active player in a cell of the board."""
        if self._check_mode(GameMode.PLACE):
            raise InvalidStateException("The game mode must be 'PLACE'")

        if self.board.get_cell(ring, cell) != CellState.EMPTY:
            raise InvalidMoveException("The cell is not empty")

        self.board.put_cell(ring, cell, self.current_player().associated_cell_state)

        # check if we have to move to the 'MOVE' state by checking the remaining pieces each player has 
        self.current_player().remaining_pieces -= 1
        if self._players[Turn.WHITE.value].remaining_pieces == 0 and self._players[Turn.BLACK.value].remaining_pieces == 0:
            self.mode = GameMode.MOVE

        if self.board.is_mill(ring, cell):
            self.has_to_delete = True
        else:
            self._change_turn()

    def move(self, ring1: int, cell1: int, ring2: int, cell2: int):
        """Move a chip of the active player placed in the board to another cell."""
        if self._check_mode(GameMode.MOVE):
            raise InvalidStateException("The game mode must be 'MOVE'")

        if not self.board.are_adjacent(ring1, cell1, ring2, cell2):
            raise InvalidMoveException("You can only move the pieces to adjacent cells")

        if self.current_player().associated_cell_state != self.board.get_cell(ring1, cell1):
            raise InvalidMoveException("You can only move your own pieces")

        if self.board.get_cell(ring2, cell2) != CellState.EMPTY:
            raise InvalidMoveException("The new position of the piece must be empty")

        self.board.remove(ring1, cell1)
        self.board.put_cell(ring2, cell2, self.current_player().associated_cell_state)

        if self.board.is_mill(ring2, cell2):
            self.has_to_delete = True
        else:
            self._change_turn()

    def remove(self, ring, cell):
        """Remove a cell from the board permanently."""
        if not self.has_to_delete:
            raise InvalidStateException("It is not required to remove a piece")

        if self.board.is_mill(ring, cell):
            raise InvalidMoveException("You cannot remove chips belonging to a mill")

        self.board.remove(ring, cell)

        self.has_to_delete = False
        self._change_turn()

    def current_player(self) -> Player:
        """ Returns the current player """

        return self._players[self.turn.value]

    def _change_turn(self):
        """ Changes the turn """

        self.turn = Turn(1 - self.turn.value)

    def _check_mode(self, mode: GameMode) -> bool:
        """ Checks whether the methods associated with a specific mode can be run """

        return self.mode == mode and not self.has_to_delete

if __name__ == "__main__":
    board = Board()
    print(board)
