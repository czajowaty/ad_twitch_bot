from collections.abc import Mapping, Sequence
import json
from .floor_descriptor import FloorDescriptor, Monster
from .traits import UnitTraits, Genus, Talents, SpellTraits


class Config:
    class InvalidConfig(Exception):
        pass

    def __init__(self):
        self._units_traits = {}
        self._floors = []

    @property
    def units_traits(self) -> Mapping[str, UnitTraits]:
        return self._units_traits

    @property
    def floors(self) -> Sequence[FloorDescriptor]:
        return self._floors

    @classmethod
    def from_file(cls, config_file_name) -> '__class__':
        with open(config_file_name) as config_file:
            return cls.from_json(config_file.read())

    @classmethod
    def from_json(cls, config_json_string) -> '__class__':
        config = Config()
        try:
            config_json = json.loads(config_json_string)
            config._units_traits = cls._create_units_traits(config_json['units'])
            config._floors = cls._create_floors(config_json['floors'])
        except json.JSONDecodeError as exc:
            raise cls.InvalidConfig(f"Invalid JSON: {exc}")
        except KeyError as exc:
            raise cls.InvalidConfig(f"Missing key: {exc}")
        cls._validate_config(config)
        return config

    @classmethod
    def _create_units_traits(cls, units_json):
        units_traits = {}
        for unit_json in units_json:
            unit_traits = cls._create_unit_traits(unit_json)
            if unit_traits.name in units_traits:
                raise cls.InvalidConfig(f"Double entry for unit '{unit_traits.name}' traits")
            units_traits[unit_traits.name] = unit_traits
        return units_traits

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
        elif spell_name == 'Breath':
            spell_traits.base_damage = 16
            spell_traits.genus = Genus.Fire
        elif spell_name == 'Sled':
            spell_traits.base_damage = 8
            spell_traits.genus = Genus.Fire
        elif spell_name == 'Rise':
            spell_traits.base_damage = 19
            spell_traits.genus = Genus.Fire
        elif spell_name == 'DeHeal':
            spell_traits.base_damage = 10
            spell_traits.genus = Genus.Water
        else:
            raise ValueError(f'Unknown spell name "{spell_name}"')
        return spell_traits

    @classmethod
    def _parse_talents(cls, talents_string):
        if talents_string is None:
            return Talents.Empty
        return [cls._parse_talent(talent_name) for talent_name in talents_string.split(',')]

    @classmethod
    def _parse_talent(cls, talent_name):
        for talent in Talents:
            if talent.name == talent_name:
                return talent
        raise ValueError(f'Unknown talent "{talent_name}"')

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
        cls._validate_floors(config)

    @classmethod
    def _validate_floors(cls, config):
        floors = config.floors
        if len(floors) == 0:
            raise cls.InvalidConfig(f"No floors specified")
        for index, floor in enumerate(floors):
            if len(floor.monsters) == 0:
                raise cls.InvalidConfig(f"Floor at index {index} has no monsters")
            for monster in floor.monsters:
                if monster.name not in config.units_traits:
                    raise cls.InvalidConfig(f"Floor at index {index} has unknown monster '{monster.name}'")
