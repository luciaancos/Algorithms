from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional
import random
from game import GameMode

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
    """ This algorithm chooses a move according to the minimax algorithm """

    def _next_state(self, game: MillGame):
        pass
