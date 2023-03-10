from __future__ import annotations

import copy

from typing import Optional
from game import (
    GameMode,
    MillGame,
    Move,
)
from mill_game_exceptions import MillGameException
from board import ALL_BOARD_POSITIONS, CellState
from collections.abc import Iterator


class State:

    def __init__(self,
                 game: MillGame,
                 move: Optional[Move] = None,
                 parent: Optional[State] = None):

        self.game = game
        self.move = move
        self.parent = parent

        self.free_pieces = [(ring, cell) for ring, cell in ALL_BOARD_POSITIONS
                            if game.board.get_cell(ring, cell) == CellState.EMPTY]

        white_player_pieces = [(ring, cell) for ring, cell in ALL_BOARD_POSITIONS
                               if game.board.get_cell(ring, cell) == CellState.WHITE]
        black_player_pieces = [(ring, cell) for ring, cell in ALL_BOARD_POSITIONS
                               if game.board.get_cell(ring, cell) == CellState.BLACK]

        self.players = [white_player_pieces, black_player_pieces]

    def _generate_place_sucessors(self) -> Iterator[State]:
        oponent_turn = 1 - self.game.turn.value

        for free_pos in self.free_pieces:
            game_copy = copy.deepcopy(self.game)
            try:
                game_copy.place(*free_pos)
            except MillGameException:
                continue

            if game_copy.has_to_delete:
                for op_pos in self.players[oponent_turn]:
                    remove_copy = copy.deepcopy(game_copy)
                    try:
                        remove_copy.remove(*op_pos)
                    except MillGameException:
                        continue
                    move = Move(pos_init=None,
                                next_pos=free_pos,
                                kill=op_pos
                            )

                    yield State(remove_copy, move, self)
            else:
                move = Move(pos_init=None,
                            next_pos=free_pos,
                            kill=None)
                yield State(game_copy, move, self)

    def _generate_move_sucessors(self) -> Iterator[State]:
        oponent_turn = 1 - self.game.turn.value

        for init_pos in self.players[self.game.turn.value]:
            for free_pos in self.free_pieces:
                # This check avoid making an useless copy of MillGame when init_pos is not adjacent to
                # free_pos
                if not self.game.board.are_adjacent(*init_pos, *free_pos):
                    continue

                game_copy = copy.deepcopy(self.game)
                try:
                    game_copy.move(*init_pos, *free_pos)
                except MillGameException:
                    continue

                if game_copy.has_to_delete:
                    for op_pos in self.players[oponent_turn]:
                        remove_copy = copy.deepcopy(game_copy)
                        try:
                            remove_copy.remove(*op_pos)
                        except MillGameException:
                            continue
                        move = Move(pos_init=init_pos,
                                    next_pos=free_pos,
                                    kill=op_pos)
                        yield State(remove_copy, move, self)
                else:
                    move = Move(pos_init=init_pos,
                                next_pos=free_pos,
                                kill=None)
                    yield State(game_copy, move, self)

    def successors(self) -> Iterator[State]:
        """ Returns a generator with all the successors states of the current one """ 

        if self.game.mode == GameMode.PLACE:
            yield from self._generate_place_sucessors()
        elif self.game.mode == GameMode.MOVE:
            yield from self._generate_move_sucessors()

    def __str__(self):
        joined_free = ",".join(map(str, [ring * 8 + cell for ring, cell in self.free_pieces]))
        joined_players = ",".join(map(str, [[ring * 8 + cell for ring, cell in player] for player in self.players]))
        return (f"<state>={{'FREE':[{joined_free}],'GAMER':[{joined_players}],'TURN':{self.game.turn.name.lower()},"
                f"'CHIPS':[{self.game.players[0].remaining_pieces}, {self.game.players[1].remaining_pieces}]}}")

