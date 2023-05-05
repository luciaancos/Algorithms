from __future__ import annotations
import hashlib
import json

import os
import copy
import math
import random
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Callable, Optional, cast, List, Any

from game import GameMode, Turn, MillGame, Move
from state import State


class BaseAgent(ABC):
    """Base class for the algorithms which perform a specific move on a
    MillGame."""

    def perform_move(self, game: MillGame) -> Optional[Move]:
        """Perform a specific move on 'game'.

        The state of game is modified and the applied move is returned.
        If no action could be performed because the game is won, return
        None
        """

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
        """Get the move which the algorithm considers for the given 'game'. If
        no action can be performed because the game is won, return None.

        This will not update game. If you want to update the game AND
        get the move, you should use self.perform_move() instead of
        applying the returned Move to the game because it is slightly
        faster.
        """
        state = self._next_state(game)
        if state is None:
            return None

        return state.move

    @abstractmethod
    def _next_state(self, game: MillGame) -> Optional[State]:
        """Returns the next state of the game chosen by this algorithm. If
        there are no available state, then return None.

        This method is not meant to be called directly. This is what
        should be overriden by every subclass of MoveAlgorithm
        """


class RandomAgent(BaseAgent):
    """This algorithm chooses a move uniformly at random from the set of
    available ones."""

    def _next_state(self, game: MillGame) -> Optional[State]:
        """Returns the next state of the game chosen by this algorithm."""
        if game.mode == GameMode.FINISHED:
            return None

        # A StopIterationError won't be thrown because that only happens when the game state is finished
        return next(State(game).successors(shuffle=True))


class MinimaxAgent(BaseAgent):
    """This algorithm chooses a move according to the minimax algorithm with
    alpha-beta pruning."""

    def __init__(self, max_depth: int):
        self.max_depth = max_depth

    def _evaluate(self, game: MillGame, current_turn: Turn) -> int:
        """Evaluates the value of the state of a given game for the current
        player."""
        if game.mode == GameMode.FINISHED:
            winner = game.winner
            if winner is not None:
                # The game is finished when one of the players has 2 chips left,
                # so the maximum difference of 7 pieces will be used for won/lost
                # plays
                if winner == current_turn:
                    return 7
                return -7
            return 0
        # Get index of game.players for the current player and the opponent
        current_player_idx = next(
            i
            for i, player in enumerate(game.players)
            if player.associated_cell_state.name == current_turn.name
        )
        opponent_idx = current_player_idx ^ 1
        # Use the difference in the number of remaining pieces as heuristic
        return (
            game.players[current_player_idx].remaining_pieces
            - game.players[opponent_idx].remaining_pieces
        )

    def _max_value(
        self,
        game: MillGame,
        current_turn: Turn,
        alpha: int,
        beta: int,
        depth: int
    ) -> int:
        """Computes the value of a state for the player that is maximizing."""
        if depth == 0 or game.mode == GameMode.FINISHED:
            return self._evaluate(game, current_turn)

        value = float("-inf")
        for successor in State(game).successors():
            value = max(
                value,
                self._min_value(successor.game, current_turn,
                                alpha, beta, depth - 1),
            )
            alpha = max(alpha, value)
            if alpha >= beta:
                break

        return value

    def _min_value(
        self,
        game: MillGame,
        current_turn: Turn,
        alpha: int,
        beta: int,
        depth: int
    ) -> int:
        """Computes the value of a state for the player that is minimizing."""
        if depth == 0 or game.mode == GameMode.FINISHED:
            return self._evaluate(game, current_turn)

        value = float("inf")
        for successor in State(game).successors():
            value = min(
                value,
                self._max_value(successor.game, current_turn,
                                alpha, beta, depth - 1),
            )
            beta = min(beta, value)
            if alpha >= beta:
                break

        return value

    def _next_state(self, game: MillGame) -> Optional[State]:
        """Returns the next state of the game chosen by this algorithm."""
        if game.mode == GameMode.FINISHED:
            return None

        best_value = float("-inf")
        best_state = None
        current_turn = game.turn

        for successor in State(game).successors():
            value = self._min_value(
                successor.game,
                current_turn,
                float("-inf"),
                float("inf"),
                self.max_depth,
            )
            if value > best_value:
                best_value = value
                best_state = successor

        return best_state


