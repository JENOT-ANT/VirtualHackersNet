# Dev-notes:
# Create change_passwd method in VM instead editing the "shadow.sys" in Network.add_vm method

import discord
#from discord.ext import commands
from Network import Network
import asyncio
import threading
from time import asctime, gmtime

from Squad import RANKS
from VM import OS_LIST


SERVER_ID: int = 1024343901038985267

CHANNELS: dict = {
    "chat": 1024343901517123655,
    "questions-and-answers": 1025441734508941393,
    "terminal": 1025442786801111091,
    "default": 1025511904803831919,
    "exchange": 1041788707134521444,
}

CATEGORIES: dict = {
    "GLOBAL": 1024343901038985270,
    "SQUADS": 1025444416527278131,
    "STORE": 1049431906766307398,
}

ROLES: dict = {
    "Admin": 1025432915561168896,
    "Mod": 1039261745396600912,
    "Hacker": 1025436309851996191,
    "Squad-Leader": 1030199156947558510,
    "Squad-CoLeader": 1030440951077929020,
    "Squad-Master": 1030574174512623616,
    "Squad-Recruit": 1030572112068485212,
}


SQUAD_NAMES_ALPHABET: str = "abcdefghijklmnopqrstuvwxyz-"
NICKS_ALPHABET: str = "abcdefghijklmnopqrstuvwxyz-0134_ABCDEFGHIJKLMNOPQRSTUVWXYZ"
#PASSWDS_ALPHABET: str = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"



GLOBAL_HELP: str = """
# Commands:
  
  (N) = not implemented yet
  ## Global commands:
    
    - help ---------------> display this commands' help message
    
    - list ---------------> display a list of squads
    
    - info <squad-name> --> (N)display details about the squad
    
    - join <squad-name> --> join the squad
    
    - squad <squad-name> -> create a new squad
    
    - bank ---------------> display currency owned by the system
  
  ## Admin commands:
    
    - !gift <CV><nick> ---> transfer some CV to the player
    
    - !clear -------------> delete all messages in the terminal
    
    - !save --------------> save game's data to a database
    
    - !close -------------> stop game's bot
"""

SQUAD_HELP: str = f"""
# Commands:
  
  (N) = not implemented yet
  ## Member commands:
    
    - help ----------------> display this commands' help message
    
    - register <nick><OS> -> create a new Virtua Machine (VM) for yourself,
        avielable OS: {OS_LIST}
    
    - panel ---------------> (N)display basic info about squad
    
    - time ----------------> display server time
  
  ## (Co)Leader commands:
    
    - !enroll --------------> Open/close enrollment to squad
    
    - !promote <nick> ------> (N)promote a member by one rank
    
    - !demote <nick> -------> (N)demote a member by one rank
    
    - !farewell <nick> -----> (N)dismiss a member from the squad
"""

HACK_THE_PLANET = r"""
      _    _     __      ___   _   __
     | |__| |   /  \    / __| | | / /
     |  __  |  / == \  | |__  | |> |
     |_|  |_| /_/  \_\  \___| |_| \_\
          _____   _    _   _ ____
         |_____| | |__| | | |___/
           | |   |  __  | | |__|
           |_|   |_|  |_| |_|___\
 ____   _        __     _   _   _ ____  _____
| |  \ | |      /  \   | \ | | | |___/ |_____|
| |__/ | |__   / == \  |  ^  | | |__|    | |
|_|    |____| /_/  \_\ |_| \_| |_|___\   |_|
                  _________
                 /   / \   \
                / \ /   \ / \
               |---|- @ -|---|
               |===|=  @=|===|
               |---|-@@@-|---|
                \ / \   / \ /
                 \___\_/___/
"""

