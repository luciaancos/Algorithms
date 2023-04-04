from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional
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

    def __init__(self, max_depth: int):
        self.max_depth = max_depth

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
        for successor in State(game).successors():
            value = self._min_value(successor.game, current_turn, float('-inf'), float('inf'), self.max_depth)
            if value > best_value:
                best_value = value
                best_state = successor

        return best_state

@dataclass
class MontecarloNode:
    state: State
    parent: Optional[MontecarloNode] = None
    visits: int = 0
    accumulated_rewards: int = 0
    expanded_children: list[MontecarloNode] = field(
        default_factory=list, init=False)

    def __post_init__(self):
        self._sucessors = self.state.successors(shuffle=True)

    def next_child(self) -> Optional[MontecarloNode]:
        """ Add a child to this node and return it. If this node is fully expanded, return None """

        try:
            new_state = next(self._sucessors)
            child = MontecarloNode(new_state, self)
            self.expanded_children.append(child)
            return child
        except StopIteration:
            return None

    def avg_reward(self) -> float:
        """ Returns the average reward for this node """

        if self.visits == 0:
            raise ValueError("You cannot access the average reward for a node which has not been in a simulation")

        return self.accumulated_rewards / self.visits

    def uct_value(self) -> float:
        """ Returns the uct value for the this node. If this node is the root, an exception is
        raised """

        if self.parent is None:
            raise ValueError("You can not get the evaluation of the root")

        # TODO: this constant should be given as a parameter
        cp = 1 / 2 ** 0.5
        bound = 2 * cp * (2 * math.log(self.parent.visits) / self.visits) ** 0.5
        return self.avg_reward() + bound

    def get_best_child(self) -> MontecarloNode:
        """ Returns the child node with the highest uct value """

        return max([child for child in self.expanded_children], key=MontecarloNode.uct_value)

    def is_terminal(self) -> bool:
        """ Returns true if this is a terminal state. A terminal state is one which does not have
        any children because it wraps a game which is finished """

        return self.state.game.mode == GameMode.FINISHED


class MonteCarloTree:

    def __init__(self, game: MillGame) -> None:
        state = State(game)
        self.root = MontecarloNode(state)
        self.current_turn = self.root.state.game.turn

    def best_node(self) -> MontecarloNode:
        """ Returns the node with the highest average reward. In order to call this method, run_iteration() must have
        been called at least one so that the root has at least one children. Otherwise, a ValueErrorException
        is raised. """

        if len(self.root.expanded_children) == 0:
            raise ValueError("The root does not have any children")

        return max([child for child in self.root.expanded_children], key=MontecarloNode.avg_reward)

    def run_iteration(self):
        """ Run the sequence of steps required by the Montecarlo search algorithm to add a node
        to the tree """

        selected_node = self.tree_policy()
        reward = self.default_policy(selected_node)
        self.backup(selected_node, reward)

    def tree_policy(self) -> MontecarloNode:
        """ Selects the node which is going to be expanded """

        current_node = self.root
        while not current_node.is_terminal():
            if (next_child := current_node.next_child()) is not None:
                return next_child
            else:
                current_node = current_node.get_best_child()

        return current_node

    def default_policy(self, node: MontecarloNode):
        """ Randomly simulate a game and return a reward based on the result. """

        game = copy.deepcopy(node.state.game)
        move = RandomMove()
        while game.mode != GameMode.FINISHED:
            move.perform_move(game)

        if game.winner is None:
            return 0

        if game.winner == self.current_turn:
            return 1

        return -1

    def backup(self, node: MontecarloNode, reward: int):
        """ Propagate the reward obtained for node until the root is reached """

        while node is not None:
            node.visits += 1
            node.accumulated_rewards += 1
            reward = -reward
            node = node.parent  # type: ignore


class MonteCarloMove(MoveAlgorithm):
    """ This algorithm chooses a move according to the monte carlo tree search algorithm """

    def __init__(self, iterations: int):
        """ iterations are the number of iterations the algorithm is going to run. See
        MonteCarloTree.run_iteration() for more information """

        self.montecarlo_tree = None
        self.iterations = iterations

    def _next_state(self, game: MillGame) -> Optional[State]:
        """ Returns the next state of the game chosen by this algorithm """

        self.montecarlo_tree = MonteCarloTree(game)
        for _ in range(self.iterations):
            self.montecarlo_tree.run_iteration()

        return self.montecarlo_tree.best_node().state

class HybridMove(MoveAlgorithm):
    """ This algorithm chooses a move according to the monte carlo tree search algorithm during n turns, and after that chooses it according to minimax algorithm """

    def __init__(self, n_iterations: int, max_depth: int, mcts_limit: int):
        self.mcts_agent = MonteCarloMove(n_iterations)
        self.minimax_agent = MinimaxMove(max_depth)
        self.mcts_limit = mcts_limit
        self.turn_counter = 0
        
    def _next_state(self, game: MillGame) -> Optional[State]:
        """ Returns the next state of the game chosen by this algorithm """
        if game.mode == GameMode.FINISHED:
            return None

        # Check if MCTS should be used
        if self.turn_counter < self.mcts_limit:
            self.turn_counter += 1
            return self.mcts_agent._next_state(game)
        else:
            return self.minimax_agent._next_state(game)
