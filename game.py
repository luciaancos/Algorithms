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

from board import CELLS_PER_RING, RINGS, Board, CellState
from state import Move

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
    FINISHED = auto()


class Turn(Enum):
    """Represents the turn of the game in a given moment, that is, who is the
    active player."""
    WHITE = 0
    BLACK = 1


@dataclass
class Player:
    associated_cell_state: CellState
    remaining_pieces: int = field(default=NUM_PIECES_PER_PLAYER)
    alive_pieces: int = field(default=NUM_PIECES_PER_PLAYER)


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
        if not self._check_mode(GameMode.PLACE):
            raise InvalidStateException("The game mode must be 'PLACE'")

        if self.board.get_cell(ring, cell) != CellState.EMPTY:
            raise InvalidMoveException("The cell is not empty")

        self.board.put_cell(
            ring, cell, self.current_player().associated_cell_state)

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
        if not self._check_mode(GameMode.MOVE):
            raise InvalidStateException("The game mode must be 'MOVE'")

        if not self.board.are_adjacent(ring1, cell1, ring2, cell2):
            raise InvalidMoveException(
                "You can only move the pieces to adjacent cells")

        if self.current_player().associated_cell_state != self.board.get_cell(ring1, cell1):
            raise InvalidMoveException("You can only move your own pieces")

        if self.board.get_cell(ring2, cell2) != CellState.EMPTY:
            raise InvalidMoveException(
                "The new position of the piece must be empty")

        self.board.remove(ring1, cell1)
        self.board.put_cell(
            ring2, cell2, self.current_player().associated_cell_state)

        if self.board.is_mill(ring2, cell2):
            self.has_to_delete = True
        else:
            self._change_turn()

    def remove(self, ring, cell):
        """Remove a cell from the board permanently."""
        if not self.has_to_delete:
            raise InvalidStateException("It is not required to remove a piece")

        if self.board.get_cell(ring, cell) == CellState.EMPTY:
            raise InvalidMoveException(
                "It is not possible to remove and empty cell")

        if self.board.get_cell(ring, cell) != self.other_player().associated_cell_state:
            raise InvalidMoveException(
                "You cannot remove chips which belong to the current player")

        if self.board.is_mill(ring, cell) and not self.all_pieces_form_mill(self.other_player()):
            raise InvalidMoveException(
                "You cannot remove chips belonging to a mill when there are chips which don't belong to any of them")

        self.board.remove(ring, cell)
        self.other_player().alive_pieces -= 1

        if self.other_player().alive_pieces <= 2:
            self.mode = GameMode.FINISHED
        else:
            self._change_turn()

        self.has_to_delete = False

    def other_player(self) -> Player:
        """ Return the player who is not the current player """

        return self._players[1 - self.turn.value]

    def current_player(self) -> Player:
        """ Returns the current player """

        return self._players[self.turn.value]

    def all_pieces_form_mill(self, player: Player) -> bool:
        """ Returns whether a player has all their pieces being part of at least one mill """

        # check corners
        for ring in range(1, RINGS):
            if self.board.get_cell(ring, 0) == player.associated_cell_state and not self.board.is_mill(ring, 0):
                return False

            if self.board.get_cell(ring, 4) == player.associated_cell_state and not self.board.is_mill(ring, 4):
                return False

        # check mill across rings
        for cell in range(1, 8, 2):
            if (self.board.get_cell(0, cell) == player.associated_cell_state and
                    not self.board.is_mill(0, cell)):
                return False

        return True

    def can_move_to_any_adjacent_cell(self, player: Player) -> bool:
        """ Checks whether there exist one piece from 'player' which can be moved to an adjacent cell """

        # TODO: this can be improved if we don't have traverse the board in order to find 'player's pieces.
        # That information could be stored on an array. The disadvantage is that we must be careful on keeping
        # the array in sync with the board

        for ring in range(RINGS):
            for cell in range(CELLS_PER_RING):
                if self.board.get_cell(ring, cell) == player.associated_cell_state and self.board.is_any_adjacent_cell_empty(ring, cell):
                    return True

        return False
    
    def is_valid_play(self, sucesor_dict: dict) -> bool:
        """Check if a given dictionary representing a successor received from
        another player is a valid play."""
        # Check if the initial state corresponds to our game's board state
        state = sucesor_dict[0]
        if not self._is_correct_state(state):
            # TODO: raise exception for a not corresponding state?
            pass

        move = Move(
            sucesor_dict[1]["INIT_POS"], sucesor_dict[1]["NEXT_POS"],
            sucesor_dict[1]["KILL"]
            )

        ring_dest, cell_dest = divmod(move.next_pos, 8)

        # If the player wants to place a free chip
        if move.pos_init == -1:
            try:
                self.place(ring_dest, cell_dest)
            except InvalidStateException as ex:
                print(ex)
                return False
            except InvalidMoveException as ex:
                print(ex)
                return False
        else:
            ring_init, cell_init = divmod(move.pos_init, 8)
            # If the player wants to move a chip placed on the board
            try:
                self.move(ring_init, cell_init, ring_dest, cell_dest)
            except InvalidStateException as ex:
                print(ex)
                return False
            except InvalidMoveException as ex:
                print(ex)
                return False
            # If the player wants to also remove one of our chips
            if move.kill != -1:
                ring_kill, cell_kill = divmod(move.kill, 8)
                try:
                    self.remove(ring_kill, cell_kill)
                except InvalidStateException as ex:
                    print(ex)
                    return False
                except InvalidMoveException as ex:
                    print(ex)
                    return False
        
        # Check if the next state provided by the other player corresponds to
        # our game's new board state after the move
        next_state = sucesor_dict[2]
        if not self._is_correct_state(next_state):
            # TODO: raise exception for a not corresponding state?
            pass

        return True

    
    def _is_correct_state(self, state_dict: dict) -> bool:
        """Check if a given dictionary representing a state received from
        another player corresponds the game's board current state."""
        state_buff = [CellState.EMPTY] * 24
        white_placed_chips = state_dict["GAMER"][0]
        black_placed_chips = state_dict["GAMER"][1]
        
        for pos in state_dict["FREE"]:
            if self.board.buff[pos] != CellState.EMPTY:
                return False

        for chip in white_placed_chips:
            state_buff[chip] = CellState.WHITE
        for chip in black_placed_chips:
            state_buff[chip] = CellState.BLACK
        
        if (
            state_buff != self.board.buff
            or self.turn != state_dict["TURN"]
            or self._players[0].remaining_pieces != state_dict["CHIPS"][0]
            or self._players[1].remaining_pieces != state_dict["CHIPS"][1]
            ):
            return False
        return True


    def _change_turn(self):
        """ Changes the turn """

        # every time a piece in the board is removed or moved it is possible that
        # the configuration is such that the other player cannot move to any adjacent cell.
        # In that case, game is lost

        if self.mode == GameMode.MOVE and not self.can_move_to_any_adjacent_cell(self.other_player()):
            self.mode = GameMode.FINISHED
        else:
            self.turn = Turn(1 - self.turn.value)

    def _check_mode(self, mode: GameMode) -> bool:
        """ Checks whether the methods associated with a specific mode can be run """

        return self.mode == mode and not self.has_to_delete


if __name__ == "__main__":
    board = Board()
    print(board)
