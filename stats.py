import itertools
import json
import time
import os
from typing import List
from game import MillGame, GameMode, Turn
from agents import BaseAgent, RandomAgent, MinimaxAgent, MCTSAgent, HybridAgent, QAgent, QTable

def play_game(game: MillGame, agent1: BaseAgent, agent2: BaseAgent) -> GameMode:
    total_time_agent1 = 0
    total_time_agent2 = 0
    move_count_agent1 = 0
    move_count_agent2 = 0

    print(agent1.__class__.__name__, "vs", agent2.__class__.__name__)
    while game.mode != GameMode.FINISHED:
        start_time = time.time()
        move = agent1.perform_move(game)
        total_time_agent1 += time.time() - start_time
        move_count_agent1 += 1
        print("agent1", game.current_player().associated_cell_state.name, move)

        if game.mode == GameMode.FINISHED:
            break

        start_time = time.time()
        move = agent2.perform_move(game)
        total_time_agent2 += time.time() - start_time
        move_count_agent2 += 1
        print("agent2", game.current_player().associated_cell_state.name, move)

    print("winner", game.winner.name if game.winner is not None else "draw")
    mean_time_agent1 = total_time_agent1 / move_count_agent1
    mean_time_agent2 = total_time_agent2 / move_count_agent2
    return game.winner, mean_time_agent1, mean_time_agent2


def load_results(output_file: str) -> dict:
    if os.path.exists(output_file):
        with open(output_file, "r") as f:
            return json.load(f)
    else:
        return {}

def save_results(results: dict, output_file: str) -> None:
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

def gather_statistics(agent_combinations: List[tuple[BaseAgent, BaseAgent]],
                      output_file: str,
                      n_games: int = 50,
                      max_moves: int = 100) -> None:
    results = load_results(output_file)
    for agent1, agent2 in agent_combinations:
        agent1_wins = 0
        agent2_wins = 0
        draws = 0
        total_time_agent1 = 0
        total_time_agent2 = 0

        key = str((agent1.__class__.__name__, agent2.__class__.__name__))
        if key in results:
            total_plays = results[key]["agent1_wins"] + results[key]["agent2_wins"] + results[key]["draws"]
            if total_plays >= n_games:
                continue
            agent1_wins = results[key]["agent1_wins"]
            agent2_wins = results[key]["agent2_wins"]
            draws = results[key]["agent2_wins"]
            total_time_agent1 = results[key]["mean_time_agent1"] * total_plays
            total_time_agent2 = results[key]["mean_time_agent2"] * total_plays

        for _ in range(n_games):
            game = MillGame(turn=Turn.WHITE, max_movements=max_moves)
            winner, mean_time_agent1, mean_time_agent2 = play_game(game, agent1, agent2)
            total_time_agent1 += mean_time_agent1
            total_time_agent2 += mean_time_agent2

            if winner is None:
                draws += 1
            elif winner == Turn.WHITE:
                agent1_wins += 1
            else:
                agent2_wins += 1
            
            total_plays = agent1_wins + agent2_wins + draws

            results[key] = {
                "agent1_wins": agent1_wins,
                "agent2_wins": agent2_wins,
                "draws": draws,
                "mean_time_agent1": total_time_agent1 / total_plays,
                "mean_time_agent2": total_time_agent2 / total_plays,
            }
            save_results(results, output_file)


if __name__ == "__main__":
    agent1 = RandomAgent()
    agent2 = MinimaxAgent(max_depth=4)
    agent3 = MCTSAgent(iterations=50, runs=4)
    agent4 = HybridAgent(n_iterations=50, max_depth=4, mcts_limit=10)
    q_table = QTable()  # Assuming a pre-trained QTable
    q_table.load(file_name="q_table.json")
    agent5 = QAgent(q_table=q_table)

    agents = [agent1, agent2, agent3, agent4, agent5]
    agent_combinations = list(itertools.combinations(agents, 2))
    agent_combinations = [(a1, a2) for a1, a2 in agent_combinations if a1 != a2]
    print("Total number of games:", len(agent_combinations))
    for agent1, agent2 in agent_combinations:
        print(agent1.__class__.__name__, "vs", agent2.__class__.__name__)
    print()
    stats = gather_statistics(agent_combinations, output_file="stats.json")
