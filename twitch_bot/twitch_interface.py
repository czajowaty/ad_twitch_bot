from twitchio.dataclasses import User
from typing import Callable


class TwitchInterface:
    def set_bot_connected_event_handler(self, handler: Callable):
        raise NotImplementedError(f'{self.__class.__name__}.{self.set_bot_connected_event_handler}')

    def set_join_event_handler(self, handler: Callable[[User], None]):
        raise NotImplementedError(f'{self.__class.__name__}.{self.set_join_event_handler}')

    def set_part_event_handler(self, handler: Callable[[User], None]):
        raise NotImplementedError(f'{self.__class.__name__}.{self.set_part_event_handler}')

    def set_message_event_handler(self, handler: Callable[[User], None]):
        raise NotImplementedError(f'{self.__class.__name__}.{self.set_message_event_handler}')

    def set_command_event_handler(self, handler: Callable[[User, str, list[str]], None]):
        raise NotImplementedError(f'{self.__class.__name__}.{self.set_command_event_handler}')

    def ignore_user(self, user_name: str):
        raise NotImplementedError(f'{self.__class.__name__}.{self.ignore_user}')

    def unignore_user(self, user_name: str):
        raise NotImplementedError(f'{self.__class.__name__}.{self.unignore_user}')

    def send_message(self, message: str) -> bool:
        raise NotImplementedError(f'{self.__class.__name__}.{self.send_message}')
