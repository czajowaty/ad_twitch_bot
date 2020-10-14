import logging
from .genus import Genus
from .spell import Spell
from .traits import UnitTraits

logger = logging.getLogger(__name__)


class Unit:
    def __init__(self, traits: UnitTraits):
        self._traits = traits
        self.name = traits.name
        self.genus = traits.native_genus
        self.level = 1
        self.max_hp = traits.base_hp
        self.hp = self.max_hp
        self.max_mp = traits.base_mp
        self.mp = self.max_mp
        self.attack = traits.base_attack
        self.defense = traits.base_defense
        if traits.native_spell_traits is not None:
            self.spell = Spell(traits.native_spell_traits)
        else:
            self.spell = None

    def has_spell(self) -> bool:
        return self.spell is not None

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

    def is_dead(self) -> bool:
        return self.hp <= 0

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
    def spell(self) -> Spell:
        return self._spell

    @spell.setter
    def spell(self, value: Spell):
        self._spell = value