@dataclass
class MontecarloNode:
    state: State
    parent: Optional[MontecarloNode] = None
    visits: int = 0
    accumulated_rewards: float = 0
    expanded_children: list[MontecarloNode] = field(
        default_factory=list, init=False)

    def __post_init__(self):
        self._sucessors = self.state.successors(shuffle=True)

    def next_child(self) -> Optional[MontecarloNode]:
        """Add a child to this node and return it.

        If this node is fully expanded, return None
        """
        new_state = next(self._sucessors, None)
        if new_state is None:
            return None

        child = MontecarloNode(new_state, self)
        self.expanded_children.append(child)
        return child

    def avg_reward(self) -> float:
        """Returns the average reward for this node."""
        if self.visits == 0:
            raise ValueError(
                "You cannot access the average reward for a node which has not "
                "been in a simulation"
            )

        return self.accumulated_rewards / self.visits

    def uct_value(self, cp: float) -> float:
        """Returns the uct value for the this node.

        cp is a constant, which the user is free to choose, that is part of the formula
        which ranks an unexplored child based on how appropiate it is to explore it.

        If this node is the root, an exception is raised
        """

        if self.parent is None:
            raise ValueError("You can not get the evaluation of the root")

        bound = 2 * cp * (2 * math.log(self.parent.visits) /
                          self.visits) ** 0.5
        return self.avg_reward() + bound

    def get_best_child(self, cp: float) -> MontecarloNode:
        """Returns the child node with the highest uct value.

        cp is a constant, which the user is free to choose, that is part of the formula
        which ranks an unexplored child based on how appropiate it is to explore it.

        """
        return max(self.expanded_children, key=lambda child: child.uct_value(cp))

    def is_terminal(self) -> bool:
        """Returns true if this is a terminal state.

        A terminal state is one which does not have any children because
        it wraps a game which is finished
        """

        return self.state.game.mode == GameMode.FINISHED


class _SimulationExecutor:
    """ Wrapper for the ProcessPoolExecutor which will perform several simulations on a given MillGame """

    def __init__(self, runs: int):
        self.runs = runs

        # The processes are created lazily. This means that although the maximum number
        # of processes spawned is os.cpu_count(), they will created if needed
        self._executor = ProcessPoolExecutor()

    def run_simulation(self,
                       simulation: Callable[[MillGame, Turn], float],
                       game: MillGame,
                       turn: Turn) -> list[float]:
        """ Run 'runs' simulations in parallel """

        futures = [self._executor.submit(
            simulation, game, turn) for _ in range(self._runs)]
        rewards = [future.result() for future in futures]
        return rewards

    def shutdown(self):
        self._executor.shutdown()

    @property
    def runs(self) -> int:
        return self._runs

    @runs.setter
    def runs(self, runs):
        if runs <= 0:
            raise ValueError("'runs' cannot be negative or 0")
        self._runs = runs


