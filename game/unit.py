import logging
from game.config import Config
from game.genus import Genus
from game.spell import Spell
from game.talents import Talents
from game.traits import UnitTraits
from game.stats_calculator import StatsCalculator


logger = logging.getLogger(__name__)


class Unit:
    def __init__(self, traits: UnitTraits, levels: Config.Levels):
        self._traits = traits
        self._levels = levels
        self.name = traits.name
        self.genus = traits.native_genus
        self.level = 1
        self._talents = traits.talents
        self.max_hp = traits.base_hp
        self.hp = self.max_hp
        self.max_mp = traits.base_mp
        self.mp = self.max_mp
        self.attack = traits.base_attack
        self.defense = traits.base_defense
        self.luck = traits.base_luck
        if traits.native_spell_traits is not None:
            self.spell = Spell(traits.native_spell_traits)
        else:
            self.spell = None
        self.exp = 0

    @property
    def traits(self):
        return self._traits

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def genus(self) -> Genus:
        return self._genus

    @genus.setter
    def genus(self, value: Genus):
        self._genus = value

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value):
        self._level = value

    def is_max_level(self) -> bool:
        return self.level >= self._levels.max_level

    @property
    def talents(self):
        return self._talents

    @property
    def max_hp(self):
        return self._max_hp

    @max_hp.setter
    def max_hp(self, value):
        self._max_hp = value

    @property
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, value):
        self._hp = value

    def is_hp_at_max(self) -> bool:
        return self.hp >= self.max_hp

    def is_dead(self) -> bool:
        return self.hp <= 0

    def restore_hp(self):
        self.hp = self.max_hp

    def deal_damage(self, damage):
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0

    @property
    def max_mp(self):
        return self._max_mp

    @max_mp.setter
    def max_mp(self, value):
        self._max_mp = value

    @property
    def mp(self):
        return self._mp

    @mp.setter
    def mp(self, value):
        self._mp = value

    def is_mp_at_max(self) -> bool:
        return self.mp >= self.max_mp

    def restore_mp(self):
        self.mp = self.max_mp

    def use_mp(self, mp_usage):
        self.mp -= mp_usage
        if self.mp < 0:
            self.mp = 0

    @property
    def attack(self):
        return self._attack

    @attack.setter
    def attack(self, value):
        self._attack = value

    @property
    def defense(self):
        return self._defense

    @defense.setter
    def defense(self, value):
        self._defense = value

    @property
    def luck(self):
        return self._luck

    @luck.setter
    def luck(self, value):
        self._luck = value

    @property
    def spell(self) -> Spell:
        return self._spell

    @spell.setter
    def spell(self, value: Spell):
        self._spell = value

    def has_spell(self) -> bool:
        return self.spell is not None

    @property
    def spell_mp_cost(self) -> int:
        return self.spell.traits.mp_cost

    def has_enough_mp_for_spell(self) -> bool:
        return self.mp >= self.spell_mp_cost

    @property
    def exp(self):
        return self._exp

    @exp.setter
    def exp(self, value):
        self._exp = value

    def gain_exp(self, gained_exp) -> bool:
        has_leveled_up = False
        if self.is_max_level():
            return has_leveled_up
        self.exp += gained_exp
        while not self.is_max_level() and self.exp >= self.experience_for_next_level():
            has_leveled_up = True
            self._level_up()
        return has_leveled_up

    def experience_for_next_level(self) -> int:
        if self.is_max_level():
            return 0
        return self._levels.experience_for_next_level(self.level)

    def _level_up(self):
        self.level += 1
        self._increase_hp_on_level_up()
        self._increase_mp_on_level_up()
        self._increase_attack_on_level_up()
        self._increase_defense_on_level_up()
        self._increase_luck_on_level_up()
        self._increase_spell_level_on_level_up()

    def _increase_hp_on_level_up(self):
        hp_increase = self._stats_calculator().hp_increase(self.level)
        if self.talents.has(Talents.HpIncreased):
            hp_increase *= 2
        self.max_hp += hp_increase
        self.hp += hp_increase

    def _increase_mp_on_level_up(self):
        mp_increase = self._stats_calculator().mp_increase(self.level)
        if self.talents.has(Talents.MpIncreased):
            mp_increase *= 2
        self.max_mp += mp_increase
        self.mp += mp_increase

    def _increase_attack_on_level_up(self):
        attack_increase = self._stats_calculator().attack_increase(self.level)
        if self.talents.has(Talents.StrengthIncreased):
            attack_increase *= 2
        self.attack += attack_increase

    def _increase_defense_on_level_up(self):
        defense_increase = self._stats_calculator().defense_increase(self.level)
        if self.talents.has(Talents.Hard):
            defense_increase *= 2
        self.defense += defense_increase

    def _increase_luck_on_level_up(self):
        self.luck += self._stats_calculator().luck_increase(self.level)

    def _increase_spell_level_on_level_up(self):
        if not self.has_spell():
            return
        if self.spell.traits.genus != self.genus:
            return
        spell_level_increase = 1
        if self.talents.has(Talents.MagicAttackIncreased):
            spell_level_increase *= 2
        self.spell.level += spell_level_increase
        if self.spell.level < self.level:
            self.spell.level += spell_level_increase
            self.spell.level = min(self.spell.level, self.level)

    def _stats_calculator(self) -> StatsCalculator:
        return StatsCalculator(self.traits)

    def to_string(self) -> str:
        return f'{self.name} - {self.stats_to_string()}'

    def stats_to_string(self) -> str:
        s = f'genus: {self._genus_to_string()}, talents: {self._talents_to_string()}, LVL: {self.level}, ' \
            f'HP: {self.hp}/{self.max_hp}, MP: {self.mp}/{self.max_mp}, ' \
            f'ATK: {self.attack}, DEF: {self.defense}, LUCK: {self.luck}'
        if self.has_spell():
            s += f', spell: LVL {self.spell.level} {self.spell.traits.name} (MP cost: {self.spell_mp_cost})'
        s += f', EXP: {self.exp}'
        if not self.is_max_level():
            s += f' ({self.experience_for_next_level() - self.exp} more EXP to next LVL)'
        return s

    def _genus_to_string(self) -> str:
        if self.genus is Genus.Empty:
            return '-'
        else:
            return self.genus.name

    def _talents_to_string(self) -> str:
        if self.talents is Talents.Empty:
            return '-'
        else:
            return ', '.join(talent.name for talent in Talents.all() if self.talents.has(talent))
