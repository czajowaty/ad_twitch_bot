import random
from game.config import Config
from game.errors import InvalidOperation
from game.inventory import Inventory
from game.unit import Unit
from game.state_machine_action import StateMachineAction
from game.unit_creator import UnitCreator
from game.items import Item


class BattleContext:
    def __init__(self, enemy: Unit):
        self._enemy = enemy
        self._prepare_phase_counter = 0
        self._holy_scroll_counter = 0
        self.is_player_turn = False
        self._finished = False

    @property
    def enemy(self):
        return self._enemy

    def start_prepare_phase(self, counter: int):
        self._prepare_phase_counter = counter

    def is_prepare_phase(self) -> bool:
        return self._prepare_phase_counter > 0

    def dec_prepare_phase_counter(self):
        self._prepare_phase_counter -= 1

    def finish_prepare_phase(self):
        self._prepare_phase_counter = 0

    def is_holy_scroll_active(self) -> bool:
        return self._holy_scroll_counter > 0

    def dec_holy_scroll_counter(self):
        self._holy_scroll_counter -= 1

    def set_holy_scroll_counter(self, counter):
        self._holy_scroll_counter = counter

    def is_finished(self):
        return self._finished

    def finish_battle(self):
        self._finished = True


class StateMachineContext:
    def __init__(self, game_config: Config, player_name: str):
        self._game_config = game_config
        self._player_name = player_name
        self._is_game_finished = False
        self._floor = 0
        self._familiar = None
        self._inventory = Inventory()
        self._battle_context = None
        self._item_buffer = None
        self._familiar_for_trade = None
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
    def inventory(self) -> Inventory:
        return self._inventory

    @property
    def battle_context(self) -> BattleContext:
        return self._battle_context

    def clear_item_buffer(self):
        self._item_buffer = None

    def buffer_item(self, item: Item):
        if self._item_buffer is not None:
            raise InvalidOperation(f'Item already buffered - {self._item_buffer.name}')
        self._item_buffer = item

    def peek_buffered_item(self) -> Item:
        return self._item_buffer

    def take_buffered_item(self) -> Item:
        item = self.peek_buffered_item()
        self.clear_item_buffer()
        return item

    def clear_familiar_for_trade(self):
        self._familiar_for_trade = None

    def set_familiar_for_trade(self, familiar_for_trade: Unit):
        self._familiar_for_trade = familiar_for_trade

    def take_familiar_for_trade(self) -> Unit:
        familiar_for_trade = self._familiar_for_trade
        self.clear_familiar_for_trade()
        return familiar_for_trade

    @property
    def rng(self):
        return self._rng

    def does_action_succeed(self, success_chance: float):
        return self.rng.random() < success_chance

    def is_in_battle(self) -> bool:
        return self._battle_context is not None

    def clear_battle_context(self):
        self._battle_context = None

    def start_battle(self, enemy: Unit):
        if self.is_in_battle():
            raise InvalidOperation(f'Battle already started - {enemy.name}')
        self._battle_context = BattleContext(enemy)

    def finish_battle(self):
        if not self.is_in_battle():
            raise InvalidOperation(f'Battle not started')
        self.clear_battle_context()

    def generate_monster(self, floor: int, level_increase: int=0) -> Unit:
        highest_floor = self.game_config.highest_floor
        if floor > highest_floor:
            raise InvalidOperation(f'Highest floor is {highest_floor}')
        floor_descriptor = self.game_config.floors[floor]
        monster_descriptor = self.rng.choices(floor_descriptor.monsters, floor_descriptor.weights)[0]
        monster_traits = self.game_config.monsters_traits[monster_descriptor.name]
        monster_level = min(monster_descriptor.level + level_increase, self.game_config.levels.max_level)
        return UnitCreator(monster_traits).create(monster_level)

    def generate_action(self, command, *args):
        if self._generated_action is not None:
            raise InvalidOperation(f'Already generated - {self._generated_action}')
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
