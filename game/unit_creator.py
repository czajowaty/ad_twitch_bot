from game.config import Config
from game.spell import Spell
from game.stats_calculator import StatsCalculator
from game.traits import UnitTraits
from game.unit import Unit


class UnitCreator:
    def __init__(self, unit_traits: UnitTraits):
        self._unit_traits = unit_traits
        self._spell = None

    def set_spell(self, spell: Spell):
        # TODO: probably change it to SpellTraits
        self._spell = spell
        return self

    def create(self, level, levels: Config.Levels=Config.Levels()) -> Unit:
        # TODO: think about talents
        stats_calculator = StatsCalculator(self._unit_traits)
        unit = Unit(self._unit_traits, levels)
        unit.level = level
        unit.max_hp = stats_calculator.hp(level)
        unit.hp = unit.max_hp
        unit.max_mp = stats_calculator.mp(level)
        unit.mp = unit.max_mp
        unit.attack = stats_calculator.attack(level)
        unit.defense = stats_calculator.defense(level)
        unit.luck = stats_calculator.luck(level)
        if self._spell is not None:
            unit.spell = self._spell
        return unit
