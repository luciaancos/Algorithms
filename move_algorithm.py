from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional
import random

from state import State

if TYPE_CHECKING:
    from game import Move, MillGame

class MoveAlgorithm(ABC):
    """ Base class for the algorithms which perform a specific move on a MillGame """

    @abstractmethod
    def perform_move(self, game: MillGame) -> Optional[Move]:
        """ Perform a specific move on 'game'. The state of game is modified and the applied move is returned. If
        no action could be performed because the game is won, return None """

    @abstractmethod
    def next_move(self, game: MillGame) -> Optional[Move]:
        """ Get the move which the algorithm considers for the given 'game'. If no action can
        be performed because the game is won, return None.

        This will not update game. If you want to update the game AND get the move, you should use self.perform_move()
        instead of applying the returned Move to the game because it is instead slightly faster. """


class RandomMove(MoveAlgorithm):
    """ This algorithm chooses a move uniformly at random from the set of available ones """

    def perform_move(self, game: MillGame) -> Optional[Move]:
        state = self._next_state(game)
        if state is None:
            return None

        new_game = state.game
        # Update all the attributes
        game.__dict__ = new_game.__dict__
        return state.move

    def next_move(self, game: MillGame) -> Optional[Move]:
        state = self._next_state(game)
        if state is None:
            return None
        return state.move

    def _next_state(self, game: MillGame) -> Optional[State]:
        """ Returns the next state of the game chosen by this algorithm """

        state = State(game)
        sucessors = list(state.successors())
        if not sucessors:
            return None

        return random.choice(sucessors)

class MinimaxMove(MoveAlgorithm):
    """ This algorithm chooses a move according to the minimax algorithm """

    def perform_move(self, game: MillGame) -> Optional[Move]:
        raise NotImplementedError

    def next_move(self, game: MillGame) -> Optional[Move]:
        raise NotImplementedError
