from .genus import Genus
from .talents import Talents


class UnitTraits:
    def __init__(self):
        self.name = ''
        self.base_hp = 0
        self.hp_growth = 0
        self.base_mp = 0
        self.mp_growth = 0
        self.base_attack = 0
        self.attack_growth = 0
        self.base_defense = 0
        self.defense_growth = 0
        self.base_exp_given = 0
        self.exp_given_growth = 0
        self.native_genus = Genus.Empty
        self.native_spell_traits = None
        self.talents = Talents.Empty
        self.is_evolved = False


class SpellTraits:
    def __init__(self):
        self.name = ''
        self.base_damage = 0
        self.genus = Genus.Empty
