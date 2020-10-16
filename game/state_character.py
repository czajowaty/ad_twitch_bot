from game import commands, items
from game.state_base import StateBase
from game.unit import Unit
from game.unit_creator import UnitCreator
from game.state_with_inventory_item import StateWithInventoryItem
from game.statuses import Statuses


class StateCharacterEvent(StateBase):
    def __init__(self, context, character=None):
        super().__init__(context)
        self._character = character

    def on_enter(self):
        character = self._select_character()
        encounter_handler = self.ENCOUNTERS[character]
        (next_command, args), response = encounter_handler(self)
        self._context.add_response(f'You met {character}. {response}')
        self._context.generate_action(next_command, *args)

    def _select_character(self):
        return self._character or self._context.rng.choice(list(self.ENCOUNTERS.keys()))

    def _handle_cherrl_encounter(self):
        familiar = self._context.familiar
        familiar.restore_hp()
        familiar.restore_mp()
        return (commands.EVENT_FINISHED, ()), 'You are fully healed.'

    def _handle_nico_encounter(self):
        return (commands.EVENT_FINISHED, ()), 'You are cultured. You gain 100 channel points.'

    def _handle_patty_encounter(self):
        self._context.familiar.set_status(Statuses.StatsBoost)
        return (commands.EVENT_FINISHED, ()), \
            'You immediately catch the scent of amazing curry that she carries. ' \
            'You gobble it without hesitation. You feel much stronger and sooo ready for the next battle.'

    def _handle_fur_encounter(self):
        if self.inventory.is_empty():
            return (commands.EVENT_FINISHED, ()), \
                'She wanted to offer you an item exchange, but you don\'t have any items... ' \
                'She finds you very uninteresting and leaves with a grumpy face.'
        else:
            item = self._context.rng.choice(items.all_items())
            self._context.buffer_item(item)
            return (commands.START_ITEM_TRADE, ()), 'She offers you an item exchange.'

    def _handle_selfi_encounter(self):
        familiar_for_trade_traits = self._context.familiar.traits
        while familiar_for_trade_traits.name == self._context.familiar.traits.name:
            familiar_for_trade_traits = self._context.rng.choice(list(self.game_config.monsters_traits.values()))
        familiar_for_trade = UnitCreator(familiar_for_trade_traits).create(self._context.familiar.level)
        familiar_for_trade.exp = self._context.familiar.exp
        return (commands.START_FAMILIAR_TRADE, (familiar_for_trade,)), 'She offers you a familiar trade.'

    def _handle_mia_encounter(self):
        return (commands.EVENT_FINISHED, ()), 'She gazes upon you while mumbling indefinitely. You leave her alone...'

    def _handle_vivianne_encounter(self):
        return (commands.EVENT_FINISHED, ()), 'She started dancing. After a while you leave.'

    def _handle_ghosh_encounter(self):
        ghosh_traits = self.game_config.special_units_traits.ghosh
        ghosh = UnitCreator(ghosh_traits).create(self._context.familiar.level)
        return (commands.START_BATTLE, (ghosh,)), 'He wants to fight you!'

    def _handle_beldo_encounter(self):
        floor = min(self._context.floor + 1, self.game_config.highest_floor)
        monster = self._context.generate_monster(floor, level_increase=1)
        return (commands.START_BATTLE, (monster,)), \
            'He is accompanied by a strong monster, which takes its interest in you... ' \
            'Beldo leaves laughing maniacally.'

    ENCOUNTERS = {
        'Cherrl': _handle_cherrl_encounter,
        'Nico': _handle_nico_encounter,
        'Patty': _handle_patty_encounter,
        'Fur': _handle_fur_encounter,
        'Selfi': _handle_selfi_encounter,
        'Mia': _handle_mia_encounter,
        'Vivianne': _handle_vivianne_encounter,
        'Ghosh': _handle_ghosh_encounter,
        'Beldo': _handle_beldo_encounter
    }

    @classmethod
    def _parse_args(cls, context, args):
        if len(args) == 0:
            return ()
        character = args[0].lower().capitalize()
        if character not in cls.ENCOUNTERS.keys():
            raise cls.ArgsParseError('Unknown character')
        return character,


class StateItemTrade(StateBase):
    def on_enter(self):
        inventory_string = ', '.join(self._context.inventory.items)
        item = self._context.peek_buffered_item()
        self._context.add_response(f"You have: {inventory_string}. Fur offers {item.name}. Do you want to trade?")


class StateItemTradeAccepted(StateWithInventoryItem):
    def on_enter(self):
        self._context.inventory.take_item(self._item_index)
        self._context.inventory.add_item(self._context.take_buffered_item())
        self._context.add_response(
            "Fur is very happy with what she got. She leaves with a smug smile on her face. "
            "Maybe you made a mistake...")
        self._context.generate_action(commands.EVENT_FINISHED)


class StateItemTradeRejected(StateBase):
    def on_enter(self):
        self._context.add_response(f"Fur leaves looking a bit mad. Maybe you made a mistake...")
        self._context.generate_action(commands.EVENT_FINISHED)


class StateFamiliarTrade(StateBase):
    def __init__(self, context, familiar_for_trade: Unit):
        super().__init__(context)
        self._familiar_for_trade = familiar_for_trade

    def on_enter(self):
        self._context.set_familiar_for_trade(self._familiar_for_trade)
        familiar = self._context.familiar
        self._context.add_response(
            f"You have: {familiar.to_string()}. Selfi offers {self._familiar_for_trade.to_string()}. "
            "Do you want to trade?")


class StateFamiliarTradeAccepted(StateBase):
    def on_enter(self):
        self._context.familiar = self._context.take_familiar_for_trade()
        self._context.add_response(
            "Selfi hapilly says \"Thank you, Puffy Lips!\" and quickly walks away with your familiar.")
        self._context.generate_action(commands.EVENT_FINISHED)


class StateFamiliarTradeRejected(StateBase):
    def on_enter(self):
        self._context.add_response(
            "Selfi turns around and leaves immediately. From afar you can hear her saying \"Stupid, Puffy Lips...\".")
        self._context.generate_action(commands.EVENT_FINISHED)
