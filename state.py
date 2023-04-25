from __future__ import annotations

import copy
import random

from typing import TYPE_CHECKING, Optional
from collections.abc import Iterator
from game import (
    GameMode,
    MillGame,
    Move,
)
from mill_game_exceptions import MillGameException

if TYPE_CHECKING:
    from game import GameInfo, Turn


class State:
    def __init__(
        self,
        game: MillGame,
        move: Optional[Move] = None,
        parent: Optional[State] = None,
    ):
        self.game = game
        self.move = move
        self.parent = parent
        self.game_info = self.game.get_current_game_info()

        self.free_pieces = self.game_info.free_pieces[:]

        self.players = [self.game_info.white_player_pieces[:], self.game_info.black_player_pieces[:]]

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
                    # TODO: it is posssible not to make an useless copy if we separate the check
                    # and the action

                    remove_copy = copy.deepcopy(game_copy)
                    try:
                        remove_copy.remove(*op_pos)
                    except MillGameException:
                        continue
                    move = Move(pos_init=None, next_pos=free_pos, kill=op_pos)

                    yield State(remove_copy, move, self)
            else:
                move = Move(pos_init=None, next_pos=free_pos, kill=None)
                yield State(game_copy, move, self)

    def _generate_move_sucessors(self) -> Iterator[State]:
        oponent_turn = 1 - self.game.turn.value

        for init_pos in self.players[self.game.turn.value]:
            for free_pos in self.free_pieces:
                # This check avoids making an useless copy of MillGame when
                # init_pos is not adjacent to free_pos
                if not self.game.board.are_adjacent(*init_pos, *free_pos):
                    continue

                # TODO: it is posssible not to make an useless copy if we separate the check
                # and the action
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
                        move = Move(pos_init=init_pos, next_pos=free_pos, kill=op_pos)
                        yield State(remove_copy, move, self)
                else:
                    move = Move(pos_init=init_pos, next_pos=free_pos, kill=None)
                    yield State(game_copy, move, self)

    def successors(self, *, shuffle=False) -> Iterator[State]:
        """Returns a generator with all the successors states of the current
        one.

        If shuffle is True, the generator will generate the states in a
        random order.
        """

        # TODO: right now, the order is not uniformly random. If the consumed
        # state has been reached using a kill move then the next one will also
        # be reached using the same kind of move if it exists. This will
        # continue until all the kill moves have been consumed

        if shuffle:
            self._shuffle_indices()

        if self.game.mode == GameMode.PLACE:
            yield from self._generate_place_sucessors()
        elif self.game.mode == GameMode.MOVE:
            yield from self._generate_move_sucessors()

    def _shuffle_indices(self):
        white_pieces, black_pieces = self.players

        random.shuffle(self.free_pieces)
        random.shuffle(white_pieces)
        random.shuffle(black_pieces)

    def __eq__(self, obj: object) -> bool:
        if not isinstance(obj, State):
            return False

        return obj.__key == self.__key

    def __hash__(self) -> int:
        return hash(self.__key)

    def __str__(self):
        joined_free = ",".join(
            map(str, [ring * 8 + cell for ring, cell in self.free_pieces])
        )
        joined_players = ",".join(
            map(
                str,
                [[ring * 8 + cell for ring, cell in player] for player in self.players],
            )
        )
        return (
            f"<state>={{'FREE':[{joined_free}],'GAMER':[{joined_players}],"
            f"'TURN':{self.game.turn.name.lower()},"
            f"'CHIPS':[{self.game.players[0].remaining_pieces}, "
            f"{self.game.players[1].remaining_pieces}]}}"
        )

    def __key(self) -> tuple[GameInfo, Turn]:
        return (self.game_info, self.game.turn)
