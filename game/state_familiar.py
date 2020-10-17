from game import commands
from game.state_base import StateBase
from game.state_with_monster import StateWithMonster
from game.unit_creator import UnitCreator


class StateFamiliarEvent(StateWithMonster):
    def on_enter(self):
        met_familiar = self._select_familiar()
        self._context.buffer_unit(met_familiar)
        self._context.add_response(
            f"You come across a lonely {met_familiar.name} ({met_familiar.stats_to_string()}). "
            "It looks like it wants to join you. But you already have a familiar...")

    def _select_familiar(self):
        monsters_traits = self._context.game_config.monsters_traits
        familiar_name = self._monster_name or self._context.rng.choice(list(monsters_traits.keys()))
        current_familiar = self._context.familiar
        return UnitCreator(monsters_traits[familiar_name]) \
            .create(level=current_familiar.level, levels=self.game_config.levels)


class StateMetFamiliarIgnore(StateBase):
    def on_enter(self):
        met_familiar = self._context.take_buffered_unit()
        self._context.add_response(f"As you are walking away you can see {met_familiar.name}'s sad face.")
        self._context.generate_action(commands.EVENT_FINISHED)


class StateFamiliarFusion(StateBase):
    def on_enter(self):
        met_familiar = self._context.take_buffered_unit()
        current_familiar = self._context.familiar
        current_familiar.fuse(met_familiar)
        self._context.add_response(
            f"Fusion of {current_familiar.name} and {met_familiar.name} results in {current_familiar.to_string()}.")
        self._context.generate_action(commands.EVENT_FINISHED)


class StateFamiliarReplacement(StateBase):
    def on_enter(self):
        met_familiar = self._context.take_buffered_unit()
        current_familiar = self._context.familiar
        self._context.familiar = met_familiar
        self._context.add_response(
            f"You took {met_familiar.name} with you, leaving sad {current_familiar.name} behind.")
        self._context.generate_action(commands.EVENT_FINISHED)
