import asyncio
import datetime
from game.config import Config
from game.errors import InvalidOperation
from game.state_machine import StateMachine
from game.state_machine_action import StateMachineAction
from game import commands
from game.game_interface import GameInterface
import logging
import random
from typing import Callable

logger = logging.getLogger(__name__)


class Controller(GameInterface):
    class PlayerDoesNotExist(Exception):
        def __init__(self, player_name: str):
            super().__init__()
            self.player_name = player_name

    class NoPlayerForEvent(Exception):
        pass

    def __init__(self, game_config: Config):
        self._game_config = game_config
        self._rng = random.Random()
        self._player_state_machines = {}
        self._active_players = set()
        self._event_timer: asyncio.Task = None

    @property
    def _timers(self) -> Config.Timers:
        return self._game_config.timers

    def _any_player_active(self) -> bool:
        return len(self._active_players) > 0

    def set_response_event_handler(self, handler: Callable[[str], bool]):
        self._response_event_handler = handler

    def _send_response(self, player_name: str, responses: list[str]):
        response_string = '\n'.join(responses)
        self._response_event_handler(f"{player_name}: {response_string}")

    def handle_user_action(self, player_name: str, command: str, args: str):
        self._handle_action(player_name, self._user_action(command, args))

    def _user_action(self, command: str, args: tuple=()) -> StateMachineAction:
        return StateMachineAction(command, args)

    def handle_admin_action(self, player_name: str, command: str, args: str):
        self._handle_action(player_name, self._admin_action(command, args))

    def _admin_action(self, command: str, args: tuple=()) -> StateMachineAction:
        return StateMachineAction(command, args, is_given_by_admin=True)

    def _handle_action(self, player_name: str, action: StateMachineAction):
        self.add_active_player(player_name)
        player_state_machine = self._player_state_machine(player_name)
        responses = player_state_machine.on_action(action)
        self._send_response(player_name, responses)
        if player_state_machine.is_finished():
            # TODO: do sth when player dies
            pass

    def _does_player_exist(self, player_name: str) -> bool:
        return player_name in self._player_state_machines

    def _player_state_machine(self, player_name: str) -> StateMachine:
        if not self._does_player_exist(player_name):
            raise self.PlayerDoesNotExist(player_name)
        return self._player_state_machines[player_name]

    def add_active_player(self, player_name: str):
        if self._is_player_active(player_name):
            return
        if not self._is_game_started(player_name):
            self._start_game(player_name)
        if not self._any_player_active():
            logger.info(f"First player became active. Starting timers.")
            self._start_timers()
        self._active_players.add(player_name)

    def _is_game_started(self, player_name: str) -> bool:
        return self._does_player_exist(player_name) and self._player_state_machine(player_name).is_started()

    def _start_game(self, player_name: str):
        player_state_machine = StateMachine(self._game_config, player_name)
        self._player_state_machines[player_name] = player_state_machine
        responses = player_state_machine.on_action(self._admin_action(commands.STARTED))
        self._send_response(player_name, responses)

    def remove_active_player(self, player_name: str):
        if not self._is_player_active(player_name):
            return
        self._active_players.remove(player_name)
        if not self._any_player_active():
            logger.info(f"All players became inactive. Stopping timers.")
            self._stop_timers()

    def _is_player_active(self, player_name: str) -> bool:
        return player_name in self._active_players

    def _start_timers(self):
        self._start_event_timer()

    def _stop_timers(self):
        self._cancel_timer(self._event_timer)

    def _start_event_timer(self):
        self._cancel_timer(self._event_timer)
        self._event_timer = self._create_timer(
            'Event',
            self._timers.event_interval,
            self._handle_event_timer_expiry)

    def _handle_event_timer_expiry(self):
        self._event_timer = None
        logger.info(f"Event timer expired")
        self._start_event_timer()
        if not self._any_player_active():
            logger.info(f"No players active. Ignoring event timer expiry.")
            return
        try:
            player_name = self._select_player_for_event()
        except self.NoPlayerForEvent:
            logger.info(f"No eligible players for event.")
            return
        player_state_machine = self._player_state_machine(player_name)
        try:
            self._send_response(player_name, player_state_machine.start_random_event())
        except InvalidOperation as exc:
            logger.warning(f"Cannot start event for '{player_name}'. {exc}")

    def _select_player_for_event(self) -> str:
        eligible_players = self._event_eligible_players()
        if len(eligible_players) == 0:
            raise self.NoPlayerForEvent()
        players_weights = [self._player_event_weight(player_name) for player_name in eligible_players]
        return self._rng.choices(eligible_players, players_weights)[0]

    def _event_eligible_players(self) -> list[str]:
        return list(filter(self._is_player_waiting_for_event, self._active_players))

    def _is_player_waiting_for_event(self, player_name) -> bool:
        return self._player_state_machine(player_name).is_waiting_for_event()

    def _player_event_weight(self, player_name: str) -> int:
        self._update_event_selection_penalty(player_name)
        state_machine = self._player_state_machine(player_name)
        player_selection_weights = self._game_config.player_selection_weights
        if not state_machine.has_event_selection_penalty():
            return player_selection_weights.with_penalty
        else:
            return player_selection_weights.without_penalty

    def _update_event_selection_penalty(self, player_name):
        state_machine = self._player_state_machine(player_name)
        if not state_machine.has_event_selection_penalty():
            return
        if datetime.datetime.now() > state_machine.event_selection_penalty_end_dt:
            state_machine.clear_event_selection_penalty()

    def _create_timer(self, name, interval, callback):
        return asyncio.create_task(self._timer(name, interval, callback))

    async def _timer(self, name, interval, callback):
        logger.debug(f"'{name}' timer started ({interval}s).")
        try:
            await asyncio.sleep(interval)
            logger.debug(f"'{name}' timer expired.")
            callback()
        except asyncio.CancelledError:
            logger.debug(f"'{name}' timer cancelled.")

    def _cancel_timer(self, timer: asyncio.Task):
        if timer is not None and not timer.done():
            timer.cancel()
