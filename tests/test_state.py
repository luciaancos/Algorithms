# import copy
# import unittest

# from state import State, Move, Sucesor, Action
# from game import MillGame, Turn, GameMode, CellState


# class TestSate(unittest.TestCase):

# def generate_succ_place(self):
# game = MillGame(turn=Turn.BLACK)
# game.mode = GameMode.PLACE
# state = State(game)

# state.free = [1]
# state.chips[1] = 1
# state.gamer[1] = [4, 5, 9]
# state.game.has_to_delete = False
# successors = []

# game_copy = copy.deepcopy(self.game)
# next_state = State(game_copy)
# move = Move(-1, 1, -1)
# sucesor = Sucesor(state, move, next_state)
# action = Action(move, sucesor)
# aux = []
# aux.append(action)

# state.generate_succ_place(successors)

# # del game no cambia nada, del que cambia es del game copy

# self.assertEqual(game_copy.board.get_cell(0, 1), CellState.BLACK)
# self.assertEqual(next_state.turn, Turn.WHITE)
# self.assertEqual(successors, aux)
# self.assertEqual(len(next_state.free), [])
# self.assertEqual(next_state.chips[1], 0)
# self.assertEqual(next_state.gamer[1], [1, 4, 5, 9])

# def generate_succ_move(self):
# game = MillGame(turn=Turn.BLACK)
# game.mode = GameMode.PLACE
# state = State(game)

# state.free = [1]
# state.chips[1] = 0
# state.gamer[1] = [4, 5, 9]
# state.game.has_to_delete = False
# successors = []

# game_copy = copy.deepcopy(self.game)
# next_state = State(game_copy)
# move = Move(4, 1, -1)
# sucesor = Sucesor(state, move, next_state)
# action = Action(move, sucesor)
# aux = []
# aux.append(action)

# state.generate_succ_move(successors)

# self.assertEqual(game_copy.board.get_cell(0, 1), CellState.BLACK)
# self.assertEqual(game_copy.board.get_cell(0, 5), CellState.EMPTY)
# self.assertEqual(next_state.turn, Turn.WHITE)
# self.assertEqual(successors, aux)
# self.assertEqual(len(next_state.free), [])
# self.assertEqual(next_state.chips[1], 0)
# self.assertEqual(next_state.gamer[1], [1, 5, 9])
