"""How many of each product the shop has on the shelf."""


class Inventory:
    def __init__(self):
        self.stock = {}

    def receive(self, name, count):
        if count < 1:
            raise ValueError('count must be at least 1')
        self.stock[name] = self.stock.get(name, 0) + count

    def available(self, name):
        return self.stock.get(name, 0)

    def take(self, name, count):
        if count > self.available(name):
            raise ValueError('not enough %s on the shelf' % name)
        self.stock[name] -= count

    def low(self, limit=3):
        return sorted(name for name, count in self.stock.items() if count <= limit)
