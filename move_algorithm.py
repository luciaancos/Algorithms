
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from game import Move, MillGame

class MoveAlgorithm(ABC):
    """ Base class for the algorithms which perform a specific move on a MillGame """

    @abstractmethod
    def perform_move(self, game: MillGame) -> Optional[Move]:
        """ Perform a specific move on 'game'. The state of game is modified and the applied move is returned. If
        no action could be performed because the game is won, return None """
        pass

class RandomMove(MoveAlgorithm):
    """ This algorithm chooses a move uniformly at random from the set of available ones """

    def perform_move(self, game: MillGame) -> Optional[Move]:
        raise NotImplementedError

class MinimaxMove(MoveAlgorithm):
    """ This algorithm chooses a move according to the minimax algorithm """

    def perform_move(self, game: MillGame) -> Optional[Move]:
        raise NotImplementedError
