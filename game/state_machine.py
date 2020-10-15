import logging
from game import commands
from game.errors import InvalidOperation
from game.state_base import StateBase
from game.state_battle import StateBattleEvent, StateBattle, StateStartBattle, StateBattlePlayerTurn, \
    StateBattleAttack, StateBattleUseSpell, StateBattleUseItem, StateBattleTryToFlee, StateBattleEnemyTurn
from game.state_character import StateCharacterEvent, StateItemTrade, StateItemTradeAccepted, StateItemTradeRejected, \
    StateFamiliarTrade, StateFamiliarTradeAccepted, StateFamiliarTradeRejected
from game.state_initialize import StateInitialize
from game.state_item import StateItemEvent
from game.state_machine_action import StateMachineAction
from game.state_machine_context import StateMachineContext
from game.state_trap import StateTrapEvent
from game.state_wait_for_event import StateWaitForEvent

logger = logging.getLogger(__name__)


class Transition:
    def __init__(self, nextState: StateBase, guard):
        self.nextState = nextState
        self.guard = guard

    @classmethod
    def _action_by_admin_guard(cls, action):
        return action.is_given_by_admin

    @classmethod
    def _no_guard(cls, action):
        return True

    @classmethod
    def by_admin(cls, nextState: StateBase):
        return Transition(nextState, guard=cls._action_by_admin_guard)

    @classmethod
    def by_user(cls, nextState):
        return Transition(nextState, guard=cls._no_guard)


class StateStart(StateBase):
    pass


class StateGameOver(StateBase):
    def on_enter(self):
        self._context.generate_action(commands.RESTART)


