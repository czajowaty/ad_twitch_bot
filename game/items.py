from game.errors import InvalidOperation


class Item:
    @property
    def name(self) -> str:
        raise NotImplementedError(f'{self.__class__.__name__}.name')

    def can_use(self, context) -> bool:
        raise NotImplementedError(f'{self.__class__.__name__}.{self.can_use}')

    def use(self, context) -> str:
        can_use, reason = self.can_use(context)
        if not can_use:
            raise InvalidOperation(f'Cannot use {self.name}. {reason}')
        effect = self._use(context)
        context.add_response(f"You used {self.name}. {effect}")

    def _use(self, context) -> str:
        raise NotImplementedError(f"{self.__class__.__name__}.{self.use}")


class Pita(Item):
    @property
    def name(self) -> str:
        return 'Pita'

    def can_use(self, context) -> (bool, str):
        if context.familiar.is_mp_at_max():
            return False, 'Your MP is already at max.'
        else:
            return True, ''

    def _use(self, context) -> str:
        context.familiar.restore_mp()
        return 'Your MP has been restored to max.'


class BattleOnlyItem(Item):
    def can_use(self, context) -> bool:
        if not context.is_in_battle():
            return False, 'You are not in battle.'
        else:
            return True, ''


class Oleem(BattleOnlyItem):
    @property
    def name(self) -> str:
        return 'Oleem'

    def _use(self, context) -> bool:
        context.battle_context.finish_battle()
        return 'Monster disappeared.'


class HolyScroll(BattleOnlyItem):
    @property
    def name(self) -> str:
        return 'Holy Scroll'

    def _use(self, context) -> str:
        # TODO: Implement adding the status
        return 'You are invulnerable for next 3 turns.'


class MedicinalHerb(Item):
    @property
    def name(self) -> str:
        return 'Medicinal Herb'

    def can_use(self, context) -> bool:
        if context.familiar.is_hp_at_max():
            return False, 'Your HP is already at max.'
        else:
            return True, ''

    def _use(self, context) -> str:
        context.familiar.restore_hp()
        return 'Your HP has been restored to max.'


class CureAllHerb(Item):
    @property
    def name(self) -> str:
        return 'Cure-All Herb'

    def can_use(self, context) -> bool:
        if True:  # TODO: Check if unit has negative status
            return False, 'You do not have any negative statuses.'
        else:
            return True, ''

    def _use(self, context) -> str:
        # TODO: heal negative statuses
        return 'You no longer have any negative statuses.'


class FireBall(BattleOnlyItem):
    @property
    def name(self) -> str:
        return 'Fire Ball'

    def _use(self, context) -> str:
        damage = context.battle_context.enemy.max_hp // 2
        enemy = context.battle_context.enemy
        enemy.deal_damage(damage)
        return f'Flames of {self.name} dealt {damage} damage. {enemy.name} has {enemy.hp} HP left.'


class WaterBall(Item):
    @property
    def name(self) -> str:
        return 'Water Ball'

    def can_use(self, context) -> bool:
        familiar = context.familiar
        if familiar.is_hp_at_max() and familiar.is_mp_at_max():
            return False, 'Your HP and MP is already at max.'
        else:
            return True, ''

    def _use(self, context) -> str:
        familiar = context.familiar
        familiar.restore_hp()
        familiar.restore_mp()
        return 'Your HP and MP and has been restored to max.'


def all_items():
    return [Pita(), Oleem(), HolyScroll(), MedicinalHerb(), CureAllHerb(), FireBall(), WaterBall()]