class MonteCarloTree:

    def __init__(self, game: MillGame) -> None:
        state = State(game)
        self.root = MontecarloNode(state)
        self.current_turn = self.root.state.game.turn

    def best_node(self) -> MontecarloNode:
        """Returns the node with the highest average reward.

        In order to call this method, run_iteration() must have been
        called at least one so that the root has at least one children.
        Otherwise, a ValueErrorException is raised.
        """

        if len(self.root.expanded_children) == 0:
            raise ValueError("The root does not have any children")

        return max(self.root.expanded_children, key=MontecarloNode.avg_reward)

    def run_iteration(self, cp: float, executor: Optional[_SimulationExecutor] = None):
        """Run the sequence of steps required by the Montecarlo search
        algorithm to add a node to the tree.

        cp is the constant given to the formula which selects the best child of a montecarlo node.

        if 'executor' is not None, it will be used to perform several simulations on the node
        selected by tree_policy. The number of simulations will correspond to the number returned
        by os.cpu_count(). In case the number of CPUs cannot be determined, the executor is not
        used for the simulation. 
        Therefore, to improve performance, the number of processes in pool (max_workers) must 
        be set to that number. if 'executor', only one simulation will be performed on the selected node.
        """

        selected_node = self.tree_policy(cp)
        selected_game = selected_node.state.game

        # If we are going to simulate it just once, it is cheaper to do it here instead of on another
        # process because of IPC overhead
        if executor is not None and executor.runs > 1:
            # A copy is not needed here because all the data needed to run a simulation is cloned so that
            # the process can use it and that includes the MillGame
            rewards = executor.run_simulation(
                self.default_policy, selected_game, self.current_turn)
            reward = sum(rewards)
            visited = executor.runs
        else:
            reward = self.default_policy(
                copy.deepcopy(selected_game), self.current_turn)
            visited = 1

        self.backup(selected_node, reward, visited)

    def tree_policy(self, cp: float) -> MontecarloNode:
        """Selects the node which is going to be expanded."""
        current_node = self.root
        while not current_node.is_terminal():
            if (next_child := current_node.next_child()) is not None:
                return next_child
            current_node = current_node.get_best_child(cp)

        return current_node

    @staticmethod
    def default_policy(game: MillGame, current_turn: Turn):
        """Randomly simulate a game and return a reward based on the result.
        This method is static so that pickle does not try to serialize MonteCarloTree """
        random_agent = RandomAgent()

        while game.mode != GameMode.FINISHED:
            random_agent.perform_move(game)

        if game.winner is None:
            return 0.5
        if game.winner == current_turn:
            return 1
        return 0

    def backup(self, node: MontecarloNode, reward: float, visited: int):
        """Propagate the reward obtained for node until the root is reached.
        'visited' is the number of times the node has been visited. """

        while node is not None:
            node.visits += visited
            node.accumulated_rewards += reward
            node = node.parent  # type: ignore


class MCTSAgent(BaseAgent):
    """This algorithm chooses a move according to the Monte Carlo Tree Search
    algorithm."""

    def __init__(self, iterations: int, runs: int = 1, cp: Optional[int] = None):
        """iterations are the number of iterations the algorithm is going to
        run.

        cp is a constant which influences the value given to a state when deciding
        which one to choose. If None is given, a recommended one is used. See MontecarloNode.uct_value()
        See MonteCarloTree.run_iteration() for more information

        'runs' is the number of simulations that will be made on a chosen node. If this number is greater than 1,
        then the simulations will be run in parallel in a maximum of os.cpu_count() proceses. The optimal value
        depends on a lot of factors but the recommendations is to set that number to os.cpu_count(). If 'runs' equals
        1, no additional process will be created.
        """

        self.montecarlo_tree = None
        self.iterations = iterations
        self.cp = 1 / 2 ** 0.5 if cp is None else cp

        self._executor = None
        self.runs = runs

    def _next_state(self, game: MillGame) -> Optional[State]:
        """Returns the next state of the game chosen by this algorithm."""
        self.montecarlo_tree = MonteCarloTree(game)
        for _ in range(self.iterations):
            self.montecarlo_tree.run_iteration(self.cp, self._executor)

        return self.montecarlo_tree.best_node().state

    def release(self):
        """ Release the resources aquired by the agent. If parallel is True, it will release
        the resources aquired by the executor. Otherwise, it won't do anything. The same is done
        when the context manager protocol is used."""
        if self._executor is not None:
            self._executor.shutdown()

    @property
    def runs(self) -> int:
        return self._runs

    @runs.setter
    def runs(self, runs: int):
        if self._executor is None:
            if runs > 1:
                self._executor = _SimulationExecutor(runs)
            elif runs <= 0:
                raise ValueError("'runs' cannot be 0 or negative")
        else:
            self._executor.runs = runs

        self._runs = runs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.release()


