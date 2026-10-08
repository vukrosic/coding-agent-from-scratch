"""A shop cart. All prices are in cents, so 800 means 8.00."""

FREE_SHIPPING_FROM = 5000      # an order of 50.00 or more ships free
SHIPPING = 499


class Cart:
    def __init__(self):
        self.items = []        # each item is (name, price, quantity)
        self.coupon = 0        # percent off, from 0 to 100

    def add(self, name, price, quantity=1):
        if price < 0 or quantity < 1:
            raise ValueError('bad price or quantity')
        self.items.append((name, price, quantity))

    def remove(self, name):
        self.items = [item for item in self.items if item[0] != name]

    def apply_coupon(self, percent):
        if not 0 <= percent <= 100:
            raise ValueError('percent must be from 0 to 100')
        self.coupon = percent

    def subtotal(self):
        return sum(price for name, price, quantity in self.items)

    def discount(self):
        return self.subtotal() * self.coupon // 100

    def shipping(self):
        after = self.subtotal() - self.discount()
        if after == 0:
            return 0
        if after > FREE_SHIPPING_FROM:
            return 0
        return SHIPPING

    def total(self):
        return self.subtotal() - self.discount() + self.shipping()

    def receipt(self):
        lines = ['%-12s %2d x %7.2f' % (name, quantity, price / 100) for name, price, quantity in self.items]
        lines.append('%-12s %12.2f' % ('subtotal', self.subtotal() / 100))
        if self.coupon:
            lines.append('%-12s %12.2f' % ('coupon %d%%' % self.coupon, -self.discount() / 100))
        lines.append('%-12s %12.2f' % ('shipping', self.shipping() / 100))
        lines.append('%-12s %12.2f' % ('total', self.total() / 100))
        return '\n'.join(lines)
