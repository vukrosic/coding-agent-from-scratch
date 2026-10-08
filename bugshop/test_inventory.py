import unittest

from inventory import Inventory


class TestInventory(unittest.TestCase):
    def test_receive_and_count(self):
        shelf = Inventory()
        shelf.receive('mug', 5)
        self.assertEqual(shelf.available('mug'), 5)

    def test_take(self):
        shelf = Inventory()
        shelf.receive('mug', 5)
        shelf.take('mug', 2)
        self.assertEqual(shelf.available('mug'), 3)

    def test_cannot_take_more_than_there_is(self):
        shelf = Inventory()
        shelf.receive('mug', 1)
        with self.assertRaises(ValueError):
            shelf.take('mug', 2)

    def test_low_stock(self):
        shelf = Inventory()
        shelf.receive('mug', 2)
        shelf.receive('pen', 40)
        self.assertEqual(shelf.low(), ['mug'])


if __name__ == '__main__':
    unittest.main()
