import random
from .config import Config
from game.unit import Unit
from .state_machine_action import StateMachineAction


class BattleContext:
    def __init__(self, enemy: Unit):
        self.enemy = enemy
        self.is_player_turn = False


class StateMachineContext:
    class InvalidOperation(Exception):
        pass

    MAX_ITEMS = 5

    def __init__(self, game_config: Config, player_name: str):
        self._game_config = game_config
        self._player_name = player_name
        self._floor = 0
        self._familiar = None
        self._inventory = []
        self._battle_context = None
        self._rng = random.Random()
        self._responses = []
        self._generated_action = None

    @property
    def game_config(self):
        return self._game_config

    @property
    def player_name(self):
        return self._player_name

    @property
    def floor(self):
        return self._floor

    @floor.setter
    def floor(self, value):
        self._floor = value

    @property
    def familiar(self) -> Unit:
        return self._familiar

    @familiar.setter
    def familiar(self, value):
        self._familiar = value

    @property
    def inventory(self) -> list:
        return self._inventory

    @property
    def battle_context(self) -> BattleContext:
        return self._battle_context

    @property
    def rng(self):
        return self._rng

    def does_action_succeed(self, success_chance: float):
        return self.rng.random() < success_chance 

    def clear_inventory(self):
        self._inventory.clear()

    def add_item(self, item):
        if len(self._inventory) >= self.MAX_ITEMS:
            raise self.InvalidOperation(f"Trying to add {item} to full inventory")
        self._inventory.append(item)

    def take_item(self, index):
        if index >= len(self._inventory):
            raise self.InvalidOperation(
                f"Trying to take item at index {index} from inventory of size {len(self._inventory)}")
        return self._inventory.pop(index)

    def start_battle(self, enemy: Unit):
        if self._battle_context is not None:
            raise self.InvalidOperation(f"Battle already started - {enemy.name}")
        self._battle_context = BattleContext(enemy)

    def finish_battle(self):
        if self._battle_context is None:
            raise self.InvalidOperation(f"Battle not started")
        self._battle_context = None

    def generate_action(self, command, *args):
        if self._generated_action is not None:
            raise self.InvalidOperation(f"Already generated - {self._generated_action}")
        self._generated_action = StateMachineAction(command, args, is_given_by_admin=True)

    def has_action(self) -> bool:
        return self._generated_action is not None

    def take_action(self) -> StateMachineAction:
        action = self._generated_action
        self._generated_action = None
        return action

    def add_response(self, response: str):
        self._responses.append(response)

    def take_responses(self) -> list:
        responses = self._responses[:]
        self._responses.clear()
        return responses
