from game import commands
from game.damage_calculator import DamageCalculator
from game.state_base import StateBase
from game.state_machine_context import StateMachineContext
from game.stats_calculator import StatsCalculator
from game.state_machine_context import BattleContext
from game.unit import Unit

DamageRoll = DamageCalculator.DamageRoll
RelativeHeight = DamageCalculator.RelativeHeight


class StateBattleEvent(StateBase):
    def on_enter(self):
        monster = self._context.generate_monster(floor=self._context.floor)
        self._context.generate_action(commands.START_BATTLE, monster)


class StateStartBattle(StateBase):
    def __init__(self, context, enemy: Unit):
        super().__init__(context)
        self._enemy = enemy

    def on_enter(self):
        enemy = self._enemy
        self._context.add_response(
            f"You encountered LVL {enemy.level} {enemy.name} ({enemy.hp} HP).")
        self._context.start_battle(self._enemy)
        self._context.generate_action(commands.BATTLE_STARTED)


class StateBattleBase(StateBase):
    @property
    def _battle_context(self) -> BattleContext:
        return self._context.battle_context

    def _is_enemy_dead(self) -> bool:
        return self._battle_context.enemy.is_dead()

    def _is_familiar_dead(self) -> bool:
        return self._context.familiar.is_dead()

    def _is_battle_finished(self) -> bool:
        return self._battle_context.is_finished() or self._is_enemy_dead() or self._is_familiar_dead()

    def _perform_physical_attack(self, attacker: Unit, defender: Unit):
        if not self._is_physical_attack_accurate(attacker):
            return self._physical_attack_miss_response(attacker, defender)
        else:
            damage_calculator = DamageCalculator(attacker, defender)
            relative_height = self._select_relative_height(attacker)
            is_critical = self._select_whether_attack_is_critical(attacker)
            damage = damage_calculator.physical_damage(self._select_damage_roll(), relative_height, is_critical)
            defender.deal_damage(damage)
            physical_attack_descriptor = damage, relative_height, is_critical
            return self._physical_attack_hit_response(attacker, defender, physical_attack_descriptor)

    def _perform_spell_attack(self, attacker: Unit, defender: Unit):
        damage = DamageCalculator(attacker, defender).spell_damage()
        defender.deal_damage(damage)
        attacker.use_mp(attacker.spell.traits.mp_cost)
        return self._spell_attack_response(attacker, defender, damage)

    def _is_physical_attack_accurate(self, attacker: Unit):
        if attacker.luck <= 0:
            return False
        else:
            hit_chance = attacker.luck - 1 / attacker.luck
            return self._context.does_action_succeed(success_chance=hit_chance)

    def _select_damage_roll(self) -> DamageRoll:
        return self._context.rng.choices([DamageRoll.Low, DamageRoll.Normal, DamageRoll.High], weights=[1, 2, 1])[0]

    def _select_relative_height(self, attacker: Unit) -> RelativeHeight:
        # TODO: Check from attacker status
        return DamageCalculator.RelativeHeight.Same

    def _select_whether_attack_is_critical(self, attacker: Unit) -> bool:
        crit_chance = (attacker.luck // 64 + 1) / 128
        return self._context.does_action_succeed(success_chance=crit_chance)

    def _physical_attack_miss_response(self, attacker: Unit, defender: Unit):
        def is_familiar_attack() -> bool:
            return attacker is self._context.familiar

        response = 'You try' if is_familiar_attack() else f'{attacker.name} tries'
        response += ' to hit '
        response += f'{defender.name}' if is_familiar_attack() else 'you'
        response += ', but '
        response += 'it' if is_familiar_attack() else f'you'
        response += ' dodge'
        if is_familiar_attack():
            response += 's'
        response += ' swiftly.'
        return response

    def _physical_attack_hit_response(self, attacker: Unit, defender: Unit, physical_attack_descriptor):
        def is_familiar_attack() -> bool:
            return attacker is self._context.familiar

        def attacker_name() -> str:
            return 'you' if is_familiar_attack() else attacker.name

        def defender_name() -> str:
            return defender.name if is_familiar_attack() else 'you'

        damage, relative_height, is_critical = physical_attack_descriptor
        response = f'{attacker_name().capitalize()} hit'
        if not is_familiar_attack():
            response += 's'
        response += ' '
        if is_critical:
            response += 'hard '
        if relative_height is RelativeHeight.Higher:
            response += 'from above '
        elif relative_height is RelativeHeight.Lower:
            response += 'from below '
        response += f'dealing {damage} damage. {defender_name().capitalize()} '
        response += 'has' if is_familiar_attack() else 'have'
        response += f' {defender.hp} HP left.'
        return response

    def _spell_attack_response(self, attacker: Unit, defender: Unit, damage: int):
        def is_familiar_attack() -> bool:
            return attacker is self._context.familiar

        def attacker_name() -> str:
            return 'you' if is_familiar_attack() else attacker.name

        def defender_name() -> str:
            return defender.name if is_familiar_attack() else 'you'

        response = f'{attacker_name().capitalize()} cast'
        if not is_familiar_attack():
            response += 's'
        response += f' {attacker.spell.traits.name} '
        response += f'dealing {damage} damage. {defender_name().capitalize()} '
        response += 'has' if is_familiar_attack() else 'have'
        response += f' {defender.hp} HP left.'
        return response


class StateBattle(StateBattleBase):
    def on_enter(self):
        if self._is_battle_finished():
            if self._is_enemy_dead():
                self._handle_enemy_defeated()
            self._context.finish_battle()
            if self._is_familiar_dead():
                self._context.add_response("You died...")
                self._context.generate_action(commands.YOU_DIED)
            else:
                self._context.generate_action(commands.EVENT_FINISHED)
        else:
            self._select_next_one_to_act()
            if self._battle_context.is_player_turn:
                self._context.generate_action(commands.PLAYER_TURN)
            else:
                self._context.generate_action(commands.ENEMY_TURN)

    def _handle_enemy_defeated(self):
        enemy = self._battle_context.enemy
        response = f'You defeated {enemy.name}'
        familiar = self._context.familiar
        if not familiar.is_max_level():
            gained_exp = self._calculate_gained_exp()
            response += f' and gained {gained_exp} EXP.'
            has_leveled_up = familiar.gain_exp(gained_exp)
            if has_leveled_up:
                response += f' You leveled up! Your new stats - {familiar.stats_to_string()}.'
        else:
            response += '.'
        self._context.add_response(response)

    def _calculate_gained_exp(self):
        enemy = self._battle_context.enemy
        given_experience = StatsCalculator(enemy.traits).given_experience(enemy.level)
        if enemy.level > self._context.familiar.level:
            given_experience *= 2
        return given_experience

    def _select_next_one_to_act(self):
        self._battle_context.is_player_turn = not self._battle_context.is_player_turn


class StateBattlePlayerTurn(StateBattleBase):
    def on_enter(self):
        self._context.add_response(f"Your turn.")


class StateBattleAttack(StateBattleBase):
    def on_enter(self):
        familiar = self._context.familiar
        enemy = self._battle_context.enemy
        response = self._perform_physical_attack(attacker=familiar, defender=enemy)
        self._context.add_response(response)
        self._context.generate_action(commands.BATTLE_ACTION_PERFORMED)


class StateBattleUseSpell(StateBattleBase):
    def on_enter(self):
        familiar = self._context.familiar
        if not familiar.has_spell():
            self._context.add_response("You do not have a spell.")
            self._context.generate_action(commands.CANNOT_USE_SPELL)
        elif not familiar.has_enough_mp_for_spell():
            self._context.add_response("You do not have enough MP.")
            self._context.generate_action(commands.CANNOT_USE_SPELL)
        else:
            response = self._perform_spell_attack(attacker=familiar, defender=self._battle_context.enemy)
            self._context.add_response(response)
            self._context.generate_action(commands.BATTLE_ACTION_PERFORMED)

    @classmethod
    def _verify_preconditions(cls, context, parsed_args):
        familiar = context.familiar
        if not familiar.has_spell():
            raise cls.PreConditionsNotMet('You do not have a spell.')
        if not familiar.has_enough_mp_for_spell():
            raise cls.PreConditionsNotMet('You do not have enough MP.')


class StateBattleUseItem(StateBattleBase):
    def __init__(self, context: StateMachineContext, item_index: int):
        super().__init__(context)
        self._item_index = item_index

    def on_enter(self):
        item = self._context.inventory.peek_item(self._item_index)
        can_use, reason = item.can_use(self._context)
        if not can_use:
            self._context.add_response(f"You cannot use {item.name}. {reason}")
            self._context.generate_action(commands.CANNOT_USE_ITEM)
        else:
            item.use(self._context)
            self._context.inventory.take_item(self._item_index)
            self._context.generate_action(commands.BATTLE_ACTION_PERFORMED)

    @classmethod
    def _parse_args(cls, context: StateMachineContext, args):
        if len(args) < 1:
            raise cls.ArgsParseError('You need to specify item to use.')
        item_name = ''.join(args)
        try:
            index, _ = context.inventory.find_item(item_name)
        except ValueError:
            raise cls.ArgsParseError(f'You do not have "{item_name}" in your inventory.')
        return (index,)


class StateBattleTryToFlee(StateBattleBase):
    def on_enter(self):
        if self._context.does_action_succeed(success_chance=self.game_config.probabilities.flee):
            self._battle_context.finish_battle()
            self._context.add_response("You successfully fleed from the battle.")
        else:
            self._context.add_response("You attempted to flee from the battle, but monster caught up with you.")
        self._context.generate_action(commands.BATTLE_ACTION_PERFORMED)


class StateBattleEnemyTurn(StateBattleBase):
    def on_enter(self):
        familiar = self._context.familiar
        enemy = self._battle_context.enemy
        response = self._perform_physical_attack(attacker=enemy, defender=familiar)
        self._context.add_response(response)
        self._context.generate_action(commands.BATTLE_ACTION_PERFORMED)
