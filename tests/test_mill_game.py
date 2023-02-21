import unittest
from board import CellState

from game import (GameMode,
                  MillGame,
                  InvalidMoveException,
                  Turn)


class TestMillGame(unittest.TestCase):

    def test_place_invalid_move(self):
        game = MillGame(turn=Turn.WHITE)
        game.place(0, 0)
        with self.assertRaises(InvalidMoveException):
            game.place(0, 0)

    def test_change_turn_place_mode(self):
        game = MillGame(turn=Turn.BLACK)
        game.place(2, 1)
        self.assertEqual(game.turn, Turn.WHITE)
        game.place(2, 3)
        self.assertEqual(game.turn, Turn.BLACK)

    def test_from_place_to_move(self):
        game = MillGame(turn=Turn.WHITE)
        game._players[0].remaining_pieces = 1
        game._players[1].remaining_pieces = 1

        game.place(0, 0)
        self.assertEqual(game.mode, GameMode.PLACE)
        game.place(1, 1)
        self.assertEqual(game.mode, GameMode.MOVE)
        self.assertEqual(game.turn, Turn.WHITE)

    def test_all_pieces_form_mill_across_rings(self):
        game = MillGame(turn=Turn.WHITE)

        game.board.buff[0] = CellState.WHITE
        game.board.buff[1] = CellState.WHITE
        game.board.buff[2] = CellState.WHITE
        game.board.buff[9] = CellState.WHITE
        game.board.buff[17] = CellState.WHITE

        self.assertTrue(game.all_pieces_form_mill(game.current_player()))

        game.board.buff[7] = CellState.WHITE

        self.assertFalse(game.all_pieces_form_mill(game.current_player()))

    def test_all_pieces_form_mill_same_ring(self):
        game = MillGame(turn=Turn.BLACK)

        game.board.buff[8] = CellState.BLACK
        game.board.buff[15] = CellState.BLACK
        game.board.buff[14] = CellState.BLACK

        game.board.buff[22] = CellState.BLACK
        game.board.buff[21] = CellState.BLACK
        game.board.buff[20] = CellState.BLACK

        self.assertTrue(game.all_pieces_form_mill(game.current_player()))

    def test_remove(self):
        game = MillGame(turn=Turn.WHITE)

        game.place(0, 0)
        game.place(0, 1)
        game.place(0, 7)
        game.place(0, 2)
        game.place(0, 6)

        self.assertEqual(game.turn, Turn.WHITE)
        self.assertTrue(game.has_to_delete)

        alive_pieces = game.other_player().alive_pieces

        game.remove(0, 2)

        self.assertEqual(game.turn, Turn.BLACK)
        self.assertEqual(alive_pieces - game.current_player().alive_pieces, 1)
        self.assertEqual(game.board.get_cell(0, 2), CellState.EMPTY)

        self.assertFalse(game.has_to_delete)
        self.assertEqual(game.mode, GameMode.PLACE)

    def test_finish_mode_from_remove(self):
        game = MillGame(turn=Turn.WHITE)
        game.mode = GameMode.MOVE
        game.has_to_delete = True
        game._players[0].alive_pieces = 3
        game._players[1].alive_pieces = 3

        game.board.buff[0] = CellState.WHITE
        game.board.buff[1] = CellState.WHITE
        game.board.buff[2] = CellState.WHITE

        game.board.buff[23] = CellState.BLACK
        game.board.buff[18] = CellState.BLACK
        game.board.buff[15] = CellState.BLACK

        game.remove(2, 7)

        self.assertEqual(game.mode, GameMode.FINISHED)
        self.assertEqual(game.turn, Turn.WHITE)


    def test_finish_change_turn(self):
        game = MillGame(turn=Turn.WHITE)
        game.mode = GameMode.MOVE
        game.has_to_delete = True

        game.board.buff[0] = CellState.WHITE
        game.board.buff[1] = CellState.WHITE
        game.board.buff[2] = CellState.WHITE

        game.board.buff[9] = CellState.BLACK

        game.board.buff[8] = CellState.WHITE
        game.board.buff[10] = CellState.WHITE
        game.board.buff[17] = CellState.WHITE

        game.board.buff[4] = CellState.BLACK

        game.remove(0, 4)

        self.assertEqual(game.mode, GameMode.FINISHED)
        self.assertEqual(game.turn, Turn.WHITE)

    def test_invalid_move(self):
        game = MillGame(turn=Turn.WHITE)
        game.mode = GameMode.MOVE

        game.board.buff[0] = CellState.WHITE
        game.board.buff[1] = CellState.WHITE
        game.board.buff[2] = CellState.WHITE

        game.board.buff[9] = CellState.BLACK

        with self.assertRaises(InvalidMoveException):
            game.move(1, 2, 1, 4)

        with self.assertRaises(InvalidMoveException):
            game.move(1, 1, 0, 1)

        with self.assertRaises(InvalidMoveException):
            game.move(1, 2, 0, 2)

    def test_move(self):
        game = MillGame(turn=Turn.BLACK)
        game.mode = GameMode.MOVE

        game.board.buff[0] = CellState.WHITE
        game.board.buff[1] = CellState.WHITE
        game.board.buff[2] = CellState.WHITE

        game.board.buff[9] = CellState.BLACK

        game.move(1, 1, 1, 0)
        self.assertEqual(game.board.get_cell(1, 1), CellState.EMPTY)
        self.assertEqual(game.board.get_cell(1, 0), CellState.BLACK)
        self.assertEqual(game.turn, Turn.WHITE)

    def test_invalid_remove(self):
        game = MillGame(turn=Turn.WHITE)

        game.board.buff[0] = CellState.WHITE
        game.board.buff[1] = CellState.WHITE
        game.board.buff[2] = CellState.WHITE

        game.board.buff[22] = CellState.BLACK
        game.board.buff[21] = CellState.BLACK
        game.board.buff[20] = CellState.BLACK
        game.board.buff[12] = CellState.BLACK

        game.has_to_delete = True

        with self.assertRaises(InvalidMoveException):
            game.remove(0, 3)

        with self.assertRaises(InvalidMoveException):
            game.remove(0, 0)

        with self.assertRaises(InvalidMoveException):
            game.remove(2, 4)

        game.remove(1, 4)
