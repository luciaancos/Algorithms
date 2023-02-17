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

CELLS_PER_RING = 8
RINGS = 3
BOARD_SIZE = CELLS_PER_RING * RINGS


class CellState(Enum):
    """Represents the state of a board cell, which can either have a cell from
    some player or be empty."""

    WHITE = auto()
    BLACK = auto()
    EMPTY = auto()

    def __str__(self) -> str:
        """Return the string representation of the cell state."""
        match self:
            case CellState.EMPTY:
                return "O"
            case CellState.BLACK:
                return "B"
        return "W"


class Board:
    """
    Represents the standard board for the "Nine men's morris" game.

    It contains three rings, each composed of eight cells. The outer ring is
    identified with the number 0 and the most inner one, with 2. For the cells,
    the one at the upper left corner is identified with the number 0. The
    identifier of the next cells increases by one in clockwise motion, so the
    cell to the right of cell zero is one and so on until the last one, which
    is seven.
    """

    def __init__(self, buff: Optional[list[CellState]] = None):
        """Create an instance of the Board class."""
        # buff is a 24 sized list which represents the board. If None is given,
        # an empty board will be generated
        self.buff = buff if buff is not None else [CellState.EMPTY] * BOARD_SIZE

        if len(self.buff) > BOARD_SIZE:
            raise ValueError(
                f"'buff' must have a length of 24, but it has {len(self.buff)}"
            )

    def get_cell(self, ring: int, cell: int) -> CellState:
        """Return the state of a cell located in a specific ring."""
        idx = self._get_cell_idx(ring, cell)
        return self.buff[idx]

    def put_cell(self, ring: int, cell: int, state: CellState):
        """Change the state of a cell located in a specific ring. The value of
        the cell is completely overriden."""
        idx = self._get_cell_idx(ring, cell)
        self.buff[idx] = state

    def remove(self, ring: int, cell: int):
        """Equivalent to put_cell(ring, cell, CellState.EMPTY)."""
        self.put_cell(ring, cell, CellState.EMPTY)

    def is_intersection(self, ring: int, cell: int) -> bool:
        """Return whether the cell in a specific has a connection with an
        inner or outer ring."""
        return cell % 2 == 1

    def are_adjacent(self, ring1: int, cell1: int, ring2: int, cell2: int) -> bool:
        """Return true iff the two positions are adjacent."""
        cell_adjacent = abs(cell1 - cell2) in (1, 7)

        # if both rings are the same, we only have to focus on the cell
        if ring1 == ring2 and cell_adjacent:
            return True

        ring_adjacent = abs(ring1 - ring2) == 1

        # but if two cells are equal, we have to focus on the rings
        if cell1 == cell2 and ring_adjacent:
            return True

        return False

    def is_mill(self, ring: int, cell: int) -> bool:
        """Return true if the piece at (ring, cell) is part of a mill."""
        current_state = self.get_cell(ring, cell)

        # If the given cell is empty, it cannot be part of a mill
        if current_state == CellState.EMPTY:
            return False

        if self.is_intersection(ring, cell):
            # If it is not one of the corners, the mill can be created with other
            # pieces in the same ring
            if self._check_same_in_ring(current_state, ring, cell - 1):
                return True

            # Or with pieces in the other rings which are connected to it
            if self._check_across_rings(current_state, cell):
                return True

        elif self._check_same_in_ring(
            current_state, ring, cell
        ) or self._check_same_in_ring(current_state, ring, cell + 6):
            # If it is a corner, we have to check for two possible mills
            return True

        return False

    def _check_same_in_ring(self, check_state: CellState, ring: int, cell: int) -> bool:
        """Check whether there is a mill starting at a corner. It is checked
        in clockwise motion.
        NOTE: This method does NOT check whether the cell is a corner."""
        for i in range(3):
            if check_state != self.get_cell(ring, (cell + i) % CELLS_PER_RING):
                return False

        return True

    def _check_across_rings(self, check_state: CellState, cell: int) -> bool:
        """Check whether there is a mill across ring which contains cell.
        NOTE: This method does NOT check whether a cell is in a intersection."""
        for ring in range(RINGS):
            if check_state != self.get_cell(ring, cell):
                return False

        return True

    def _get_cell_idx(self, ring: int, cell: int) -> int:
        """Return the index in the board from a given cell."""
        if ring < 0 or ring >= RINGS:
            raise ValueError(
                f"The ring must be between 0 and {RINGS}, but {ring} was given"
            )

        if cell < 0 or cell >= CELLS_PER_RING:
            raise ValueError(
                f"The cell must be between 0 and {CELLS_PER_RING}, but {cell} was given"
            )

        return ring * CELLS_PER_RING + cell

    def __str__(self) -> str:
        """Return the string representation of the board."""
        table = f"{self.buff[0]}----------------"
        table += f"{self.buff[1]}----------------"
        table += f"{self.buff[2]}\n"

        table += "|                |                |\n"
        table += "|                |                |\n"

        table += f"|      {self.buff[8]}"
        table += f"---------{self.buff[9]}---------"
        table += f"{self.buff[11]}      |\n"

        table += "|      |         |         |      |\n"
        table += "|      |         |         |      |\n"

        table += f"|      |    {self.buff[16]}----{self.buff[17]}----{self.buff[18]}    |      |\n"

        table += "|      |    |         |    |      |\n"

        table += f"{self.buff[7]}      "
        table += f"{self.buff[15]}    {self.buff[23]}"
        table += f"         {self.buff[19]}"
        table += f"    {self.buff[11]}      "
        table += f"{self.buff[3]}\n"

        table += "|      |    |         |    |      |\n"
        table += f"|      |    {self.buff[22]}----{self.buff[21]}----{self.buff[20]}    |      |\n"

        table += "|      |         |         |      |\n"
        table += "|      |         |         |      |\n"

        table += f"|      {self.buff[14]}"
        table += f"---------{self.buff[13]}---------"
        table += f"{self.buff[12]}      |\n"

        table += "|                |                |\n"
        table += "|                |                |\n"

        table += f"{self.buff[6]}----------------"
        table += f"{self.buff[5]}----------------"
        table += f"{self.buff[4]}"

        return table


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
