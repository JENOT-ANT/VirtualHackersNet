import discord
import time
from Network import Network

CHANNELS: dict = {
    "chat": 1024343901517123655,
    "questions-and-answers": 1025441734508941393,
    "terminal": 1025442786801111091,
    "default": 1025511904803831919,
}

CATEGORIS: dict = {
    "GLOBAL": 1024343901038985270,
    "SQUADS": 1025444416527278131,
}

ROLES: dict = {
    "Admin": 1025432915561168896,
    "Hacker": 1025436309851996191,
    "Squad-Lider": 1030199156947558510,
    "Squad-CoLider": 1030440951077929020,
    "Squad-Master": 1030574174512623616,
    "Squad-Recruit": 1030572112068485212,
}

GLOBAL_HELP: str = """
# Commands:
  
  ## Global commands:
    - help ---------------> display this commands' help message
    - list ---------------> display list of squads
    - info <squad-name> --> display details about squad
    - join <squad-name> --> join squad
    - squad <squad-name> -> create new squad
  
  ## Admin commands:
    - !clear -------------> delete all messages in terminal
"""


class Server:

    network: Network = None
    channels: tuple = None
    bot: discord.Client = None

    def __check_role__(self, member: discord.Member, role_id: int):
        for role in member.roles:
            if role.id == role_id:
                return True
        
        return False

    async def __send__(self, content: str, channel: discord.TextChannel, user: discord.Member):
        await channel.send(f"{user.mention}\n```\n{content}\n```")

    async def __terminal__(self, terminal: discord.TextChannel, author: discord.Member, args: tuple) -> None:
        if args[0] == "help":
            await self.__send__(GLOBAL_HELP, terminal, author)
        
        elif args[0] == "!clear":
            if self.__check_role__(author, ROLES["Admin"]) is False:
                await terminal.send(GLOBAL_HELP)
                return
            async for message in terminal.history():
                await message.delete(delay=5)
                time.sleep(1)

    async def __squad__(self, channel: discord.TextChannel, author: discord.Member, args: tuple):
        pass

    def __init__(self):
        self.network = Network()
        self.bot = discord.Client(intents=discord.Intents.all())

        @self.bot.event
        async def on_ready() -> None:
            print(f"-- session by {self.bot.user} --")

        @self.bot.event
        async def on_message(message: discord.Message) -> None:
            author: discord.Member = None
            channel: discord.TextChannel = None
            args: list = None
            
            author = message.author
            channel = self.bot.get_channel(message.channel.id)
            
            if author == self.bot.user:
                return

            
            if channel.category_id == CATEGORIS["GLOBAL"] and channel.id != CHANNELS["terminal"]:
                return
            
            
            args = message.content.split()

            if channel.category_id == CATEGORIS["SQUADS"]:
                pass

            elif channel.id == CHANNELS["terminal"]:
                print(args)
                await self.__terminal__(channel, author, args)
    
    def start(self, api_token: str):
        self.bot.run(api_token)
    
