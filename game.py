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
from typing import Optional

from board import Board, CellState


class GameMode(Enum):
    """Represents the mode in which the game is in a given moment."""

    PLACE = auto()
    MOVE = auto()
    DELETE = auto()


class Turn(Enum):
    """Represents the turn of the game in a given moment, that is, who is the
    active player."""

    WHITE = 1
    BLACK = 2


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
        """Create an instance of the MillGame class."""
        # turn is the turn of the one who starts the game. If None is given,
        # it is chosen randomly
        self.turn = turn if self.turn is not None else Turn(random.randint(1, 2))
        self.mode = GameMode.PLACE
        self.board = Board()

    def place(self, ring: int, cell: int) -> bool:
        """Place the next chip of the active player in a cell of the board."""
        if (
            self.mode != GameMode.PLACE
            or self.board.get_cell(ring, cell) != CellState.EMPTY
        ):
            return False

        self.board.put_cell(ring, cell, self._get_state_by_turn())

        return True

    def move(self, ring1: int, cell1: int, ring2: int, cell2: int):
        """Move a chip of the active player placed in the board to another cell."""
        if self.mode != GameMode.MOVE:
            raise ValueError("The game mode must be 'MOVE'")
        if not self.board.are_adjacent(ring1, cell1, ring2, cell2):
            raise ValueError("You can only move your chips to adjacent cells")
        if self.turn != self.board.get_cell(ring1, cell1):
            raise ValueError("You can only move your own chips")
        if self.board.get_cell(ring2, cell2) != CellState.EMPTY:
            raise ValueError("The new position of the chip must be empty")

        self.board.remove(ring1, cell1)
        self.board.put_cell(ring2, cell2, self._get_state_by_turn())

        if self.board.is_mill(ring2, cell2):
            self.mode = GameMode.DELETE

    def remove(self, ring: int, cell: int):
        """Remove a cell from the board permanently."""
        if self.mode != GameMode.DELETE:
            raise ValueError("The game mode must be 'DELETE'")
        if self.board.is_mill(ring, cell):
            raise ValueError("You cannot remove chips belonging to a mill")

        self.board.remove(ring, cell)

    def _get_state_by_turn(self) -> CellState:
        """Return the state of cells owned by the active player."""
        return CellState.BLACK if self.turn == Turn.BLACK else CellState.WHITE


class State:
    # TODO: Implement
    pass


if __name__ == "__main__":
    tablero = Board()
    print(tablero)

    # game = MillGame(turn=, )

    # game.place(ring, cell) -> bool
    # game.place(ring, cell)

    # # Si se llama a un método distinto a los que permite el modo en el que se encuentra
    # # el juego, crashe
    # game.remove(ring, cell) -> Indicar la razon del fallo

    # game.move(ring1, cell1, ring2, cell2) -> Indicar la razon del fallo

    # game.mode
