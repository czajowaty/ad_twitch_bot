from game.controller import Controller
import logging

logger = logging.getLogger(__name__)


class RemoteCommandsHandler:
    def __init__(self, controller: Controller):
        self._controller = controller

    def handle_command(self, command_line: str):
        splitted = command_line.split()
        if len(splitted) < 2:
            logger.warning(f"Too short remote command '{command_line}'.")
            return
        player_name, command, args = splitted[0], splitted[1], splitted[2:]
        if not player_name.startswith('@'):
            logger.warning(f"Player name needs to start with '@' character.")
            return
        player_name = player_name.lstrip('@')
        if not self._controller.does_player_exist(player_name):
            logger.warning(f"Player with name '{player_name}' does not exist.")
            return
        logger.info(f"Sending command '{command}' with args {args} to '{player_name}'.")
        self._controller.handle_admin_action(player_name, command, args)
