from game.unit import Monster


class Controller:
    def __init__(self):
        self._inventory = []
        self._familiar = Monster('Kewne')
