import re


class Commander:
    def __init__(self):
        self.a = ''

    def run(self):
        command = ''
        while command != 'exit':
            command_line = input("Enter command: ")
            command, args = self._parse_command_line(command_line)
            print(f"You entered {command}, {args}")

    def _parse_command_line(self, command):
        parsed_command = [s.strip() for s in re.split("\s+", command)]
        parsed_command = [s for s in parsed_command if len(s) > 0]
        if len(parsed_command) > 0:
            return parsed_command[0].lower(), parsed_command[1:]
        else:
            return '', []


if __name__ == '__main__':
    import logging
    from game.config import Config
    from game.state_machine import StateMachine
    from game.state_machine_action import StateMachineAction

    logging.basicConfig(level=logging.DEBUG)
    game_config = Config.from_file('../game_config.json')
    state_machine = StateMachine(game_config, "TestPlayer")
    responses = state_machine.on_action(StateMachineAction('started', is_given_by_admin=True))
    for response in responses:
        print(response)
    while True:
        command_line = input("Enter command: ")
        splitted = command_line.split(' ')
        command, args = splitted[0], splitted[1:]
        if command == 'exit':
            break
        responses = state_machine.on_action(StateMachineAction(command, args, is_given_by_admin=True))
        for response in responses:
            print(response)
