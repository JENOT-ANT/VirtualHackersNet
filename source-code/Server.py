import discord
import time
from Network import Network

SERVER_ID: int = 1024343901038985267

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
    "Squad-Leader": 1030199156947558510,
    "Squad-CoLeader": 1030440951077929020,
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
    - !save --------------> save game's data to database
"""

SQUAD_NAMES_ALPHABET: str = "abcdefghijklmnopqrstuvwxyz-"
NICKS_ALPHABET: str = "abcdefghijklmnopqrstuvwxyz-ABCDEFGHIJKLMNOPQRSTUVWXYZ"


class Server:

    network: Network = None
    channels: tuple = None
    bot: discord.Client = None
    guild: discord.Guild = None

    async def __create_squad__(self, leader: discord.Member, squad_name: str):
        squad_channel: discord.TextChannel = None
        default_channel: discord.TextChannel = None

        self.network.add_squad(squad_name)

        default_channel = self.guild.get_channel(CHANNELS["default"])
        squad_channel = await default_channel.clone(name=squad_name)
        await leader.add_roles(self.guild.get_role(ROLES["Squad-Leader"]))
        await squad_channel.set_permissions(leader, read_messages=True, send_messages=True, add_reactions=True, manage_messages=True)
        
        await self.__send__("Your squad servers are ready. Recruitment is open.", squad_channel, leader)

        if self.__check_role__(leader, ROLES["Hacker"]) is True:
            return
        
        await self.__send__("Now you can create your VM. Use 'register <nick>' cmd.", squad_channel, leader)

    def __check_name__(self, name: str, alphabet: str) -> bool:
        for letter in name:
            if not (letter in alphabet):
                return False
        
        return True

    def __check_role__(self, member: discord.Member, role_id: int) -> bool:
        for role in member.roles:
            if role.id == role_id:
                return True
        
        return False

    async def __send__(self, content: str, channel: discord.TextChannel, user: discord.Member):
        await channel.send(f"{user.mention}\n```\n{content}\n```")

    async def __terminal__(self, terminal: discord.TextChannel, author: discord.Member, args: tuple) -> None:
        if args[0] == "help":
            await self.__send__(GLOBAL_HELP, terminal, author)
        
        elif args[0][0] == '!':
            if self.__check_role__(author, ROLES["Admin"]) is False:
                await self.__send__("Don't bother yourself :) It's an admin's duty.", terminal, author)
                return
            if args[0] == "!clear":
                async for message in terminal.history():
                    await message.delete(delay=5)
            if args[0] == "!save":
                self.network.save()

        elif args[0] == "squad":

            if len(args) != 2 or (self.__check_name__(args[1], SQUAD_NAMES_ALPHABET) is False):
                await self.__send__("Incorrect squad name!", terminal, author)
                return
            if self.__check_role__(author, ROLES["Squad-Recruit"]) is True or self.__check_role__(author, ROLES["Squad-Master"]) is True or self.__check_role__(author, ROLES["Squad-CoLeader"]) is True or self.__check_role__(author, ROLES["Squad-Leader"]) is True:
                await self.__send__("Your current squad needs you :)", terminal, author)
                return
            if args[1] in self.network.squads.keys():
                await self.__send__("Cool squad name, however it's already in use.", terminal, author)
                return

            await self.__create_squad__(author, args[1])
            
            
    
    async def __squad__(self, channel: discord.TextChannel, author: discord.Member, args: tuple):
        pass

    def __init__(self, db_filename: str):
        self.network = Network(db_filename)
        self.bot = discord.Client(intents=discord.Intents.all())

        @self.bot.event
        async def on_ready() -> None:
            self.guild = self.bot.get_guild(SERVER_ID)
            print(f"-- session by {self.bot.user} in {self.guild.name} --")

        @self.bot.event
        async def on_message(message: discord.Message) -> None:
            author: discord.Member = None
            channel: discord.TextChannel = None
            args: list = None
            
            author = message.author
            channel = self.guild.get_channel(message.channel.id)#self.bot.get_channel(message.channel.id)
            
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
    
