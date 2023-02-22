# Dev-notes:
# Clear message in #quick-report on !close and add it on sturtup with ticket emoji.


import discord
#from discord.ext import commands
from Network import Network, Offer
import asyncio
import threading
from time import asctime, gmtime
from datetime import timedelta

from Squad import RANKS, INT_TO_RANK
from VM import VM, OS_LIST, EXPLOITS
from Games import GAMES, TicTacToe
from Errors import error

SERVER_ID: int = 1024343901038985267

CHANNELS: dict = {
    "quick-report": 1040654448621531137,
    "auto-mod": 1039257068445646960,
    "chat": 1024343901517123655,
    "questions-and-answers": 1025441734508941393,
    "terminal": 1025442786801111091,
    "default": 1025511904803831919,
    "exchange": 1041788707134521444,
    "mini-games": 1064196114196217896,
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

TAGS: dict = {
    "exploits": 1041789556091015288,
    "system": 1049032139930337350,
}

DEFAULT_TIMEOUT: int = 60 * 30

SQUAD_NAMES_ALPHABET: str = "abcdefghijklmnopqrstuvwxyz-"
NICKS_ALPHABET: str = "abcdefghijklmnopqrstuvwxyz-0134_ABCDEFGHIJKLMNOPQRSTUVWXYZ"
#PASSWDS_ALPHABET: str = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
HISTORY_LIMIT: int = 15


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
    
    - !gift <nick><CV> ---> transfer some CV to the player
    
    - !clear -------------> delete all messages in the terminal
    
    - !save --------------> save game's data to a database
    
    - !close -------------> stop game's bot
  
  
  ## Mod commands (WORK ON ANY CHANNEL):
    
    - !void [nick, ...] --> timout player(s), clear chat

    - !nick <old><new> ---> change nick of the player

"""

SQUAD_HELP: str = f"""
# Commands:
  
  (N) = not implemented yet
  ## Member commands:
    
    - help ----------------> display this commands' help message
    
    - register <nick><OS> -> create a new Virtua Machine (VM) for yourself,
        avielable OS: {OS_LIST}
    
    - panel ---------------> (N)display basic info about the squad
    
    - time ----------------> display server time
    
    - leave ---------------> leave the squad

  ## (Co)Leader commands:
    
    - !enroll --------------> Open/close enrollment to squad
    
    - !promote <nick> ------> promote a member by one rank
    
    - !demote <nick> -------> demote a member by one rank
    
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

MINI_GAMES_HELP: str = """
# Commands:
    
    start <game><nick> -> Invite member <nick> for the game,
        avielable games:
            o ttt => Tic Tac Toe
    
    stop ---------------> Stop currently running game

# Example:
    
    start ttt John -----> Invite John to play Tic Tac Toe
    
# Instruction:
    
    Use reaction or type number by yourself when it's your turn.

"""

ATTACK_PANEL: str = """
🔎 = scan
📋 = scan resoults

🗃 = exploits archives
🎛 = kernel exploit
🗜 = vsh exploit
"""


class Server:

    network: Network = None
    channels: tuple = None
    bot: discord.Client = None
    guild: discord.Guild = None
    #state: bool = None# True - running, False - well...
    network_thread: threading.Thread = None
    game: int = None

    __ttt: TicTacToe = None

    def __list__squads__(self) -> str:
        squad_list: str = None
        leader: str = None
        
        squad_list = f"   squad name    |members| state | leader\n{'=' * 42}\n"

        for squad in self.network.squads.values():
            leader = None
            for member in squad.members.keys():
                if squad.members[member] == RANKS["leader"]:
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
            self.network.by_nick[leader.display_name].squad = squad_name
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

        
        self.network.squads[squad_name].members[member.display_name] = RANKS["recruit"]
        
        if self.__check_role__(member, ROLES["Hacker"]) is True:
            self.network.by_nick[member.display_name].squad = squad_name
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

    async def __promote__(self, squad_channel: discord.TextChannel, member: discord.Member, demote: bool=False):
        squad_name: str = squad_channel.name
        role: str = None
        promotion: int = 1

        if demote is True:
            promotion = -1
        
        # remove old role
        role = INT_TO_RANK[self.network.squads[squad_name].members[member.display_name]]
        await member.remove_roles(self.guild.get_role(ROLES[role]))

        # update role
        self.network.squads[squad_name].members[member.display_name] += promotion
        
        role = INT_TO_RANK[self.network.squads[squad_name].members[member.display_name]]
        await member.add_roles(self.guild.get_role(ROLES[role]))

        # output
        await self.__send__(f"{member.display_name} has been (pro/de)moted to {role}.", squad_channel)

    async def __vsh__(self, args: tuple[str, ...], squad_terminal: discord.TextChannel, author: discord.Member):
        ip: str = None
        port: int = None
        answer: str = ""
        nick: str = author.display_name
        message: discord.Message = None
        
        ip = self.network.by_nick[nick].ip
        port = self.network.by_nick[nick].port_config["vsh"]
        self.network.send((ip, port), (nick, None), ' '.join(args))
        answer = self.network.vsh(self.network.by_nick[nick])
        message = await self.__send__(answer, squad_terminal, author, color=True)
        
        await self.__add_buttons__(message, ['📟', '📁', '📑', '🛡', '⚔', '❔'])

    async def __send__(self, content: str, channel: discord.TextChannel, user: discord.Member=None, color: bool=False) -> discord.Message:
        if user == None:
            return await channel.send(f"```{'js' if color is True else ''}\n{content}\n```")
        else:
            return await channel.send(f"{user.mention}\n```{'js' if color is True else ''}\n{content}\n```")
    
    async def __cls__(self, channel: discord.TextChannel, author: discord.Member=None, keep: int = 0):
        counter: int = 0

        async for message in channel.history():
            if (author == None or message.author == author) and counter >= keep:
                    await message.delete()

            await asyncio.sleep(0.7)
            counter += 1

    async def __terminal__(self, terminal: discord.TextChannel, author: discord.Member, args: tuple) -> None:

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
                await self.__cls__(self.guild.get_channel(CHANNELS["quick-report"]))
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
                if not args[1] in self.network.by_nick.keys():
                    await self.__send__("VM not found!", terminal, author)
                    return
                if args[2].isdigit() is False:
                    await self.__send__("Incorrect transfer value!", terminal, author)
                    return

                self.network.transfer(int(args[1]), args[2])
                await self.guild.get_channel(CHANNELS["chat"]).send(f"@everyone\n :gift: **{args[2]} has just been gifted {args[1]} CV!**\n\tCongratulations!")

        elif args[0] == "join":
            if self.__check_role__(author, ROLES["Squad-Recruit"]) is True or self.__check_role__(author, ROLES["Squad-Master"]) is True or self.__check_role__(author, ROLES["Squad-CoLeader"]) is True or self.__check_role__(author, ROLES["Squad-Leader"]) is True:
                await self.__send__("Your current squad needs you :)", terminal, author)
                return
            if len(args) != 2:
                await self.__send__("Incorrect amount of arguments. Take a look at 'help' command.", terminal, author)
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
            await self.__send__(self.__list__squads__(), terminal, author, True)

        elif args[0] == "bank":
            await self.__send__(f"System account: {self.network.bank:_} [CV]", terminal, author, True)
        
        
    async def __attack_panel__(self, squad_terminal: discord.TextChannel, author: discord.Member):
        message: discord.Message = await self.__send__(ATTACK_PANEL, squad_terminal, author)

        await self.__add_buttons__(message, ['🔎', '📋', '🗃', '🛠'])#'🎛', '🗜'])


    async def __add_offer_post__(self, author: discord.Member, exploit_id: int, price: str):
        store: discord.ForumChannel = self.guild.get_channel(CHANNELS["exchange"])
        vm: VM = self.network.by_nick[author.display_name]
        offer: Offer = self.network.offers[-1]

        await store.create_thread(name=f"[ {len(self.network.offers) - 1} ] --{EXPLOITS[offer.content.category].upper()} {OS_LIST[offer.content.os]} {offer.content.lvl}--", content=f"**By:** {author.mention}\n**Price:** {price} CV\n**Success rate:** {offer.content.success_rate} %", applied_tags=[store.get_tag(TAGS["exploits"]), ])

    async def __squad__(self, squad_terminal: discord.TextChannel, author: discord.Member, args: list[str]=None, reaction: discord.Reaction=None):
        
        if args == None:
            if reaction.emoji == '📟':
                args = ['>', "panel",]
            elif reaction.emoji == '📁':
                args = ['>', "ls",]
            elif reaction.emoji == '📑':
                args = ['>', "cat", "log.sys"]
            elif reaction.emoji == '🛡':
                args = ['>', "close",]
            elif reaction.emoji == '🗃':
                args = ["$archives",]
            elif reaction.emoji == '❔':
                args = ['>', "help",]
            elif reaction.emoji == '⚔':
                args = ["$attack"]
            elif reaction.emoji == '🔎':
                args = ['>', "scan", "target"]
            elif reaction.emoji == '📋':
                args = ['>', "cat", "scan.txt"]
            elif reaction.emoji == '🛠':
                args = ["$ai", "max"]
            elif reaction.emoji == '🎛':
                args = ['>', "vsh_exploit", ]
            elif reaction.emoji == '🗜':
                args = ['>', "kernel_exploit", ]
            else:
                args = ["nothing",]

        print(args)

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

            elif args[0] == "!promote":
                if len(args) != 2:
                    await self.__send__("Incorrect amount of arguments. Take a look at 'help' command.", squad_terminal, author)
                    return
                
                if not args[1] in self.network.squads[squad_terminal.name].members:
                    await self.__send__("Member not found.", squad_terminal, author)
                    return
                
                if self.network.squads[squad_terminal.name].members[args[1]] >= RANKS["coleader"]:
                    await self.__send__("Member has already max rank.", squad_terminal, author)
                    return
                
                await self.__promote__(squad_terminal, self.guild.get_member_named(args[1]))
        
            elif args[0] == "!demote":
                if len(args) != 2:
                    await self.__send__("Incorrect amount of arguments. Take a look at 'help' command.", squad_terminal, author)
                    return
                
                if not args[1] in self.network.squads[squad_terminal.name].members:
                    await self.__send__("Member not found.", squad_terminal, author)
                    return
                
                if self.network.squads[squad_terminal.name].members[args[1]] == RANKS["recruit"]:
                    await self.__send__("Member has already minimal rank.", squad_terminal, author)
                    return
                
                await self.__promote__(squad_terminal, self.guild.get_member_named(args[1]), True)
        
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
            await self.__send__("Welcome hacker! Now you play! Enter `>help` here.", squad_terminal, author)
        
        elif args[0] == "leave":
            self.network.squads[squad_terminal.name].members.pop(author.display_name)
            
            if self.__check_role__(author, ROLES["Hacker"]) is True:
                self.network.by_nick[author.display_name].squad = None
                
            await squad_terminal.set_permissions(author, read_messages=False, send_messages=False, add_reactions=False, manage_messages=False, read_message_history=False)
            
            if self.__check_role__(author, ROLES["Squad-Recruit"]) is True:
                await author.remove_roles(self.guild.get_role(ROLES["Squad-Recruit"]))
            if self.__check_role__(author, ROLES["Squad-Master"]) is True:
                await author.remove_roles(self.guild.get_role(ROLES["Squad-Master"]))
            if self.__check_role__(author, ROLES["Squad-CoLeader"]) is True:
                await author.remove_roles(self.guild.get_role(ROLES["Squad-CoLeader"]))
            if self.__check_role__(author, ROLES["Squad-Leader"]) is True:
                await author.remove_roles(self.guild.get_role(ROLES["Squad-Leader"]))
                

        elif args[0] == "$time" or args[0] == "time":
            await self.__send__(f"It's <{asctime(gmtime())}> in the game.", squad_terminal, author, True)

        elif args[0] == "$whois":
            if len(args) != 2:
                await self.__send__("Incorrect amount of arguments. Take a look at '> help' command.", squad_terminal, author)
                return

            if not args[1] in self.network.by_ip.keys():
                await self.__send__("IP address not found.", squad_terminal, author)
                return
            
            await self.__send__(f"{args[1]}:\n\tnick: {self.network.by_ip[args[1]].nick}\n\tsquad: {self.network.by_ip[args[1]].squad}", squad_terminal, author)
        
        elif args[0] == "$attack":
            await self.__attack_panel__(squad_terminal, author)

        elif args[0] == "$ai":
            if self.__check_role__(author, ROLES["Hacker"]) is False:
                await self.__send__("You are not registered yet... See `help` cmd here.", squad_terminal, author)
                return
            
            await self.__send__(self.network.start_ai(author.display_name, args), squad_terminal, author)

        elif args[0] == "$bf":
            if self.__check_role__(author, ROLES["Hacker"]) is False:
                await self.__send__("You are not registered yet... See `help` cmd here.", squad_terminal, author)
                return
            if len(args) != 2:
                await self.__send__("Incorrect amount of arguments. Take a look at '> help' command.", squad_terminal, author)
                return
            
            await self.__send__(self.network.start_bf(author.display_name, args[1]), squad_terminal, author)

        elif args[0] == "$archives":
            if self.__check_role__(author, ROLES["Hacker"]) is False:
                await self.__send__("You are not registered yet... See `help` cmd here.", squad_terminal, author)
                return

            await self.__send__(self.network.by_nick[author.display_name].archives(), squad_terminal, author, True)

        elif args[0] == "$sell":
            if self.__check_role__(author, ROLES["Hacker"]) is False:
                await self.__send__(error(6, 0), squad_terminal, author)
                return
            if len(args) != 3:
                await self.__send__(error(0, 1), squad_terminal, author)
                return
            if args[1].isdigit() is False or args[2].isdigit() is False:
                await self.__send__(error(1, 1), squad_terminal, author)
                return
            

            if self.network.sell_exploit(self.network.by_nick[author.display_name], int(args[2]), int(args[1])) is False:
                await self.__send__(error(5, 6), squad_terminal, author)
                return
            
            await self.__add_offer_post__(author, int(args[1]), args[2])
            await self.__send__(f"Your offer's id is: {len(self.network.offers) - 1}", squad_terminal, author)

        elif args[0] == '>':
            if self.__check_role__(author, ROLES["Hacker"]) is False:
                await self.__send__("You are not registered yet... See `help` cmd here.", squad_terminal, author)
                return
            
            await self.__vsh__(args[1:], squad_terminal, author)

    async def __add_buttons__(self, message: discord.Message, emoijs: tuple[str]):
        for emoji in emoijs:
            await message.add_reaction(emoji)

    async def __mini_games__(self, panel: discord.TextChannel, author: discord.Member, args: list[str]=None, reaction: discord.Reaction=None):
        player2: discord.Member = None
        message: discord.Message = None

        if args == None:
            if reaction.emoji == '🛑':
                args = ["stop",]
            elif reaction.emoji == '0️⃣':
                args = ["0", ]
            elif reaction.emoji == '1️⃣':
                args = ["1", ]
            elif reaction.emoji == '2️⃣':
                args = ["2", ]
            elif reaction.emoji == '3️⃣':
                args = ["3", ]
            elif reaction.emoji == '4️⃣':
                args = ["4", ]
            elif reaction.emoji == '5️⃣':
                args = ["5", ]
            elif reaction.emoji == '6️⃣':
                args = ["6", ]
            elif reaction.emoji == '7️⃣':
                args = ["7", ]
            elif reaction.emoji == '8️⃣':
                args = ["8", ]
            else:
                args = ["nothing", ]
        
        print(args)

        if args[0] == "help":
            await self.__send__(MINI_GAMES_HELP, panel, author)

        elif args[0] == "start":
            if self.game != GAMES["None"]:
                await self.__send__("Other game is already running.", panel, author)
                return

            if len(args) != 3:
                await self.__send__("Incorrect amount of arguments.", panel, author)
                return
            
            player2 = self.guild.get_member_named(args[2])

            if player2 == None:
                await self.__send__("Player not found.", panel, author)
                return

            if args[1] == "ttt":
                self.game = GAMES["TicTacToe"]
                self.__ttt = TicTacToe([author.display_name, player2.display_name])
                
                await self.guild.get_channel(CHANNELS["chat"]).send(f"{player2.mention}\n{author.display_name} invited you to play TicTacToe at {panel.mention}.")
                
                message = await self.__send__(self.__ttt.render(), panel, self.guild.get_member_named(self.__ttt.players[self.__ttt.turn]))
                await self.__cls__(panel, keep=1)
                await self.__add_buttons__(message, ['0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '🛑'])
            else:
                await self.__send__("Game not found.", panel, author)
        
        else:
            if self.game == GAMES["TicTacToe"]:
                
                if args[0] == "stop" and (author.display_name in self.__ttt.players or self.__check_role__(author, ROLES["Mod"]) or self.__check_role__(author, ROLES["Admin"])):
                    
                    self.game = GAMES["None"]
                    self.__ttt = None
                    
                    await self.__send__("Game over!", panel)
                    
                    return
                
                if args[0].isdigit() is False:
                    return
                
                if self.__ttt.is_correct_move(author.display_name, int(args[0])) is False:
                    return
                
                if self.__ttt.forward(int(args[0])) is True:

                    await self.__send__(self.__ttt.render(), panel)
                    await self.__cls__(panel, keep=1)
                    await self.__send__(f"Game over!\nWinner: {self.__ttt.winner}", panel)

                    self.__ttt = None
                    self.game = GAMES["None"]
                
                else:
                    message = await self.__send__(self.__ttt.render(), panel, self.guild.get_member_named(self.__ttt.players[self.__ttt.turn]))
                    await self.__cls__(panel, keep=1)
                    await self.__add_buttons__(message, ['0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '🛑'])

    
    async def __void__(self, nick: str, channel: discord.TextChannel, author: discord.Member):
        member: discord.Member = self.guild.get_member_named(nick)

        if member != None:
            await member.timeout(timedelta(seconds=DEFAULT_TIMEOUT))
            await self.__cls__(channel, member)
        else:
            await self.__send__(f"Member '{nick}' not found.", channel, author)

    def __init__(self, db_filename: str):
        self.network = Network(db_filename)
        self.game = GAMES["None"]
        self.bot = discord.Client(intents=discord.Intents.all())#commands.Bot(command_prefix='$', intents=discord.Intents.all())
        
        self.network_thread = threading.Thread(target=self.network.cpu_loop)
        self.network_thread.start()
        
        #@self.bot.command()
        #async def hello(ctx: commands.Context):
        #    await ctx.send("Hello, World!")
        

        @self.bot.event
        async def on_ready() -> None:
            channel: discord.TextChannel = None
            report_message: discord.Message = None

            self.guild = self.bot.get_guild(SERVER_ID)
            
            print(f"-- session by {self.bot.user} in {self.guild.name} --")
            #await self.__send__("Starting up...", self.guild.get_channel(CHANNELS["terminal"]), self.guild.get_role(ROLES["everyone"]))
            await self.guild.get_channel(CHANNELS["terminal"]).send("```\nStarting up...\n```")
            
            report_message = await self.guild.get_channel(CHANNELS["quick-report"]).send("React with :warning: emoij to quickly notify **MODS** about some **rules-braking** incident.")
            await report_message.add_reaction("⚠")

            #print([f"{tag.name}: {tag.id}" for tag in self.guild.get_channel(CHANNELS["exchange"]).available_tags])

            while True:
                for notification in self.network.notifications:
                    
                    if notification[0] in CHANNELS.keys():
                        channel = self.guild.get_channel(CHANNELS[notification[0]])
                    else:
                        for i in range(len(self.guild.channels)):
                            if self.guild.channels[i].name == notification[0]:
                                channel = self.guild.channels[i]
                                break

                    if notification[1] == None:
                        await self.__send__(notification[2], channel)
                    else:
                        await self.__send__(notification[2], channel, self.guild.get_member_named(notification[1]))

                self.network.notifications = []
                await asyncio.sleep(60)

        @self.bot.event
        async def on_message(message: discord.Message) -> None:
            #await self.bot.process_commands(message)
            author: discord.Member = None
            channel: discord.TextChannel = None
            args: list = None
            # history: list[discord.Message] = None

            author = message.author
            
            if author == self.bot.user:
                return
            

            channel = self.guild.get_channel(message.channel.id)#self.bot.get_channel(message.channel.id)
            args = message.content.split()
            

            if self.__check_role__(author, ROLES["Mod"]) or self.__check_role__(author, ROLES["Admin"]):
                if args[0] == "!void":
                    if len(args) == 1:
                        await self.__cls__(channel)
                        return

                    for nick in args[1:]:
                        await self.__void__(nick, channel, author)
                    
                    return

                elif args[0] == "!nick":
                    if len(args) != 3:
                        await self.__send__("Incorrect amount of arguments.", channel, author)
                        return
                    
                    if self.__check_name__(args[2], NICKS_ALPHABET, 14) is False:
                        await self.__send__("Incorrect new nick.", channel, author)
                        return
                    
                    if self.guild.get_member_named(args[2]) != None:
                        await self.__send__("Nick in use.", channel)
                        return

                    if self.network.change_nick(args[1], args[2]) is True:
                        await self.__send__("Nick has been changed.", channel, author)
                        await self.guild.get_member_named(args[1]).edit(nick=args[2])
                    else:
                        await self.__send__("User not found.", channel)

                    return

            if channel.category_id == CATEGORIES["GLOBAL"] and channel.id != CHANNELS["terminal"] and channel.id != CHANNELS["mini-games"]:
                return

            if channel.category_id == CATEGORIES["SQUADS"]:
                # history = [msg async for msg in channel.history(limit=HISTORY_LIMIT + 10)]

                # if len(history) > HISTORY_LIMIT:
                #     await channel.delete_messages(history[HISTORY_LIMIT:])
                
                await self.__squad__(channel, author, args=args)

            elif channel.id == CHANNELS["terminal"]:
                # history = [msg async for msg in channel.history(limit=HISTORY_LIMIT + 5)]

                # if len(history) > HISTORY_LIMIT:
                #     await channel.delete_messages(history[HISTORY_LIMIT:])

                print(args)
                await self.__terminal__(channel, author, args)
            
            elif channel.id == CHANNELS["mini-games"]:
                await self.__mini_games__(channel, author, args)

        @self.bot.event
        async def on_reaction_add(reaction: discord.Reaction, author: discord.Member):
            message: discord.Message = reaction.message
            channel: discord.TextChannel = self.guild.get_channel(message.channel.id)
            
            if author == self.bot.user:
                return

            if message.author != self.bot.user:
                return

            if message.channel.category_id == CATEGORIES["SQUADS"] :
                await self.__squad__(channel, author, reaction=reaction)
                await reaction.remove(author)
            
            elif message.channel.id == CHANNELS["quick-report"]:
                await self.guild.get_channel(CHANNELS["auto-mod"]).send(f"{self.guild.get_role(ROLES['Mod']).mention}\n**QUICK REPORT!!!**\nFrom: {author.mention}\nSquad: {self.network.by_nick[author.display_name].squad if author.display_name in self.network.by_nick.keys() else 'None'}")
                await asyncio.sleep(10)
                await reaction.remove(author)
            
            elif message.channel.id == CHANNELS["mini-games"]:
                await self.__mini_games__(message.channel, author, reaction=reaction)


        @self.bot.event
        async def on_raw_reaction_add(reaction: discord.RawReactionActionEvent):
            offer: discord.Thread = None
            message: discord.Message = None

            offer = self.guild.get_channel_or_thread(reaction.channel_id)
            
            if offer.category_id != CATEGORIES["STORE"]:
                return

            await self.__send__(self.network.buy(int(offer.name.split()[1]), reaction.member.display_name), self.guild.get_channel(CHANNELS["terminal"]), reaction.member, True)
            
            await asyncio.sleep(1)
            message = await offer.fetch_message(reaction.message_id)
            await message.clear_reactions()

    
    def start(self, api_token: str):
        self.bot.run(api_token)
    