class Server:

    network: Network = None
    channels: tuple = None
    bot: discord.Client = None
    guild: discord.Guild = None
    #state: bool = None# True - running, False - well...
    network_thread: threading.Thread = None

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

        self.network.add_squad(squad_name, leader.display_name)

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
        
        self.network.squads[squad_name].members[member.display_name] = RANKS["recruit"]
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


    async def __vsh__(self, args: list, squad_terminal: discord.TextChannel, author: discord.Member):
        ip: str = None
        port: int = None
        message: str = ""
        nick: str = author.display_name

        for arg in args:
            message += arg + ' '

        ip = self.network.by_nick[nick].ip
        port = self.network.by_nick[nick].port_config["vsh"]
        self.network.send((ip, port), (nick, None), message)
        message = self.network.vsh(self.network.by_nick[nick])
        await self.__send__(message, squad_terminal, author)

    async def __send__(self, content: str, channel: discord.TextChannel, user: discord.Member=None):
        if user == None:
            await channel.send(f"```q\n{content}\n```")
        else:
            await channel.send(f"{user.mention}\n```q\n{content}\n```")
    
    async def __cls__(self, channel: discord.TextChannel):
        async for message in channel.history():
            await message.delete()
            await asyncio.sleep(0.7)

    async def __terminal__(self, terminal: discord.TextChannel, author: discord.Member, args: tuple) -> None:
        #checkpoint: bool = None

        if args[0] == "help":
            await self.__send__(GLOBAL_HELP, terminal, author)
        
        elif args[0][0] == '!':
            if self.__check_role__(author, ROLES["Admin"]) is False:
                await self.__send__("Don't bother yourself :) It's an admin's duty.", terminal, author)
                return

            if args[0] == "!clear":
                await self.__cls__(terminal)

            elif args[0] == "!save":
                self.network.save()
                await self.__send__("Database updated.", terminal, author)
            
            elif args[0] == "!close":
                await terminal.send("```\nShutting down...\n```")#self.__send__("Shutting down...", terminal, author)
                #self.state = False
                self.network.running = False
                self.network_thread.join()
                await self.bot.close()
            
            elif args[0] == "!planet":
                await terminal.send(f"**```\n{HACK_THE_PLANET}\n```**")

            elif args[0] == "!gift":
                if len(args) != 3:
                    await self.__send__("Incorrect amount of arguments. Take a look at 'help' command.", terminal, author)
                    return
                if not args[2] in self.network.by_nick.keys():
                    await self.__send__("VM not found!", terminal, author)
                    return
                if args[1].isdigit() is False:
                    await self.__send__("Incorrect transfer value!", terminal, author)
                    return

                self.network.transfer(int(args[1]), args[2])
                await self.guild.get_channel(CHANNELS["chat"]).send(f"@everyone\n :gift: **{args[2]} has just been gifted {args[1]} CV!**\n\tCongratulations!")

        elif args[0] == "join":
            if self.__check_role__(author, ROLES["Squad-Recruit"]) is True or self.__check_role__(author, ROLES["Squad-Master"]) is True or self.__check_role__(author, ROLES["Squad-CoLeader"]) is True or self.__check_role__(author, ROLES["Squad-Leader"]) is True:
                await self.__send__("Your current squad needs you :)", terminal, author)
                return
            if len(args) != 2:
                await self.__send__("Incorrect amount of arguments. Take a look at 'help' command.")
                return
            if not args[1] in self.network.squads.keys():
                await self.__send__("Squad not found :(", terminal, author)
                return
            
            if self.network.squads[args[1]].recruting is False:
                await self.__send__("Squad is not enrolling new members :(", terminal, author)
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

        elif args[0] == "bank":
            await self.__send__(f"System account: {self.network.bank:_} [CV]", terminal, author)
        
        

    async def __squad__(self, squad_terminal: discord.TextChannel, author: discord.Member, args: tuple[str, ...]):
        if args[0] == "help":
            await self.__send__(SQUAD_HELP, squad_terminal, author)
        
        elif args[0][0] == '!':
            if self.__check_role__(author, ROLES["Squad-Leader"]) is False and self.__check_role__(author, ROLES["Squad-CoLeader"]) is False and self.__check_role__(author, ROLES["Mod"]) is False:
                await self.__send__("Don't bother yourself :) It's an (co)leader's duty.", squad_terminal, author)
                return

            if args[0] == "!clear":
                await self.__cls__(squad_terminal)

            elif args[0] == "!enroll":
                self.network.squads[squad_terminal.name].recruting = not(self.network.squads[squad_terminal.name].recruting)
                
                if self.network.squads[squad_terminal.name].recruting is True:
                    await self.__send__("Recruitment is open for everyone!", squad_terminal, author)
                else:
                    await self.__send__("Recruitment is finished for now.", squad_terminal, author)
        
        elif args[0] == "register":
        
            if self.__check_role__(author, ROLES["Hacker"]) is True:
                await self.__send__("It seems that you already have VM.", squad_terminal, author)
                return
            if len(args) != 3:
                await self.__send__("Incorrect amount of arguments. Take a look at 'help' command.", squad_terminal, author)
                return
            if self.__check_name__(args[1], NICKS_ALPHABET, 14) is False:
                await self.__send__(f"Incorrect nick!\n- Avielable characters:\n{NICKS_ALPHABET}\n- Max lenght:\n14", squad_terminal, author)
                return
            if not args[2] in OS_LIST:
                await self.__send__(f"Incorrect operating system's name!\n- OS list:\n{OS_LIST}", squad_terminal, author)
                return

            # if self.__check_role__(author, ROLES["Squad-Leader"]) is True:
            self.network.add_vm(author.display_name, args[1], OS_LIST.index(args[2]), squad_terminal.name)
            # else:
                # self.network.add_vm(args[1], args[2], squad_terminal.name, "Recruit")

            await author.add_roles(self.guild.get_role(ROLES["Hacker"]))
            await author.edit(nick=args[1])
            await self.__send__("Welcome hacker! Now you can log in and play.", squad_terminal, author)
        
        elif args[0] == ">time" or args[0] == "time":
            await self.__send__(f"It's <{asctime(gmtime())}> in the game.", squad_terminal, author)

        elif args[0] == ">whois":
            if len(args) != 2:
                await self.__send__("Incorrect amount of arguments. Take a look at '>help' command.", squad_terminal, author)
                return

            if not args[1] in self.network.by_ip.keys():
                await self.__send__("IP address not found.", squad_terminal, author)
                return
            
            await self.__send__(f"{args[1]}:\n\tnick: {self.network.by_ip[args[1]].nick}\n\tsquad: {self.network.by_ip[args[1]].squad}", squad_terminal, author)

        elif args[0] == ">ai":
            if self.__check_role__(author, ROLES["Hacker"]) is False:
                await self.__send__("You are not registered yet... See `help` cmd here.", squad_terminal, author)
                return
            if len(args) != 2:
                await self.__send__("Incorrect amount of arguments. Take a look at '>help' command.", squad_terminal, author)
                return
            if args[1].isdigit() is False:
                await self.__send__("Incorrect arguments' values. Take a look at '>help' command.", squad_terminal, author)
                return

            if self.network.start_ai(author.display_name, int(args[1])) is True:
                await self.__send__("Production of the exploit has just started.", squad_terminal, author)
            else:
                await self.__send__("You can't choose exploit lvl higher than your AI lvl and lower than 1.", squad_terminal, author)

        elif args[0] == ">bf":
            if self.__check_role__(author, ROLES["Hacker"]) is False:
                await self.__send__("You are not registered yet... See `help` cmd here.", squad_terminal, author)
                return
            if len(args) != 2:
                await self.__send__("Incorrect amount of arguments. Take a look at '>help' command.", squad_terminal, author)
                return
            
            self.network.start_bf(author.display_name, args[1])
            
            await self.__send__("Started brutforce on the hash.", squad_terminal, author)

        elif args[0][0] == ">":
            if self.__check_role__(author, ROLES["Hacker"]) is False:
                await self.__send__("You are not registered yet... See `help` cmd here.", squad_terminal, author)
                return
            
            await self.__vsh__(args, squad_terminal, author)


    def __init__(self, db_filename: str):
        self.network = Network(db_filename)
        self.bot = discord.Client(intents=discord.Intents.all())#commands.Bot(command_prefix='$', intents=discord.Intents.all())
        
        self.network_thread = threading.Thread(target=self.network.cpu_loop)
        self.network_thread.start()
        
        #@self.bot.command()
        #async def hello(ctx: commands.Context):
        #    await ctx.send("Hello, World!")
        

        @self.bot.event
        async def on_ready() -> None:
            self.guild = self.bot.get_guild(SERVER_ID)
            print(f"-- session by {self.bot.user} in {self.guild.name} --")
            #await self.__send__("Starting up...", self.guild.get_channel(CHANNELS["terminal"]), self.guild.get_role(ROLES["everyone"]))
            await self.guild.get_channel(CHANNELS["terminal"]).send("```\nStarting up...\n```")
            
            while True:
                for notification in self.network.notifications:
                    for channel in self.guild.channels:
                        if channel.name == notification[0]:
                            if notification[1] == None:
                                await self.__send__(notification[2], channel)
                            else:
                                await self.__send__(notification[2], channel, self.guild.get_member_named(notification[1]))
                            break

                self.network.notifications = []
                await asyncio.sleep(120)

        @self.bot.event
        async def on_message(message: discord.Message) -> None:
            #await self.bot.process_commands(message)
            author: discord.Member = None
            channel: discord.TextChannel = None
            args: list = None
            
            author = message.author
            channel = self.guild.get_channel(message.channel.id)#self.bot.get_channel(message.channel.id)
            
            if author == self.bot.user:
                return
            
            if channel.category_id == CATEGORIES["GLOBAL"] and channel.id != CHANNELS["terminal"]:
                return
            
            
            args = message.content.split()

            if channel.category_id == CATEGORIES["SQUADS"]:
                print(args)
                await self.__squad__(channel, author, args)

            elif channel.id == CHANNELS["terminal"]:
                print(args)
                await self.__terminal__(channel, author, args)

        @self.bot.event
        async def on_reaction_add(reaction: discord.Reaction, author: discord.Member):
            return
            message: discord.Message = reaction.message

        @self.bot.event
        async def on_raw_reaction_add(reaction: discord.RawReactionActionEvent):
            offer: discord.Thread = None
            message: discord.Message = None

            offer = self.guild.get_channel_or_thread(reaction.channel_id)
            if offer.category_id != CATEGORIES["STORE"]:
                return

            await self.__send__(self.network.buy(int(offer.name.split()[1]), reaction.member.display_name), self.guild.get_channel(CHANNELS["terminal"]), reaction.member)
            
            await asyncio.sleep(1)
            message = await offer.fetch_message(reaction.message_id)
            await message.clear_reactions()

    
    def start(self, api_token: str):
        self.bot.run(api_token)
    
