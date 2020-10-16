import logging
from game import items
from game.state_base import StateBase
from game.unit_creator import UnitCreator

logger = logging.getLogger(__name__)


class StateInitialize(StateBase):
    def __init__(self, context, familiar_name: str=None):
        super().__init__(context)
        self._familiar_name = familiar_name

    def on_enter(self):
        logger.debug(f"{self}.onEnter()")
        self._context.floor = 0
        self._generate_familiar()
        self._set_start_inventory()
        self._context.clear_battle_context()
        self._context.clear_item_buffer()
        self._context.clear_familiar_for_trade()
        self._context.generate_action('initialized')

    def _generate_familiar(self):
        monsters_traits = self._context.game_config.monsters_traits
        if self._familiar_name is None:
            familiar_name = self._context.rng.choice(list(monsters_traits.keys()))
        else:
            familiar_name = self._familiar_name
        familiar = UnitCreator(monsters_traits[familiar_name]).create(level=1, levels=self.game_config.levels)
        self._context.familiar = familiar
        self._context.add_response(
            f'You entered the Monster Tower and you found a newborn {familiar_name}. '
            f'It smiles at you and wants to join you in your adventure.')

    def _set_start_inventory(self):
        inventory = self._context.inventory
        inventory.clear()
        inventory.add_item(items.Pita())
        inventory.add_item(items.MedicinalHerb())

    @classmethod
    def _parse_args(cls, context, args):
        if len(args) == 0:
            return ()
        familiar_name = args[0]
        if familiar_name not in context.game_config.monsters_traits.keys():
            raise cls.ArgsParseError('Unknown monster')
        return familiar_name,
