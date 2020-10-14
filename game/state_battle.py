from game import floor_descriptor, commands
from game.damage_calculator import DamageCalculator
from game.state_base import StateBase
from game.unit_creator import UnitCreator
from game.state_machine_context import BattleContext


class StateBattleEvent(StateBase):
    def on_enter(self):
        monster = self._generate_enemy_monster()
        monster_traits = self._context.game_config.units_traits[monster.name]
        monster = UnitCreator(monster_traits).create(monster.level)
        self._context.add_response(
            f"You encountered LVL {monster.level} {monster.name} ({monster.hp} HP).")
        self._context.start_battle(monster)
        self._context.generate_action(commands.BATTLE_STARTED)

    def _generate_enemy_monster(self) -> floor_descriptor.Monster:
        floor = self._context.game_config.floors[self._context.floor]
        return self._context.rng.choices(floor.monsters, floor.weights)[0]


class StateBattleBase(StateBase):
    @property
    def _battle_context(self) -> BattleContext:
        return self._context.battle_context

    def _is_enemy_dead(self) -> bool:
        return self._battle_context.enemy.is_dead()

    def _is_familiar_dead(self) -> bool:
        return self._context.familiar.is_dead()

    def _is_battle_finished(self) -> bool:
        return self._is_enemy_dead() or self._is_familiar_dead()


class StateBattle(StateBattleBase):
    def on_enter(self):
        if self._is_battle_finished():
            if self._is_enemy_dead():
                self._context.add_response("You defeated a monster!")
            elif self._is_familiar_dead():
                self._context.add_response("You died...")
            self._context.finish_battle()
            self._context.generate_action(commands.EVENT_FINISHED)
        else:
            self._select_next_one_to_act()
            if self._battle_context.is_player_turn:
                self._context.generate_action(commands.PLAYER_TURN)
            else:
                self._context.generate_action(commands.ENEMY_TURN)

    def _select_next_one_to_act(self):
        self._battle_context.is_player_turn = not self._battle_context.is_player_turn


class StateBattlePlayerTurn(StateBattleBase):
    def on_enter(self):
        self._context.add_response(f"Your turn.")


class StateBattleAttack(StateBattleBase):
    def on_enter(self):
        familiar = self._context.familiar
        enemy = self._battle_context.enemy
        calc = DamageCalculator(familiar, enemy)
        damage = calc.physical_damage(False)
        self._battle_context.enemy.deal_damage(damage)
        self._context.add_response(f"You dealt {damage} damage. {enemy.name} has {enemy.hp} HP left.")
        self._context.generate_action(commands.BATTLE_ACTION_PERFORMED)


class StateBattleUseSpell(StateBattleBase):
    pass


class StateBattleUseItem(StateBattleBase):
    pass


class StateBattleTryToFlee(StateBattleBase):
    def on_enter(self):
        if self._context.does_action_succeed(success_chance=0.65):
            self._context.add_response("You fleed from the battle.")
            self._context.finish_battle()
            self._context.generate_action(commands.EVENT_FINISHED)
        else:
            self._context.add_response("You attempted to flee from the battle, but monster caught up with you.")
            self._context.generate_action(commands.BATTLE_ACTION_PERFORMED)


class StateBattleEnemyTurn(StateBattleBase):
    def on_enter(self):
        familiar = self._context.familiar
        enemy = self._battle_context.enemy
        calc = DamageCalculator(enemy, familiar)
        damage = calc.physical_damage(False)
        self._context.familiar.hp -= damage
        self._context.add_response(f"{enemy.name} dealt {damage} damage. You have {familiar.hp} HP left.")
        self._context.generate_action(commands.BATTLE_ACTION_PERFORMED)
