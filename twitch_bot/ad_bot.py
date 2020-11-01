import asyncio
import logging
from twitch_bot.twitch_interface import TwitchInterface
from twitchio.dataclasses import Channel, Message, User
from twitchio.ext import commands
from typing import Callable

logger = logging.getLogger(__name__)


class AdBot(commands.Bot, TwitchInterface):
    def __init__(self, bot_config):
        self._excluded_user_names = set(bot_config['EXCLUDED_USERS'])
        self._channel_name = bot_config['CHANNEL'].lstrip('#')
        super().__init__(
            irc_token=bot_config['OATH_TOKEN'],
            client_id=bot_config['CLIENT_ID'],
            prefix=bot_config['PREFIX'],
            nick=bot_config['NICK'],
            initial_channels=[self._channel_name])

    def set_bot_connected_event_handler(self, handler: Callable):
        self._bot_connected_event_handler = handler

    def set_join_event_handler(self, handler: Callable[[User], None]):
        self._join_event_handler = handler

    def set_part_event_handler(self, handler: Callable[[User], None]):
        self._part_event_handler = handler

    def set_message_event_handler(self, handler: Callable[[User], None]):
        self._message_event_handler = handler

    def set_command_event_handler(self, handler: Callable[[User, str, list[str]], None]):
        self._command_event_handler = handler

    def ignore_user(self, user_name: str):
        logger.info(f"Adding {user_name} to excluded list.")
        self._excluded_user_names.add(user_name)

    def unignore_user(self, user_name: str):
        if user_name not in self._excluded_player_names:
            logger.warning(f"{user_name} is not in excluded list.")
            return
        logger.info(f"Removing {user_name} from excluded list.")
        self._excluded_user_names.remove(user_name)

    def send_message(self, message: str) -> bool:
        channel = self._get_channel()
        if channel is None:
            return False
        index = 0
        while index < len(message):
            asyncio.create_task(channel.send(f"/me {message[index:index + 500]}"))
            index += 500
        return True

    def _get_channel(self) -> Channel:
        return self.get_channel(self._channel_name)

    async def event_ready(self):
        logger.info(f"Bot connected.")
        self._bot_connected_event_handler()

    async def event_join(self, user: User):
        if self._is_excluded_user(user):
            return
        logger.info(f"'{user.name}' joined channel.")
        self._join_event_handler(user)

    async def event_part(self, user: User):
        if self._is_excluded_user(user):
            return
        logger.info(f"'{user.name}' left channel.")
        self._part_event_handler(user)

    async def event_message(self, message: Message):
        user = message.author
        if self._is_excluded_user(user):
            return
        self._message_event_handler(user)
        await self.handle_commands(message)

    def _is_excluded_user(self, user: User):
        return user.name.strip() in self._excluded_user_names

    @commands.command(name='adbot')
    async def _handle_ad_bot_command(self, ctx, *args):
        if len(args) == 0:
            return
        command, command_args = args[0], args[1:]
        self._command_event_handler(ctx.author, command, command_args)
