# Dev-notes:
# Create change_passwd method in VM instead editing the "shadow.sys" in Network.add_vm method
# Move chracter limits in creating password and nick, to some constants
import discord
from Network import Network
import asyncio
#import threading
import time

FREQUENCY: int = 0.5
SERVER_ID: int = 1024343901038985267

CHANNELS: dict = {
    "chat": 1024343901517123655,
    "questions-and-answers": 1025441734508941393,
    "terminal": 1025442786801111091,
    "default": 1025511904803831919,
    "exchange": 1041788707134521444,
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
  
  (N) = not implemented yet
  ## Global commands:
    - help ---------------> display this commands' help message
    - list ---------------> display a list of squads
    - (N)info <squad-name> --> display details about the squad
    - join <squad-name> --> join the squad
    - squad <squad-name> -> create a new squad
  
  ## Admin commands:
    - !clear -------------> delete all messages in the terminal
    - !save --------------> save game's data to a database
    - !close -------------> stop game's bot
"""

SQUAD_HELP: str = """
# Commands:
  
  (N) = not implemented yet
  ## Member commands:
    - help ---------------------> display this commands' help message
    - register <nick> <passwd> -> create a new VM for yourself, password should be fake, don't use any real data!
  
  ## (Co)Lider commands:
    - (N)promote <nick> --------> promote a member by one rank
    - (N)demote <nick> ---------> demote a member by one rank
    - (N)farewell <nick> -------> dismiss a member from the squad
"""

SQUAD_NAMES_ALPHABET: str = "abcdefghijklmnopqrstuvwxyz-"
NICKS_ALPHABET: str = "abcdefghijklmnopqrstuvwxyz-0134_ABCDEFGHIJKLMNOPQRSTUVWXYZ"
PASSWDS_ALPHABET: str = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


class Server:

    network: Network = None
    channels: tuple = None
    bot: discord.Client = None
    guild: discord.Guild = None
    state: bool = None# True - running, False - well...
    #network_thread: threading.Thread = None

    def __list__squads__(self) -> str:
        squad_list: str = None
        leader: str = None
        
        squad_list = f"   squad name    |members| state | leader\n{'=' * 42}\n"

        for squad in self.network.squads.values():
            leader = None
            for member in squad.members.keys():
                if squad.members[member] == "Leader":
                    leader = member
                    break

            squad_list += f"{squad.name:16} | {len(squad.members.keys()):2}/12 | {'open' if squad.recruting is True else 'close':5} | {leader}\n"

        return squad_list

    async def __create_squad__(self, leader: discord.Member, squad_name: str):
        squad_channel: discord.TextChannel = None
        default_channel: discord.TextChannel = None

        self.network.add_squad(squad_name)

        default_channel = self.guild.get_channel(CHANNELS["default"])
        squad_channel = await default_channel.clone(name=squad_name)
        await leader.add_roles(self.guild.get_role(ROLES["Squad-Leader"]))
        await squad_channel.set_permissions(leader, read_messages=True, send_messages=True, add_reactions=True, manage_messages=True, read_message_history=True)
        
        await self.__send__("Your squad servers are ready. Recruitment is open.", squad_channel, leader)

        if self.__check_role__(leader, ROLES["Hacker"]) is True:
            return
        
        await self.__send__("Now you can create your VM (Virtual Machine). Check 'help' cmd here.", squad_channel, leader)

    async def __join_member__(self, member: discord.Member, squad_name: str):
        squad_channel: discord.TextChannel = None
        
        for channel in self.guild.text_channels:
            if channel.name == squad_name:
                squad_channel = channel
                break
            
        await member.add_roles(self.guild.get_role(ROLES["Squad-Recruit"]))
        await squad_channel.set_permissions(member, read_messages=True, send_messages=True, add_reactions=True, read_message_history=True)
        
        await self.__send__(f"Welcome to {squad_name}!", squad_channel, member)

        if self.__check_role__(member, ROLES["Hacker"]) is True:
            return
        
        await self.__send__("Now you can create your VM (Virtual Machine). Check 'help' cmd here.", squad_channel, member)

    def __check_name__(self, name: str, alphabet: str, max_lenght: int) -> bool:
        if len(name) > max_lenght:
            return False

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
        checkpoint: bool = None

        if args[0] == "help":
            await self.__send__(GLOBAL_HELP, terminal, author)
        
        elif args[0][0] == '!':
            if self.__check_role__(author, ROLES["Admin"]) is False:
                await self.__send__("Don't bother yourself :) It's an admin's duty.", terminal, author)
                return
            if args[0] == "!clear":
                async for message in terminal.history():
                    await message.delete()
                    await asyncio.sleep(0.7)

            if args[0] == "!save":
                self.network.save()
                await self.__send__("Database updated.", terminal, author)
            
            if args[0] == "!close":
                await terminal.send("@here\n```\nShutting down...\n```")#self.__send__("Shutting down...", terminal, author)
                await self.bot.close()
                self.state = False
                self.network_thread.join()
        
        elif args[0] == "join":
            if self.__check_role__(author, ROLES["Squad-Recruit"]) is True or self.__check_role__(author, ROLES["Squad-Master"]) is True or self.__check_role__(author, ROLES["Squad-CoLeader"]) is True or self.__check_role__(author, ROLES["Squad-Leader"]) is True:
                await self.__send__("Your current squad needs you :)", terminal, author)
                return
            if len(args) != 2:
                await self.__send__("Incorrect amount of arguments. Take a look at 'help' command.")
                return

            checkpoint = False
            for squad in self.network.squads.values():
                if squad.name == args[1]:
                    checkpoint = True
                    break
        
            if checkpoint is False:
                await self.__send__("Squad not found :(", terminal, author)
                return

            await self.__join_member__(author, args[1])

        elif args[0] == "squad":

            if len(args) != 2 or (self.__check_name__(args[1], SQUAD_NAMES_ALPHABET, 14) is False):
                await self.__send__("Incorrect squad name!", terminal, author)
                return
            if self.__check_role__(author, ROLES["Squad-Recruit"]) is True or self.__check_role__(author, ROLES["Squad-Master"]) is True or self.__check_role__(author, ROLES["Squad-CoLeader"]) is True or self.__check_role__(author, ROLES["Squad-Leader"]) is True:
                await self.__send__("Your current squad needs you :)", terminal, author)
                return
            if args[1] in self.network.squads.keys():
                await self.__send__("Cool squad name, however it's already in use.", terminal, author)
                return

            await self.__create_squad__(author, args[1])
            
        elif args[0] == "list":
            await self.__send__(self.__list__squads__(), terminal, author)
    

    async def __squad__(self, squad_terminal: discord.TextChannel, author: discord.Member, args: tuple):
        if args[0] == "help":
            await self.__send__(SQUAD_HELP, squad_terminal, author)
        
        if args[0] == "register":
        
            if self.__check_role__(author, ROLES["Hacker"]) is True:
                await self.__send__("It seems that you already have VM.", squad_terminal, author)
                return
            if len(args) != 3:
                await self.__send__("Incorrect amount of arguments. Take a look at 'help' command.", squad_terminal, author)
                return
            if self.__check_name__(args[1], NICKS_ALPHABET, 14) is False:
                await self.__send__(f"Incorrect nick!\n- Avielable characters:\n{NICKS_ALPHABET}\n- Max lenght:\n14", squad_terminal, author)
                return
            if self.__check_name__(args[2], PASSWDS_ALPHABET, 6) is False:
                await self.__send__(f"Incorrect password!\n- Avielable characters:\n{PASSWDS_ALPHABET}\n- Max lenght:\n6", squad_terminal, author)
                return

            if self.__check_role__(author, ROLES["Squad-Leader"]) is True:
                self.network.add_vm(args[1], args[2], squad_terminal.name, "Leader")
            else:
                self.network.add_vm(args[1], args[2], squad_terminal.name, "Recruit")

            await author.edit(nick=args[1])
            await author.add_roles(self.guild.get_role(ROLES["Hacker"]))
            await self.__send__("Welcome hacker! Now you can log in and play.", squad_terminal, author)
        
        if args[0][0] == ">":
            if self.__check_role__(author, ROLES["Hacker"]):
                pass


    def __init__(self, db_filename: str):
        self.network = Network(db_filename)
        self.bot = discord.Client(intents=discord.Intents.all())
        
        #self.network_thread = threading.Thread(target=self.__network_loop__)
        #self.network_thread.start()

        @self.bot.event
        async def on_ready() -> None:
            self.guild = self.bot.get_guild(SERVER_ID)
            print(f"-- session by {self.bot.user} in {self.guild.name} --")
            #await self.__send__("Starting up...", self.guild.get_channel(CHANNELS["terminal"]), self.guild.get_role(ROLES["everyone"]))
            await self.guild.get_channel(CHANNELS["terminal"]).send("@here\n```\nStarting up...\n```")


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
                print(args)
                await self.__squad__(channel, author, args)

            elif channel.id == CHANNELS["terminal"]:
                print(args)
                await self.__terminal__(channel, author, args)

    
    def start(self, api_token: str):
        self.bot.run(api_token)
    
