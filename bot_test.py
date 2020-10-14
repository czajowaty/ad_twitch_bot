import json
from twitchio.ext import commands


class Bot(commands.Bot):
    def __init__(self):
        with open('bot_config.json', 'r') as bot_config_file:
            bot_config = json.load(bot_config_file)
            print(bot_config)
        super().__init__(
            irc_token=bot_config['OATH_TOKEN'],
            client_id=bot_config['CLIENT_ID'],
            nick=bot_config['NICK'],
            prefix=bot_config['PREFIX'],
            initial_channels=[bot_config['CHANNEL']])
        self._my_channel = bot_config['CHANNEL']

    async def event_ready(self):
        print("Ready")
        print(self)
        await self._ws.send_privmsg(self._my_channel, f"{self.nick} joined channel!")

    async def event_message(self, message):
        print(message)
        print(dir(message))
        print(f"#{message.channel}: {message.timestamp} - '{message.author}' said '{message.content}', tags: '{message.tags}'")
        await self.handle_commands(message)

    async def event_join(self, user):
        print(f"JOIN: {user}")
        print("JOIN2: ", dir(user))

    @commands.command(name='test')
    async def test(self, ctx):
        print("TEST command")
        await ctx.send(f"By your command, {ctx.author.name}!")


if __name__ == "__main__":
    Bot().run()
