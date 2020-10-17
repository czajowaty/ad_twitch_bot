import logging
from game import items
from game.state_with_monster import StateWithMonster
from game.unit_creator import UnitCreator

logger = logging.getLogger(__name__)


class StateInitialize(StateWithMonster):
    def on_enter(self):
        logger.debug(f"{self}.onEnter()")
        self._context.floor = 0
        self._generate_familiar()
        self._set_start_inventory()
        self._context.clear_battle_context()
        self._context.clear_item_buffer()
        self._context.clear_unit_buffer()
        self._context.add_response(
            f"You entered the Monster Tower and you found a newborn {self._context.familiar.name}. "
            f"It smiles at you and wants to join you in your adventure.")
        self._context.generate_action('initialized')

    def _generate_familiar(self):
        monsters_traits = self._context.game_config.monsters_traits
        familiar_name = self._monster_name or self._context.rng.choice(list(monsters_traits.keys()))
        familiar = UnitCreator(monsters_traits[familiar_name]).create(level=1, levels=self.game_config.levels)
        self._context.familiar = familiar

    def _set_start_inventory(self):
        inventory = self._context.inventory
        inventory.clear()
        inventory.add_item(items.Pita())
        inventory.add_item(items.MedicinalHerb())
