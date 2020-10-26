import logging
from game import commands, items
from game.state_base import StateBase
from game.state_with_monster import StateWithMonster
from game.unit_creator import UnitCreator

logger = logging.getLogger(__name__)


class StateInitialize(StateWithMonster):
    def on_enter(self):
        self._context.floor = 0
        self._generate_familiar()
        self._set_start_inventory()
        self._context.clear_battle_context()
        self._context.clear_item_buffer()
        self._context.clear_unit_buffer()
        if not self._context.is_tutorial_done:
            self._context.add_response(
                "To interact with AD bot, type '!adbot command'. Some commands require additional parameter(s). "
                "In such case you need to specify those after command, e.g. '!adbot use_item Medicinal Herb'. "
                "If you want to see what commands you can use at given moment type '!adbot help'. "
                "Have fun and good luck!")
            self._context.set_tutorial_done()
        self._context.add_response_line_break()
        self._context.add_response(
            "While wandering in the desert, you suddenly notice a huge tower. "
            "Could it be the legendary Monster Tower?! As the legend says, there are great treasures in the tower, "
            "but, as the name suggests, dangerous monsters lurk within. Do you dare to enter the tower?")

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


class StateEnterTower(StateBase):
    def on_enter(self):
        self._context.add_response(
            f"At the entrance to Monster Tower you found a newborn {self._context.familiar.name}. "
            f"It smiles at you and wants to join you in your adventure. You enter the Tower with your new friend "
            f"(who is definitely not going to betray you once you reach the top floor...).")
        self._context.add_response_line_break()
        self._context.generate_action(commands.ENTERED_TOWER)