class StateMachine:
    TRANSITIONS = {
        StateStart: {commands.STARTED: Transition.by_admin(StateInitialize)},
        StateInitialize: {commands.INITIALIZED: Transition.by_admin(StateWaitForEvent)},
        StateWaitForEvent: {
            commands.BATTLE_EVENT: Transition.by_admin(StateBattleEvent),
            commands.ITEM_EVENT: Transition.by_admin(StateItemEvent),
            commands.TRAP_EVENT: Transition.by_admin(StateTrapEvent),
            commands.CHARACTER_EVENT: Transition.by_admin(StateCharacterEvent)
        },
        StateBattleEvent: {commands.START_BATTLE: Transition.by_admin(StateStartBattle)},
        StateStartBattle: {commands.BATTLE_STARTED: Transition.by_admin(StateBattle)},
        StateBattle: {
            commands.PLAYER_TURN: Transition.by_admin(StateBattlePlayerTurn),
            commands.ENEMY_TURN: Transition.by_admin(StateBattleEnemyTurn),
            commands.EVENT_FINISHED: Transition.by_admin(StateWaitForEvent),
            commands.YOU_DIED: Transition.by_admin(StateGameOver)
        },
        StateBattlePlayerTurn: {
            commands.ATTACK: Transition.by_user(StateBattleAttack),
            commands.USE_SPELL: Transition.by_user(StateBattleUseSpell),
            commands.USE_ITEM: Transition.by_user(StateBattleUseItem),
            commands.FLEE: Transition.by_user(StateBattleTryToFlee)
        },
        StateBattleAttack: {commands.BATTLE_ACTION_PERFORMED: Transition.by_admin(StateBattle)},
        StateBattleUseSpell: {commands.BATTLE_ACTION_PERFORMED: Transition.by_admin(StateBattle)},
        StateBattleUseItem: {
            commands.BATTLE_ACTION_PERFORMED: Transition.by_admin(StateBattle),
            commands.CANNOT_USE_ITEM: Transition.by_admin(StateBattlePlayerTurn)
        },
        StateBattleTryToFlee: {
            commands.BATTLE_ACTION_PERFORMED: Transition.by_admin(StateBattle),
            commands.EVENT_FINISHED: Transition.by_admin(StateWaitForEvent)
        },
        StateBattleEnemyTurn: {commands.BATTLE_ACTION_PERFORMED: Transition.by_admin(StateBattle)},
        StateItemEvent: {
            commands.EVENT_FINISHED: Transition.by_admin(StateWaitForEvent)
        },
        StateTrapEvent: {
            commands.EVENT_FINISHED: Transition.by_admin(StateWaitForEvent)
        },
        StateCharacterEvent: {
            commands.START_ITEM_TRADE: Transition.by_admin(StateItemTrade),
            commands.START_FAMILIAR_TRADE: Transition.by_admin(StateFamiliarTrade),
            commands.START_BATTLE: Transition.by_admin(StateStartBattle),
            commands.EVENT_FINISHED: Transition.by_admin(StateWaitForEvent)
        },
        StateItemTrade: {
            commands.TRADE_ITEM: Transition.by_user(StateItemTradeAccepted),
            commands.REJECTED: Transition.by_user(StateItemTradeRejected)
        },
        StateItemTradeAccepted: {commands.EVENT_FINISHED: Transition.by_admin(StateWaitForEvent)},
        StateItemTradeRejected: {commands.EVENT_FINISHED: Transition.by_admin(StateWaitForEvent)},
        StateFamiliarTrade: {
            commands.ACCEPTED: Transition.by_user(StateFamiliarTradeAccepted),
            commands.REJECTED: Transition.by_user(StateFamiliarTradeRejected)
        },
        StateFamiliarTradeAccepted: {commands.EVENT_FINISHED: Transition.by_admin(StateWaitForEvent)},
        StateFamiliarTradeRejected: {commands.EVENT_FINISHED: Transition.by_admin(StateWaitForEvent)},
        StateGameOver: {commands.RESTART: Transition.by_admin(StateStart)}
    }

    def __init__(self, game_config: dict, player_name: str):
        self._context = StateMachineContext(game_config, player_name)
        self._state = StateStart(self._context)

    def on_action(self, action):
        try:
            if not self._handle_generic_action(action):
                self._handle_non_generic_action(action)
        except InvalidOperation as exc:
            self._context.add_response(str(exc))
        return [f'{self._context.player_name}: {response}' for response in self._context.take_responses()]

    def _handle_generic_action(self, action: StateMachineAction) -> bool:
        command = action.command
        if command == commands.RESTART:
            if action.is_given_by_admin:
                self._state = StateStart(self._context)
            return True
        if command == commands.SHOW_FAMILIAR_STATS:
            self._handle_familiar_stats_query()
            return True
        elif command == commands.SHOW_INVENTORY:
            self._handle_inventory_query()
            return True
        elif command == commands.SHOW_FLOOR:
            self._handle_floor_query()
            return True
        else:
            return False

    def _handle_familiar_stats_query(self):
        familiar = self._context.familiar
        self._context.add_response(f"{familiar.to_string()}.")

    def _handle_inventory_query(self):
        inventory_string = ', '.join(self._context.inventory.items)
        self._context.add_response(f"You have: {inventory_string}.")

    def _handle_floor_query(self):
        self._context.add_response(f"You are on {self._context.floor + 1}F.")

    def _handle_non_generic_action(self, action):
        state_transition_table = self.TRANSITIONS.get(type(self._state))
        if state_transition_table is None:
            self._on_unknown_state()
            return
        transition = state_transition_table.get(action.command)
        if transition is None:
            self._on_unexpected_action(action)
        else:
            self._change_state(transition, action)
            if self._context.has_action():
                self._handle_non_generic_action(self._context.take_action())

    def _on_unknown_state(self):
        logger.error(f"{self} is in state {self._state} for which there is no transition.")

    def _on_unexpected_action(self, action):
        logger.warning(f"{self} in state {self._state} does not have transition for '{action.command}'")

    def _change_state(self, transition, action):
        if transition.guard(action):
            self._state = transition.nextState.create(self._context, action.args)
            logger.info(f"{self} changed state to {self._state}.")
            self._state.on_enter()

    def __str__(self):
        return f'SM for "{self._context.player_name}"'
