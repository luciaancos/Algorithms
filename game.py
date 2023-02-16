import random

from enum import Enum, auto
from typing import Optional

CELLS_PER_RING = 8
RINGS = 3
BOARD_SIZE = CELLS_PER_RING * RINGS


class CellState(Enum):
    WHITE = auto()
    BLACK = auto()
    EMPTY = auto()

    def print_state(self) -> str:
        match self:
            case CellState.EMPTY:
                return 'O'
            case CellState.BLACK:
                return 'B'
            case _:
                return 'W'

class Board:
    """ It represents the standard board for the "Nine men's morris" game. It contains
    three rings, each composed of eight cells. The outer ring is identified with the number 0 and
    the most inner one, with 2. For the cells, the one at the upper left corner is identified
    with the number 0. The identifier of the next cells increases by one in clockwise motion, so 
    the cell to the right of cell zero is one and so on until the last one, which is seven. 
    """

    def __init__(self, buff: Optional[list[CellState]]=None):
        """ buff is a 24 sized list which represents the board. If None is given, an empty board will be generated"""

        self.buff = buff if buff is not None else [CellState.EMPTY] * BOARD_SIZE

        if len(self.buff) > BOARD_SIZE:
            raise ValueError(
                f"'buff' must have a length of 24, but it has {len(self.buff)}")

    def get_cell(self, ring: int, cell: int) -> CellState:
        """ Returns the state of a cell located in a specific ring """

        idx = self._get_cell_idx(ring, cell)
        return self.buff[idx]

    def put_cell(self, ring: int, cell: int, state: CellState):
        """ Change the state of a cell located in a specific ring. The value of the cell 
        is completely overriden"""

        idx = self._get_cell_idx(ring, cell)
        self.buff[idx] = state

    def remove(self, ring: int, cell: int):
        """ Equivalent to put_cell(ring, cell, CellState.EMPTY) """

        self.put_cell(ring, cell, CellState.EMPTY)

    def is_intersection(self, ring: int, cell: int) -> bool:
        """ Returns whether the cell in a specific has a connection with an inner or outer ring """

        return cell % 2 == 1

    def are_adjacent(self, ring1, cell1, ring2, cell2) -> bool:
        """ Returns true iff the two positions are adjacent """

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
        """ Returns true if the piece at (ring, cell) is part of a mill """

        current_state = self.get_cell(ring, cell)

        # If the given cell is empty, it cannot be part of a mill
        if current_state == CellState.EMPTY:
            return False


        if self.is_intersection(ring, cell):
            # if it is not one of the corners, the mill can be created with other pieces in the same ring 
            if self._check_same_in_ring(current_state, ring, cell - 1):
                return True

            # or with pieces in the other rings which are connected to it
            if self._check_across_rings(current_state, cell):
                return True

        elif self._check_same_in_ring(current_state, ring, cell) or \
                self._check_same_in_ring(current_state, ring, cell + 6):
            # if it is a corner, we have to check for two possible mills
            return True
        
        return False

    def _check_same_in_ring(self, check_state: CellState, ring, cell) -> bool:
        """ Checks whether there is a mill starting at a corner. It is checked in clockwise motion 
        NOTE: this method does NOT check whether the cell is a corner """

        for i in range(3):
            if check_state != self.get_cell(ring, (cell + i) % CELLS_PER_RING):
                return False

        return True

    def _check_across_rings(self, check_state, cell) -> bool:
        """ Checks whether there is a mill across ring which contains cell.
        NOTE: this method does NOT check whether a cell is in a intersection"""

        for ring in range(RINGS):
            if check_state != self.get_cell(ring, cell):
                return False

        return True


    def _get_cell_idx(self, ring: int, cell: int):
        if ring < 0 or ring >= RINGS:
            raise ValueError(
                f"The ring must be between 0 and {RINGS}, but {ring} was given")

        if cell < 0 or cell >= CELLS_PER_RING:
            raise ValueError(
                f"The cell must be between 0 and {CELLS_PER_RING}, but {cell} was given")

        return ring * CELLS_PER_RING + cell


    def __str__(self):
        table = (self.buff[0].print_state() + '----------------' +
        self.buff[1].print_state() + '----------------' +
        self.buff[2].print_state() + '\n')
        table += ('|                |                |\n') 
        table += ('|                |                |\n')
        table += ('|      ' + self.buff[8].print_state() + 
        '---------' + self.buff[9].print_state() + '---------' +
        self.buff[10].print_state() + '      |\n') 
        table += ('|      |         |         |      |\n')
        table += ('|      |         |         |      |\n')
        table += ('|      |    ' + self.buff[16].print_state() + 
        '----' + self.buff[17].print_state() + '----' +
        self.buff[18].print_state() + '    |      |\n')
        table += ('|      |    |         |    |      |\n')
        table += (self.buff[7].print_state() + '      ' +
        self.buff[15].print_state() + '    ' + self.buff[23].print_state() +
        '         ' + self.buff[19].print_state() +
        '    ' + self.buff[11].print_state() + '      ' +
        self.buff[3].print_state() + '\n')
        table+= ('|      |    |         |    |      |\n')
        table += ('|      |    ' + self.buff[22].print_state() + '----' +
        self.buff[21].print_state() + '----' +
        self.buff[20].print_state() + '    |      |\n') 
        table+= ('|      |         |         |      |\n')
        table+= ('|      |         |         |      |\n')
        table += ('|      ' + self.buff[14].print_state() + '---------' +
        self.buff[13].print_state() + '---------' +
        self.buff[12].print_state() + '      |\n')
        table += ('|                |                |\n') 
        table += ('|                |                |\n') 
        table += (self.buff[6].print_state() + '----------------' +
        self.buff[5].print_state() + '----------------' +
        self.buff[4].print_state() + '\n')

        return table

class GameMode(Enum):
    PLACE = auto()
    MOVE = auto()
    DELETE = auto()

class Turn(Enum):
    WHITE = 1
    BLACK = 2

class MillGame:
    """ This class encodes the game logic """
    
    def __init__(self, turn: Optional[Turn]=None):
        """ turn is the one who starts. If None is given, it is chosen randomly """

        self.turn = turn if self.turn is not None else Turn(random.randint(1, 2))
        self.mode = GameMode.PLACE
        self.board = Board()

    def place(self, ring: int, cell: int) -> bool:
        if self.mode != GameMode.PLACE or self.board.get_cell(ring, cell) != CellState.EMPTY:
            return False

        self.board.put_cell(ring, cell, self._get_state_by_turn())

        return True

    def _get_state_by_turn(self) -> CellState:
        return CellState.BLACK if self.turn == Turn.BLACK else CellState.WHITE


class State:
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
