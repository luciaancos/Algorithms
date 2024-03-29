import unittest

from board import Board, CellState


class TestBoard(unittest.TestCase):
    def test_get_cell(self):
        buff = [CellState.EMPTY] * 24

        buff[17] = CellState.BLACK
        buff[11] = CellState.WHITE
        buff[7] = CellState.BLACK

        board = Board(buff)

        self.assertEqual(board.get_cell(2, 1), CellState.BLACK)
        self.assertEqual(board.get_cell(1, 3), CellState.WHITE)
        self.assertEqual(board.get_cell(0, 7), CellState.BLACK)
        self.assertEqual(board.get_cell(2, 7), CellState.EMPTY)

    def test_put_cell(self):
        board = Board()

        board.put_cell(2, 1, CellState.BLACK)
        board.put_cell(1, 3, CellState.WHITE)
        board.put_cell(0, 7, CellState.BLACK)

        self.assertEqual(board.get_cell(2, 1), CellState.BLACK)
        self.assertEqual(board.get_cell(1, 3), CellState.WHITE)
        self.assertEqual(board.get_cell(0, 7), CellState.BLACK)
        self.assertEqual(board.get_cell(2, 7), CellState.EMPTY)

    def test_remove(self):
        board = Board()

        board.put_cell(2, 7, CellState.BLACK)
        board.remove(2, 7)

        self.assertEqual(board.get_cell(2, 7), CellState.EMPTY)

    def test_is_intersection(self):
        board = Board()

        self.assertTrue(board.is_intersection(2, 7))
        self.assertFalse(board.is_intersection(1, 6))

    def test_are_adjacent(self):
        board = Board()

        self.assertFalse(board.are_adjacent(2, 2, 2, 2))
        self.assertTrue(board.are_adjacent(2, 1, 1, 1))
        self.assertTrue(board.are_adjacent(2, 0, 2, 7))

        self.assertFalse(board.are_adjacent(0, 6, 1, 6))
        self.assertFalse(board.are_adjacent(1, 6, 0, 6))

    def test_is_mill_same_ring(self):
        board = Board()

        board.put_cell(0, 0, CellState.BLACK)
        board.put_cell(0, 1, CellState.BLACK)
        board.put_cell(0, 2, CellState.BLACK)

        self.assertTrue(board.is_mill(0, 0))
        self.assertTrue(board.is_mill(0, 1))
        self.assertTrue(board.is_mill(0, 2))

        board.put_cell(1, 2, CellState.WHITE)
        board.put_cell(1, 3, CellState.WHITE)
        board.put_cell(1, 4, CellState.WHITE)

        self.assertTrue(board.is_mill(1, 2))
        self.assertTrue(board.is_mill(1, 3))
        self.assertTrue(board.is_mill(1, 4))

        board.put_cell(1, 6, CellState.WHITE)

        self.assertFalse(board.is_mill(1, 6))
        self.assertFalse(board.is_mill(1, 5))

        board.put_cell(2, 5, CellState.WHITE)
        board.put_cell(2, 6, CellState.WHITE)
        board.put_cell(2, 7, CellState.WHITE)

        self.assertFalse(board.is_mill(2, 6))
        self.assertFalse(board.is_mill(2, 7))
        self.assertFalse(board.is_mill(2, 5))

    def test_is_any_adjacent_cell_empty(self):
        board = Board()

        board.put_cell(0, 1, CellState.WHITE)
        board.put_cell(1, 0, CellState.WHITE)
        board.put_cell(1, 2, CellState.WHITE)

        self.assertTrue(board.is_any_adjacent_cell_empty(1, 1))

        board.put_cell(2, 1, CellState.BLACK)

        self.assertFalse(board.is_any_adjacent_cell_empty(1, 1))

    def test_is_mill_across_ring(self):
        board = Board()

        board.put_cell(0, 7, CellState.BLACK)
        board.put_cell(1, 7, CellState.BLACK)
        board.put_cell(2, 7, CellState.BLACK)

        self.assertTrue(board.is_mill(0, 7))
        self.assertTrue(board.is_mill(1, 7))
        self.assertTrue(board.is_mill(2, 7))

        board.put_cell(0, 3, CellState.BLACK)
        board.put_cell(2, 3, CellState.BLACK)