class HybridAgent(BaseAgent):
    """This algorithm chooses a move according to the monte carlo tree search
    algorithm during n turns, and after that chooses it according to minimax
    algorithm."""

    def __init__(self, n_iterations: int, max_depth: int, mcts_limit: int):
        self.mcts_agent = MCTSAgent(n_iterations)
        self.minimax_agent = MinimaxAgent(max_depth)
        self.mcts_limit = mcts_limit
        self.turn_counter = 0

    def _next_state(self, game: MillGame) -> Optional[State]:
        """Returns the next state of the game chosen by this algorithm."""
        if game.mode == GameMode.FINISHED:
            return None

        # Check if MCTS should be used
        if self.turn_counter < self.mcts_limit:
            self.turn_counter += 1
            return self.mcts_agent._next_state(game)
        return self.minimax_agent._next_state(game)


def _to_md5(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()

class QTable:
    """ This is the table where the rewards for a given state-action pair are given """

    def __init__(self):
        self._table: dict[str, dict[str, float]] = {}

    def get_reward(self, state: State, move: Move) -> Optional[float]:
        """ Returns the reward for the given state-move pair """ 

        state_key, move_key = self._get_keys(state, move)
        if (reward_table := self._table.get(state_key)) is not None and (reward := reward_table.get(move_key)) is not None:
            return reward

        return None

    def apply_reward(
            self,
            state: State,
            move: Move,
            reward: float,
            max_reward: float,
            lr: float,
            df: float,
            initial_value: float=0
        ):

        """ Updates the reward according to the value-iteration algorithm """

        # Get the stored reward. If it does not exist, set it to 0 by default
        current_reward = self.get_reward(state, move)
        current_reward = initial_value if current_reward is None else current_reward

        # Calcuate the value
        value = current_reward + lr * (reward + df * max_reward - current_reward)

        # Store the new value
        state_key, move_key = self._get_keys(state, move)
        if state_key in self._table:
            move_table = self._table[state_key]
        else:
            move_table: dict[str, float] = {}
            self._table[state_key] = move_table

        move_table[move_key] = value

    def max_reward_move(self, state: State) -> Optional[tuple[float, Move]]:
        """ Return the pair (reward, Move) with the highest reward for the given state. If
        the state does not exist or it does not have any move stored in the table then 
        None is returned """

        state_key = self._get_state_key(state)
        if (move_table := self._table.get(state_key)) is None:
            return None

        if len(move_table) == 0:
            return None

        all_pairs = [(reward, Move.from_compressed(int(compressed_move))) 
                     for compressed_move, reward in move_table.items()]

        return max(all_pairs, key=lambda pair : pair[0])

    def best_move(self, state: State) -> Optional[Move]:
        """ Return the best move for the given state according to what is stored in the q table """

        if (reward_move := self.max_reward_move(state)) is None:
            return None

        return reward_move[1]

    def max_reward(self, state: State) -> Optional[float]:
        """ Return the best move for the given state according to what is stored in the q table """

        if (reward_move := self.max_reward_move(state)) is None:
            return None

        return reward_move[0]

    def save(self, file_name: str):
        """ Saves the q table to the given file_name """
        # TODO: it would be more pythonic if we use Path instead of a str for the filename

        with open(file_name, "w") as json_file:
            json.dump(self._table, json_file, indent=1)

    def load(self, file_name: str):
        """ Loads the q table from a file """

        # TODO: it would be more pythonic if we use Path instead of a str for the filename
        with open(file_name, 'r') as file:
            self._table = json.load(file)


    def _get_state_key(self, state: State) -> str:
        remaining_players = (state.game.players[0].remaining_pieces, 
                             state.game.players[1].remaining_pieces)

        unique = str(state.game_info) + str(state.game.turn) + str(remaining_players)

        return _to_md5(unique)

    def _get_move_key(self, move: Move) -> str:
        return str(move.to_compressed())

    def _get_keys(self, state: State, move: Move) -> tuple[str, str]:
        return self._get_state_key(state), self._get_move_key(move)

def _default_reward_fn(state: State, initial_turn: Turn):
    """ Obtain the reward for this state based on whether it is terminal or if 
        it gets any mills of each move. """

    reward = 0
    # Check if the state is terminal
    if state.game.mode == GameMode.FINISHED:
        if state.game.winner == initial_turn:
            reward += 100
        else:
            reward += -100
    else:
        reward += -1

    # Check if there is a mill
    if state.move is not None and state.move.kill is not None:
        if state.game.turn != initial_turn:
            reward += 30
        else:
            reward += -30

    return reward

class Trainer:

    def __init__(self, 
                 *,
                 episodes: int,
                 file_name: str,
                 resume=True,
                 lr: float=0.1,
                 df: float=0.9,
                 gamma: float=0,
                 reward_fn: Optional[Callable[[State, Turn], float]]=None,
                 reward_fn_args: Optional[List[Any]]=None):
        """ If 'resume' is true, it assumed that file_name already exists and the intention
        is continue training with the results obtained in a previous training session. If
        resume is True but file_name does not exist, then an empty q table is created but
        the file is not saved until the training session has finished 

        reward_fn is a function which calculates the reward given for a move.
        gamma denotes how often a montecarlo agent will be used

        NOTE: this will override file_name if it exists but resume is set to False """

        # TODO: it would be more pythonic if we use Path instead of a str for a filename

        self.q_table = QTable()

        self.file_name = file_name
        self.episodes = episodes
        self.lr = lr
        self.df = df
        self.reward_fn = _default_reward_fn if reward_fn is None else reward_fn
        self.reward_fn_args = reward_fn_args
        self.gamma = gamma

        # This is necessary to perform the training
        self._random_agent = RandomAgent()

        # FIXME: this is not the best approach for exploration
        # FIXME: should this agent be given as an argument?
        self._mcts_agent = MCTSAgent(iterations=50)

        # Load the q_table if appropiate
        if resume and os.path.exists(self.file_name):
            self.q_table.load(self.file_name)

    def train(self, turn: Turn, max_moves: int=150, verbose=False):
        """ Train the agent by filling the q_table. Turn is the turn of the agent """

        for i in range(self.episodes):
            state = State(MillGame(turn=turn, max_movements=max_moves))
            self._run_episode(state)
            if verbose:
                print(f"Finished episode #{i + 1}")

    def save_results(self):
        self.q_table.save(self.file_name)

    def _run_episode(self, state: State):
        initial_turn = state.game.turn

        while state.game.mode != GameMode.FINISHED:
            if random.random() < self.gamma:
                next_state = cast(State, self._mcts_agent._next_state(state.game))
            else:
                next_state = cast(State, self._random_agent._next_state(state.game))

            if self.reward_fn_args is not None:
                reward = self.reward_fn(state, initial_turn, *self.reward_fn_args)
            else:
                reward = self.reward_fn(state, initial_turn)
            
            reward = self.reward_fn(next_state, initial_turn)
            if (max_reward := self.q_table.max_reward(next_state)) is None:
                max_reward = 0

            self.q_table.apply_reward(
                    state,
                    next_state.move, # type: ignore
                    reward=reward,
                    max_reward=max_reward,
                    lr=self.lr,
                    df=self.df
            )
            state = next_state

class QAgent(BaseAgent):
    """This algorithm chooses a move according to the values it had learned 
    by applying q-learning algorithm"""

    def __init__(self, q_table: QTable, alternative_agent: Optional[BaseAgent]=None):
        """ Alternative agent is the agent which is going to perform the move in case the state is not found """

        self.q_table = q_table
        self.alternative_agent = MCTSAgent(iterations=50) if alternative_agent is None else alternative_agent

    def _next_state(self, game: MillGame) -> Optional[State]:
        if game.mode == GameMode.FINISHED:
            return None

        state = State(game)
        move = self.q_table.best_move(state)
        if move is None:
            return self.alternative_agent._next_state(game)
        else:
            game_copy = copy.deepcopy(game)
            game_copy.apply_move(move)
            return State(game_copy, move, state)


class QlearningAgent(BaseAgent):
    """This algorithm chooses a move according to the values it had learned 
    by applying q-learning through a dynamic programming algorithm"""

    def __init__(self, num_episodes: int = 5, learning_factor: float = 0.1, discount_factor: float = 0.9):
        self.num_episodes = num_episodes
        self.learning_factor = learning_factor 
        self.discount_factor = discount_factor
        self.curiosity_factor = 0.2
        self.q_table = {}

    def calculate_reward(self, initial_turn: Turn, next_state: State) -> int:
        """ Obtain the reward for this state based on whether it is terminal or if 
        it gets any mills. """

        reward = 0
        # Check if the state is terminal
        if next_state.game.mode == GameMode.FINISHED:
            if next_state.game.winner == initial_turn:
                reward += 100
            else:
                reward += -100
        else:
            reward += -1

        # Check if there is a mill
        if next_state.move.kill is not None:
            if next_state.game.turn == initial_turn:
                reward += 30
            else:
                reward += -30

        return reward

    def max_qvalue(self, state: State) -> float:
        """Obtain the maximum Q value for this state based on all possible actions."""
        best = None
        all_states = list(state.successors())

        for key, value in self.q_table.items():
            for sucessor in all_states:
                check_tuple = str(state) + str(sucessor.move)
                hash_check_tuple = hashlib.md5(
                    check_tuple.encode()).hexdigest()
                if key == hash_check_tuple:
                    if best is None or value > best:
                        best = value
        if best is None:
            best = 0

        return best

    def train(self, game: MillGame) -> Optional[State]:

        """Loads the content of the json file and stores it in the q_table 
        dictionary. This dictionary will be updated with new state-action pairs 
        with their corresponding value of the q-value formula. This represents 
        the knowledge of our agent """
        try:
            with open('q_table.json', 'r') as f:
                self.q_table = json.load(f)
        except FileNotFoundError:
            self.q_table = {}

        for _ in range(self.num_episodes):
            state = next(State(game).successors(shuffle=True))
            initial_turn = state.game.turn
            while state.game.mode != GameMode.FINISHED:
                # prob = random.random()
                # if prob < self.curiosity_factor:
                #     next_state = next(state.successors(shuffle=True))
                # else:
                #     mc_player = MCTSAgent(iterations=50)
                #     next_state = mc_player._next_state(state.game)
                next_state = next(state.successors(shuffle=True))

                key = str(state) + str(next_state.move)
                hash_key = hashlib.md5(key.encode()).hexdigest()

                self.q_table[hash_key] = 0
                value = self.q_table[hash_key] + self.learning_factor * \
                    (self.calculate_reward(initial_turn, next_state) +
                     self.discount_factor * self.max_qvalue(next_state) -
                     self.q_table[hash_key])
                self.q_table[hash_key] = value

                state = next_state
            print("termina episodio")

        with open("q_table.json", "w") as json_file:
            json.dump(self.q_table, json_file, indent=1)

    def _next_state(self, game: MillGame) -> Optional[State]:
        """Returns the next state of the game chosen by this algorithm."""
        # TODO: cargar q_table
        state = State(game)
        best = None
        sum_prob = 0
        prob = 0

        for key, value in self.q_table.items():
            for sucessor in state.successors():
                check_tuple = str(state) + str(sucessor.move)
                hash_check_tuple = hashlib.md5(
                    check_tuple.encode()).hexdigest()
                if key == hash_check_tuple:
                    sum_prob += value

        for key, value in self.q_table.items():
            for sucessor in state.successors():
                check_tuple = str(state) + str(sucessor.move)
                hash_check_tuple = hashlib.md5(
                    check_tuple.encode()).hexdigest()
                if key == hash_check_tuple:
                    if prob < (value/sum_prob):
                        prob = value/sum_prob
                        best = sucessor

        if best is not None:
            return best
        else:
            mc_player = MCTSAgent(iterations=50)
            return mc_player._next_state(state.game)

