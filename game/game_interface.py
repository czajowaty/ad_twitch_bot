from typing import Callable


class GameInterface:
    def set_response_event_handler(self, handler: Callable[[str], bool]):
        raise NotImplementedError(f"{self.__class__.__name__}.{self.set_response_event_handler}")

    def handle_user_action(self, player_name: str, command: str, args: str):
        raise NotImplementedError(f"{self.__class__.__name__}.{self.handle_user_action}")

    def handle_admin_action(self, player_name: str, command: str, args: str):
        raise NotImplementedError(f"{self.__class__.__name__}.{self.handle_admin_action}")

    def add_active_player(self, player_name: str):
        raise NotImplementedError(f"{self.__class__.__name__}.{self.add_active_player}")

    def remove_active_player(self, player_name: str):
        raise NotImplementedError(f"{self.__class__.__name__}.{self.remove_active_player}")
