import argparse
import json
from commander.commander import Commander
from game.controller import Controller as GameController, Config as GameConfig
import logging.handlers
from twitch_bot.ad_bot import AdBot, User


class TwitchGameMediator:
    def __init__(self, bot_config: dict, game_config: GameConfig):
        self._ad_twitch_bot = AdBot(bot_config)
        self._game_controller = GameController(game_config)
        self._connect_twitch_if_events()
        self._connect_game_if_events()

    def _connect_twicht_if_events(self):
        self._twitch_if.set_bot_connected_event_handler(self._handle_bot_connected)
        self._twitch_if.set_join_event_handler(self._handle_user_joined_channel)
        self._twitch_if.set_part_event_handler(self._handle_user_left_channel)
        self._twitch_if.set_message_event_handler(self._handle_user_sent_message)
        self._twitch_if.set_command_event_handler(self._handle_user_command)

    def _connect_game_if_events(self):
        self._game_if.set_response_event_handler(self._handle_game_response)

    def _handle_bot_connected(self):
        pass

    def _handle_user_joined_channel(self, user: User):
        self._game_if.add_active_player(self._player_name(user))

    def _handle_user_left_channel(self, user: User):
        self._game_if.remove_active_player(self._player_name(user))

    def _handle_user_sent_message(self, user: User):
        self._game_if.add_active_player(self._player_name(user))

    def _handle_user_command(self, user: User, command: str, args: list[str]):
        self._game_if.handle_user_action(self._player_name(user), command, args)

    def _handle_game_response(self, response: str) -> bool:
        return self._twitch_if.send_message(response)

    def _player_name(self, user: User) -> str:
        return user.name

    def run(self):
        self._ad_twitch_bot.run()


def main():
    args = parse_args()
    configure_logger()
    game_config = GameConfig.from_file(args.game_config)
    if args.bot_config is not None:
        bot_config = json.load(args.bot_config)
        TwitchGameMediator(bot_config, game_config).run()
    else:
        Commander(game_config).run()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('game_config', type=argparse.FileType('r'))
    parser.add_argument('-b', '--bot_config', type=argparse.FileType('r'))
    return parser.parse_args()


def configure_logger():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler = logging.handlers.RotatingFileHandler('ad_bot.log', maxBytes=megabytes_to_bytes(100), backupCount=1)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)


def megabytes_to_bytes(mb):
    return mb * 1000 ** 2


if __name__ == '__main__':
    main()
