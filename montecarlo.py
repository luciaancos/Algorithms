from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field
from typing import Optional

from state import State
from game import MillGame, GameMode
from move_algorithm import MoveAlgorithm, RandomMove


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

        _, child = max([(child.uct_value(), child)
                       for child in self.expanded_children])
        return child

    def is_terminal(self) -> bool:
        """ Returns true if this is a terminal state. A terminal state is one which does not have
        any children because it wraps a game which is finished """

        return self.state.game.mode == GameMode.FINISHED


class MonteCarloTree:

    def __init__(self, game: MillGame) -> None:
        state = State(game)
        self.root = MontecarloNode(state)
        self.current_turn = self.root.state.game.turn

    def best_state(self) -> State:
        """ Returns the next state with the highest average reward. In order to call this method, run_iteration() must have
        been called at least one so that the root has at least one children. Otherwise, a ValueErrorException
        is raised. """

        if len(self.root.expanded_children) == 0:
            raise ValueError("The root does not have any children")

        _, child = max([(child.avg_reward(), child) for child in self.root.expanded_children])
        return child.state

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

        return self.montecarlo_tree.best_state().move  # type: ignore
