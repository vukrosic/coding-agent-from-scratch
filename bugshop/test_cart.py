import unittest

from cart import Cart


class TestCart(unittest.TestCase):
    def test_empty_cart_costs_nothing(self):
        self.assertEqual(Cart().total(), 0)

    def test_one_item(self):
        cart = Cart()
        cart.add('mug', 800)
        self.assertEqual(cart.subtotal(), 800)

    def test_two_of_the_same_item(self):
        cart = Cart()
        cart.add('mug', 800, quantity=2)
        self.assertEqual(cart.subtotal(), 1600)

    def test_remove(self):
        cart = Cart()
        cart.add('mug', 800)
        cart.add('pen', 150)
        cart.remove('mug')
        self.assertEqual(cart.subtotal(), 150)

    def test_coupon(self):
        cart = Cart()
        cart.add('lamp', 4000)
        cart.apply_coupon(25)
        self.assertEqual(cart.discount(), 1000)

    def test_bad_coupon(self):
        with self.assertRaises(ValueError):
            Cart().apply_coupon(120)

    def test_small_order_pays_shipping(self):
        cart = Cart()
        cart.add('pen', 150)
        self.assertEqual(cart.total(), 150 + 499)

    def test_big_order_ships_free(self):
        cart = Cart()
        cart.add('chair', 9000)
        self.assertEqual(cart.shipping(), 0)

    def test_order_of_exactly_fifty_ships_free(self):
        cart = Cart()
        cart.add('lamp', 5000)
        self.assertEqual(cart.shipping(), 0)

    def test_receipt_has_a_total_line(self):
        cart = Cart()
        cart.add('pen', 150)
        self.assertIn('total', cart.receipt())


if __name__ == '__main__':
    unittest.main()
