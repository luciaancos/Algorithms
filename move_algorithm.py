from abc import ABC, abstractmethod
import copy
from typing import TYPE_CHECKING, Optional
import random

from state import State
from montecarlo_node import MontecarloNode
from game import GameMode

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


class MonteCarloMove(MoveAlgorithm):
    """ This algorithm chooses a move according to the monte carlo algorithm """
    def __init__(self, credits: int) -> None:
        self.montecarlo_tree = None
        self.credits = credits

    def next_move(self, game: MillGame) -> Optional[Move]:
        self.montecarlo_tree = MonteCarloTree(game)
        remaining_credits = self.credits
        while remaining_credits != 0:
            self.montecarlo_tree.run_iteration()
            remaining_credits -=1 
        return self.montecarlo_tree.best_state().action 
        

class MonteCarloTree:

    def __init__(self, game:MillGame) -> None:
        state = State(game)
        self.root = MontecarloNode(state)
        self.current_turn = self.root.state.game.turn

    def best_state(self):
        return self.root.get_best_child().state

    def run_iteration(self):
        selected_node = self.tree_policy()
        reward = self.default_policy(selected_node)
        self.backup(selected_node,reward)


    def tree_policy(self):
        current_node = self.root
        while not current_node.is_terminal():
            if (next_child:= current_node.next_child()) is not None: 
                return next_child
            else:
                node = node.get_best_child()
            
    def default_policy(self, node:MontecarloNode):
        game = copy.deepcopy(node.state.game)
        move = RandomMove()
        while game.mode != GameMode.FINISHED:
            move.perform_move(game)

        if game.winner is None:
            return 0
        elif game.winner== self.current_turn:
            return 1
        else:
            return -1
    
    def backup(self, node:MontecarloNode, reward: int):
        while node is not None:
            node.visits+=1
            node.accumulated_reward+= reward
            reward = -reward
            node = node.parent

