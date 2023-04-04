from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional
import random
from game import GameMode, Turn

from state import State

if TYPE_CHECKING:
    from game import Move, MillGame


# TODO: think on a better way to organize this using modules and packages
class MoveAlgorithm(ABC):
    """ Base class for the algorithms which perform a specific move on a MillGame """

    def perform_move(self, game: MillGame) -> Optional[Move]:
        """ Perform a specific move on 'game'. The state of game is modified and the applied move is returned. If
        no action could be performed because the game is won, return None """

        state = self._next_state(game)
        if state is None:
            return None

        new_game = state.game
        # This works as long as dunder methods such as __getitem__
        # or __setitem__ are not used
        # https://stackoverflow.com/questions/243836/how-to-copy-all-properties-of-an-object-to-another-object-in-python
        game.__dict__ = new_game.__dict__
        return state.move

    def next_move(self, game: MillGame) -> Optional[Move]:
        """ Get the move which the algorithm considers for the given 'game'. If no action can
        be performed because the game is won, return None.

        This will not update game. If you want to update the game AND get the move, you should use self.perform_move()
        instead of applying the returned Move to the game because it is slightly faster. """

        state = self._next_state(game)
        if state is None:
            return None

        return state.move

    @abstractmethod
    def _next_state(self, game: MillGame) -> Optional[State]:
        """ Returns the next state of the game chosen by this algorithm. If there are no available state,
        then return None

        This method is not meant to be called directly. This is what should be overriden 
        by every subclass of MoveAlgorithm """


class RandomMove(MoveAlgorithm):
    """ This algorithm chooses a move uniformly at random from the set of available ones """

    def _next_state(self, game: MillGame) -> Optional[State]:
        """ Returns the next state of the game chosen by this algorithm """

        if game.mode == GameMode.FINISHED:
            return None

        # A StopIterationError won't be thrown because that only happens when the game state
        return next(State(game).successors(shuffle=True))

class MinimaxMove(MoveAlgorithm):
    """ This algorithm chooses a move according to the minimax algorithm with alpha-beta pruning """

    def _evaluate(self, game: MillGame, current_turn: Turn) -> int:
        """ Evaluates the value of the state of a given game for the current player """
        if game.mode == GameMode.FINISHED:
            winner = game.winner
            if winner is not None:
                # The game is finished when one of the players has 2 chips left,
                # so the maximum difference of 7 pieces will be used for won/lost
                # plays
                if winner == current_turn:
                    return 7
                else:
                    return -7
            else:
                return 0
        else:
            # Get index of game.players for the current player and the opponent
            current_player_idx  = next(i for i, player in enumerate(game.players) if player.associated_cell_state.name == current_turn.name)
            opponent_idx = current_player_idx ^ 1
            # Use the difference in the number of remaining pieces as heuristic
            return game.players[current_player_idx].remaining_pieces - game.players[opponent_idx].remaining_pieces


    def _max_value(self, game: MillGame, current_turn: Turn, alpha: int, beta: int, depth: int) -> int:
        """ Computes the value of a state for the player that is maximizing """
        if depth == 0 or game.mode == GameMode.FINISHED:
            return self._evaluate(game, current_turn)

        value = float('-inf')
        for successor in State(game).successors():
            value = max(value, self._min_value(successor.game, current_turn, alpha, beta, depth - 1))
            alpha = max(alpha, value)
            if alpha >= beta:
                break

        return value

    def _min_value(self, game: MillGame, current_turn: Turn, alpha: int, beta: int, depth: int) -> int:
        """ Computes the value of a state for the player that is minimizing """
        if depth == 0 or game.mode == GameMode.FINISHED:
            return self._evaluate(game, current_turn)

        value = float('inf')
        for successor in State(game).successors():
            value = min(value, self._max_value(successor.game, current_turn, alpha, beta, depth - 1))
            beta = min(beta, value)
            if alpha >= beta:
                break

        return value

    def _next_state(self, game: MillGame) -> Optional[State]:
        """ Returns the next state of the game chosen by this algorithm """
        if game.mode == GameMode.FINISHED:
            return None

        best_value = float('-inf')
        best_state = None
        current_turn = game.turn
        # TODO: Use the maximum depth as a parameter to choose the agent's complexity
        for successor in State(game).successors():
            value = self._min_value(successor.game, current_turn, float('-inf'), float('inf'), depth=4)
            if value > best_value:
                best_value = value
                best_state = successor

        return best_state
