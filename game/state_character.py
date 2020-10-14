from .state_base import StateBase


class StateCharacterEvent(StateBase):
    def on_enter(self):
        character = self._select_character()
        encounter_handler = self.ENCOUNTERS[character]
        next_action, response = encounter_handler(self)
        self._context.add_response(f'You met {character}. {response}')
        self._context.generate_action(next_action)

    def _select_character(self):
        return self._context.rng.choice(list(self.ENCOUNTERS.keys()))

    def _handle_cherrl_encounter(self):
        return 'character_met', 'You are fully healed.'

    def _handle_nico_encounter(self):
        return 'character_met', 'You are cultured. You gain 100 channel points.'

    def _handle_patty_encounter(self):
        return 'character_met', 'Your familiar stats are boosted.'

    def _handle_fur_encounter(self):
        return 'item_exchange', 'She offers you an item exchange.'

    def _handle_selfi_encounter(self):
        return 'familiar_trade', 'She offers you a familiar trade.'

    def _handle_mia_encounter(self):
        return 'character_met', 'She gazes upon you while mumbling indefinitely...'

    def _handle_vivianne_encounter(self):
        return 'character_met', 'She started dancing.'

    def _handle_ghosh_encounter(self):
        return 'fight_ghosh', 'He wants to fight you!'

    def _handle_beldo_encounter(self):
        return 'battle_event', 'A strong monster appears!'

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
