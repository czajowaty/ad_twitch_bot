from collections.abc import Mapping, Sequence
import json
from game.floor_descriptor import FloorDescriptor, Monster
from game.traits import UnitTraits, Genus, Talents, SpellTraits


class Config:
    class InvalidConfig(Exception):
        pass

    class Probabilities:
        def __init__(self):
            self.flee = 0.65

    class Levels:
        def __init__(self):
            self._experience_per_level = []

        @property
        def max_level(self) -> int:
            return len(self._experience_per_level)

        def add_level(self, experience_required: int):
            self._experience_per_level.append(experience_required)

        def experience_for_next_level(self, level: int) -> int:
            return self._experience_per_level[level]

    class SpecialUnitsTraits:
        def __init__(self):
            self.ghosh = UnitTraits()

    def __init__(self):
        self._probabilities = self.Probabilities()
        self._levels = self.Levels()
        self._monsters_traits = {}
        self._special_units_traits = self.SpecialUnitsTraits()
        self._floors = []

    @property
    def probabilities(self):
        return self._probabilities

    @property
    def levels(self):
        return self._levels

    @property
    def monsters_traits(self) -> Mapping[str, UnitTraits]:
        return self._monsters_traits

    @property
    def special_units_traits(self):
        return self._special_units_traits

    @property
    def floors(self) -> Sequence[FloorDescriptor]:
        return self._floors

    @property
    def highest_floor(self) -> int:
        return len(self._floors)

    @classmethod
    def from_file(cls, config_file_name) -> '__class__':
        with open(config_file_name) as config_file:
            return cls.from_json(config_file.read())

    @classmethod
    def from_json(cls, config_json_string) -> '__class__':
        config = Config()
        try:
            config_json = json.loads(config_json_string)
            cls._read_probabilities(config._probabilities, config_json['probabilities'])
            cls._read_levels(config._levels, config_json['experience_per_level'])
            config._monsters_traits = cls._create_monsters_traits(config_json['monsters'])
            config._special_units_traits = cls._create_special_units_traits(config_json['special_units'])
            config._floors = cls._create_floors(config_json['floors'])
        except json.JSONDecodeError as exc:
            raise cls.InvalidConfig(f"Invalid JSON: {exc}")
        except KeyError as exc:
            raise cls.InvalidConfig(f"Missing key: {exc}")
        cls._validate_config(config)
        return config

    @classmethod
    def _read_probabilities(cls, probabilities: '__class__.Probabilities', probabilities_json):
        try:
            probabilities.flee = float(probabilities_json['flee'])
        except ValueError as exc:
            raise cls.InvalidConfig(f"{probabilities_json}: {exc}")

    @classmethod
    def _read_levels(cls, levels: '__class__.Levels', levels_json):
        experience_for_prev_level = -1
        for level, experience_for_next_level in enumerate(levels_json, start=1):
            if experience_for_next_level <= experience_for_prev_level:
                raise cls.InvalidConfig(f'Experience required for LVL {level} is not greater than for LVL {level - 1}')
            levels.add_level(experience_for_next_level)
            experience_for_prev_level = experience_for_next_level

    @classmethod
    def _create_monsters_traits(cls, monsters_json):
        monsters_traits = {}
        for monster_json in monsters_json:
            monster_traits = cls._create_unit_traits(monster_json)
            if monster_traits.name in monsters_traits:
                raise cls.InvalidConfig(f"Double entry for monster '{monster_traits.name}' traits")
            monsters_traits[monster_traits.name] = monster_traits
        return monsters_traits

    @classmethod
    def _create_unit_traits(cls, unit_json):
        unit_traits = UnitTraits()
        try:
            unit_traits.name = unit_json['name']
            unit_traits.base_hp = unit_json['base_hp']
            unit_traits.hp_growth = unit_json['hp_growth']
            unit_traits.base_mp = unit_json['base_mp']
            unit_traits.mp_growth = unit_json['mp_growth']
            unit_traits.base_attack = unit_json['base_attack']
            unit_traits.attack_growth = unit_json['attack_growth']
            unit_traits.base_defense = unit_json['base_defense']
            unit_traits.defense_growth = unit_json['defense_growth']
            unit_traits.base_luck = unit_json['base_luck']
            unit_traits.luck_growth = unit_json['luck_growth']
            unit_traits.base_exp_given = unit_json['base_exp']
            unit_traits.exp_given_growth = unit_json['exp_growth']
            unit_traits.native_genus = cls._parse_genus(unit_json['element'])
            unit_traits.native_spell_traits = cls._parse_spell(unit_json.get('spell'))
            unit_traits.talents = cls._parse_talents(unit_json.get('talents'))
            unit_traits.is_evolved = unit_json.get('is_evolved', False)
        except KeyError as exc:
            raise cls.InvalidConfig(f"{unit_json}: missing key {exc}")
        except ValueError as exc:
            raise cls.InvalidConfig(f"{unit_json}: {exc}")
        return unit_traits

    @classmethod
    def _parse_genus(cls, genus_name):
        if genus_name == 'None':
            return Genus.Empty
        for genus in Genus:
            if genus.name == genus_name:
                return genus
        raise ValueError(f'Unknown genus "{genus_name}"')

    @classmethod
    def _parse_spell(cls, spell_name):
        if spell_name is None:
            return None
        spell_traits = SpellTraits()
        spell_traits.name = spell_name
        if spell_name == 'Brid':
            spell_traits.base_damage = 10
            spell_traits.genus = Genus.Fire
            spell_traits.mp_cost = 10
        elif spell_name == 'Breath':
            spell_traits.base_damage = 16
            spell_traits.genus = Genus.Fire
            spell_traits.mp_cost = 12
        elif spell_name == 'Sled':
            spell_traits.base_damage = 8
            spell_traits.genus = Genus.Fire
            spell_traits.mp_cost = 8
        elif spell_name == 'Rise':
            spell_traits.base_damage = 19
            spell_traits.genus = Genus.Fire
            spell_traits.mp_cost = 16
        elif spell_name == 'DeHeal':
            spell_traits.base_damage = 10
            spell_traits.genus = Genus.Water
            spell_traits.mp_cost = 10
        else:
            raise ValueError(f'Unknown spell name "{spell_name}"')
        return spell_traits

    @classmethod
    def _parse_talents(cls, talents_string):
        if talents_string is None:
            return Talents.Empty
        talents = Talents.Empty
        for talent_name in talents_string.split(','):
            talents |= cls._parse_talent(talent_name)
        return talents

    @classmethod
    def _parse_talent(cls, talent_name):
        for talent in Talents:
            if talent.name == talent_name:
                return talent
        raise ValueError(f'Unknown talent "{talent_name}"')

    @classmethod
    def _create_special_units_traits(cls, special_units_json):
        special_units_traits = cls.SpecialUnitsTraits()
        try:
            special_units_traits.ghosh = cls._create_unit_traits(special_units_json['ghosh'])
        except KeyError as exc:
            raise cls.InvalidConfig(f'Missing special units traits - {exc}')
        return special_units_traits

    @classmethod
    def _create_floors(cls, floors_json):
        floors = []
        for floor_json in floors_json:
            floors.append(cls._create_floor(floor_json))
        return floors

    @classmethod
    def _create_floor(cls, floor_json):
        floor = FloorDescriptor()
        try:
            for monster_json in floor_json:
                floor.add_monster(
                    Monster(monster_json['monster'], monster_json['level']),
                    monster_json['weight'])
        except KeyError as exc:
            raise cls.InvalidConfig(f"{floor_json}: missing key {exc}")
        return floor

    @classmethod
    def _validate_config(cls, config):
        cls._validate_probabilities(config)
        cls._validate_experience_per_level(config)
        cls._validate_floors(config)

    @classmethod
    def _validate_probabilities(cls, config):
        probabilities = config.probabilities
        cls._validate_probability('flee', probabilities.flee)

    @classmethod
    def _validate_probability(cls, name, probability):
        min_probability = 0.0
        max_probability = 1.0
        if probability < min_probability or probability > max_probability:
            raise cls.InvalidConfig(
                f'Probability "{name}"={probability} is outside range [{min_probability}-{max_probability}]')

    @classmethod
    def _validate_experience_per_level(cls, config):
        if config.levels.max_level == 0:
            raise cls.InvalidConfig(f'No levels defined')

    @classmethod
    def _validate_floors(cls, config):
        if config.highest_floor == 0:
            raise cls.InvalidConfig(f'No floors specified')
        for index, floor in enumerate(config.floors):
            if len(floor.monsters) == 0:
                raise cls.InvalidConfig(f'Floor at index {index} has no monsters')
            for monster in floor.monsters:
                if monster.name not in config.monsters_traits:
                    raise cls.InvalidConfig(f'Floor at index {index} has unknown monster "{monster.name}"')
