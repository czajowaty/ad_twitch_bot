import logging
from game.unit_creator import UnitCreator
from .state_base import StateBase

logger = logging.getLogger(__name__)


class StateInitialize(StateBase):
    def on_enter(self):
        logger.debug(f"{self}.onEnter()")
        self._context.floor = 0
        self._generate_familiar()
        self._set_start_inventory()
        self._context.generate_action('initialized')

    def _generate_familiar(self):
        units_traits = self._context.game_config.units_traits
        familiar_name = self._context.rng.choice(list(units_traits.keys()))
        familiar = UnitCreator(units_traits[familiar_name]).create(level=1)
        self._context.familiar = familiar
        self._context.add_response(
            f'You entered the Monster Tower and you found a newborn {familiar_name}. '
            f'It smiles at you and wants to join you in your adventure.')

    def _set_start_inventory(self):
        self._context.clear_inventory()
        self._context.add_item('Pita Fruit')
        self._context.add_item('Medicinal Herb')
