import asyncio
import datetime
from game.config import Config
from game.state_machine import StateMachine, StateMachineContext
from game.state_machine_action import StateMachineAction
from game import commands
from game.game_interface import GameInterface
import logging
import random
from typing import Callable
import os.path

logger = logging.getLogger(__name__)


class Controller(GameInterface):
    class PlayerDoesNotExist(Exception):
        def __init__(self, player_name: str):
            super().__init__()
            self.player_name = player_name

    class NoPlayerForEvent(Exception):
        pass

    STATE_FILE_SUFFIX = '.json'

    def __init__(self, game_config: Config, state_files_directory: str):
        self._game_config = game_config
        self._state_files_directory = state_files_directory
        self._rng = random.Random()
        self._player_state_machines = {}
        self._active_players = set()
        self._event_timer: asyncio.Task = None
        self._load_state_files()

    def _load_state_files(self):
        for file_name in os.listdir(self._state_files_directory):
            file_path = os.path.join(self._state_files_directory, file_name)
            if os.path.isfile(file_path):
                self._load_state_file(file_path)

    def _load_state_file(self, state_file_path: str):
        _, state_file_name = os.path.split(state_file_path)
        player_name, file_extension = os.path.splitext(state_file_name)
        if file_extension != self.STATE_FILE_SUFFIX:
            logger.debug(f"Non-json file trying to be loaded - {state_file_path}.")
            return
        try:
            with open(state_file_path, mode='r') as state_file:
                state_machine = StateMachine.load(state_file, self._game_config)
                self._player_state_machines[player_name] = state_machine
            logger.info(f"Loaded '{player_name}'s' state.")
        except IOError as exc:
            logger.error(f"Error while loading '{player_name}'s' state. Reason - {exc}.")

    @property
    def _timers(self) -> Config.Timers:
        return self._game_config.timers

    def _any_player_active(self) -> bool:
        return len(self._active_players) > 0

    def set_response_event_handler(self, handler: Callable[[str], bool]):
        self._response_event_handler = handler

    def _send_response(self, player_name: str, responses: list[str]):
        for response_string in self._response_string_generator(responses):
            self._response_event_handler(f"@{player_name}: {response_string}")

    def _response_string_generator(self, responses: list[str]):
        def responses_group_to_string(responses_group: list[str]):
            return '\n'.join(responses_group)

        responses_group = []
        for response in responses:
            if response == StateMachineContext.RESPONSE_LINE_BREAK:
                if len(responses_group) > 0:
                    yield responses_group_to_string(responses_group)
                responses_group = []
            else:
                responses_group.append(response)
        if len(responses_group) > 0:
            yield responses_group_to_string(responses_group)

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
        if len(responses) > 0:
            self._send_response(player_name, responses)
        if player_state_machine.is_finished():
            self._restart_game(player_name)
        self._save_player_state(player_name)

    def _save_player_state(self, player_name: str):
        logger.debug(f"Saving state for '{player_name}'.")
        try:
            with open(self._player_state_file_path(player_name), mode='w') as player_state_file:
                self._player_state_machine(player_name).save(player_state_file)
        except IOError as exc:
            logger.error(f"Could not save state file for '{player_name}'. Reason - {exc}.")

    def _player_state_file_path(self, player_name: str) -> str:
        return os.path.join(self._state_files_directory, self._player_state_file_name(player_name))

    @classmethod
    def _player_state_file_name(cls, player_name: str) -> str:
        return player_name + cls.STATE_FILE_SUFFIX

    def _player_state_machine(self, player_name: str) -> StateMachine:
        if not self.does_player_exist(player_name):
            raise self.PlayerDoesNotExist(player_name)
        return self._player_state_machines[player_name]

    def does_player_exist(self, player_name: str) -> bool:
        return player_name in self._player_state_machines

    def _restart_game(self, player_name: str):
        self._handle_action(player_name, self._admin_action(commands.RESTART))

    def add_active_player(self, player_name: str):
        if self._is_player_active(player_name):
            return
        is_first_active_player = not self._any_player_active()
        self._active_players.add(player_name)
        if not self.does_player_exist(player_name):
            self._player_state_machines[player_name] = StateMachine(self._game_config, player_name)
        if is_first_active_player:
            logger.info(f"First player became active. Starting event.")
            self._handle_event_timer_expiry()

    def _is_game_started(self, player_name: str) -> bool:
        return self.does_player_exist(player_name) and self._player_state_machine(player_name).is_started()

    def _start_game(self, player_name: str):
        if player_name not in self._player_state_machines:
            player_state_machine = StateMachine(self._game_config, player_name)
            self._player_state_machines[player_name] = player_state_machine
        else:
            player_state_machine = self._player_state_machines[player_name]
        self._handle_action(player_name, self._admin_action(commands.STARTED))

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
        event_command = commands.GENERATE_EVENT if self._is_game_started(player_name) else commands.STARTED
        self._handle_action(player_name, self._admin_action(event_command))

    def _select_player_for_event(self) -> str:
        eligible_players = self._event_eligible_players()
        if len(eligible_players) == 0:
            raise self.NoPlayerForEvent()
        players_weights = [self._player_event_weight(player_name) for player_name in eligible_players]
        return self._rng.choices(eligible_players, players_weights)[0]

    def _event_eligible_players(self) -> list[str]:
        def is_event_eligible_player(player_name: str) -> bool:
            return not self._is_game_started(player_name) or self._is_player_waiting_for_event(player_name)

        return list(filter(is_event_eligible_player, self._active_players))

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
