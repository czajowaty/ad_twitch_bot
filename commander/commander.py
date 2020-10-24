import asyncio
from game.controller import Config, Controller


class Commander:
    EXIT_COMMAND = 'exit'
    JOIN_COMMAND = 'join'
    PART_COMMAND = 'part'
    ADMIN_COMMAND = 'admin'

    class InvalidCommand(Exception):
        pass

    def __init__(self, game_config: Config):
        self._controller = Controller(game_config)
        self._controller.set_response_event_handler(self._response_event_handler)

    def _response_event_handler(self, response: str) -> bool:
        print(response)
        return True

    def run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._get_and_execute_commands())

    async def _get_and_execute_commands(self):
        while True:
            player_name, is_admin, command, args = await asyncio.to_thread(self._get_command)
            if command == self.EXIT_COMMAND:
                return
            elif command == self.JOIN_COMMAND:
                self._controller.add_active_player(player_name)
            elif command == self.PART_COMMAND:
                self._controller.remove_active_player(player_name)
            else:
                if is_admin:
                    self._controller.handle_admin_action(player_name, command, args)
                else:
                    self._controller.handle_user_action(player_name, command, args)

    def _get_command(self):
        while True:
            command_line = input("Enter command [@player_name command arg1 arg2 arg3 ...]: ")
            try:
                return self._parse_to_command(command_line)
            except self.InvalidCommand as exc:
                print(f"Invalid command: {exc}")

    def _parse_to_command(self, command_line: str):
        splitted = command_line.split()
        if len(splitted) == 0:
            raise self.InvalidCommand('Cannot be empty.')
        if splitted[0] == self.EXIT_COMMAND:
            return self._build_command(command=self.EXIT_COMMAND)
        if len(splitted) == 1:
            raise self.InvalidCommand('Too short.')
        player_name = splitted[0]
        if not player_name.startswith('@'):
            raise self.InvalidCommand('Player name needs to start with "@" character.')
        player_name = player_name.lstrip('@')
        command, args = splitted[1], splitted[2:]
        is_admin = (command == self.ADMIN_COMMAND)
        if is_admin:
            if len(args) == 0:
                raise self.InvalidCommand('Too short.')
            command, args = args[0], args[1:]
        return self._build_command(player_name, is_admin, command, args)

    def _build_command(self, player_name: str='', is_admin: bool=False, command: str='', args: list[str]=[]):
        return player_name, is_admin, command, args
