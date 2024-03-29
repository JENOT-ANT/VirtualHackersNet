# TODO:
#   2. Move args checking from method Server.__squads__ to start_ai
#   3. Create error database
#   4. Move file editing from vsh code to VM method
#   6. Create some sort of API in the Squad class that would replace trash code like changing nick and other stuff in variety of places
#   7. Change Server.__send__ method to add code embody optional
#   8. (?) Move key filenames to some constants

import shelve
import random
from Squad import Squad, RANKS
from VM import VM, Packet, OS_LIST, EXPLOITS, Exploit, MAX_SOFTWARE, Process
from hashlib import md5
from random import randint, choices
from time import sleep, time
from uuid import uuid4, UUID
from Errors import error

FREQUENCY: float = 0.5
AI_TIME: int = 60 * 1
NOTIFICATION_CHANNEL: str = "terminal"
MAX_CV: int = int(1e9)
MAX_CV_HASH: int = 10000
FOUND_CV_AMOUNT: int = 4

PASSWD_LENGHT: int = 4
PASSWDS_ALPHABET: str = "02458AMPQYZ"
MAX_GUESS: int = len(PASSWDS_ALPHABET)**PASSWD_LENGHT

MAX_EXPLOITS_AMOUNT: int = 20

SYSTEM_IP: str = "0.0.0.0"

SYSTEM_PORTS: dict = {
    "mine": 76,
}

DEFAULT_OS: int = 0
FILENAME_LIMIT: int = 14


OFFER_TYPES: dict = {
    "update": 0,
    "exploit": 1,
    "ip_list": 2,
}

def chance(success: int) -> bool:
    if randint(1, 100) <= success:
        return True
    else:
        return False

class Offer:

    seller: str = None
    type: int = None
    price: int = None
    content = None #: str | Exploit


    def __init__(self, seller: str, type: int, price: int, content):#content: str | Exploit
        self.seller = seller
        self.type = type
        self.price = price
        self.content = content




class Network:
    '''class for handling virtual network'''
    running: bool = False

    bank: int = None
    offers: list[Offer] = None
    notifications: list[tuple[str, str, str]] = None# [(squad, member, content), ...]
    squads: dict[str, Squad] = None

    by_ip: dict[str, VM] = None
    by_nick: dict[str, VM] = None

    system_network: dict[int, Packet] = None

    __cv_hash__: str = None
    __db_filename__: str = None


    def __init__(self, db_filename: str):
        self.running = True
        self.__db_filename__ = db_filename
        self.__cv_hash__ = str(randint(0, MAX_CV_HASH))
        self.squads = {}
        self.by_ip = {}
        self.by_nick = {}
        self.system_network = {}
        self.bank = MAX_CV

        self.notifications = []
        
        self.offers = []

        self.__load__()

    def __load__(self):
        exploits: list = None
        port_config: dict = None
        wallet: int = None
        os: int = None

        db: shelve.Shelf = shelve.open(self.__db_filename__, "r")
        
        for vm in db["vms"]:
            
            if "exploits" in vm.keys():
                exploits = vm["exploits"]
            else:
                exploits = []

            if "port_config" in vm.keys():
                port_config = vm["port_config"]
            else:
                port_config = {}
            
            if "wallet" in vm.keys():
                wallet = vm["wallet"]
            else:
                wallet = 0

            if "os" in vm.keys():
                os = vm["os"]
            else:
                os = DEFAULT_OS
            
            self.by_nick[vm["nick"]] = VM(vm["nick"], vm["squad"], vm["ip"], os, wallet, vm["software"], vm["files"], exploits, port_config)
            self.by_ip[vm["ip"]] = self.by_nick[vm["nick"]]

        for squad in db["squads"]:
            self.squads[squad["name"]] = Squad(squad["name"], squad["members"], squad["recruting"])
            
            # for member in self.squads[squad["name"]].members.keys():
            #     if self.squads[squad["name"]].members[member] == "Squad-Leader" or self.squads[squad["name"]].members[member] == "Leader":
            #         self.squads[squad["name"]].members[member] = LEADER
                
            #     elif self.squads[squad["name"]].members[member] == "Squad-Recruit" or self.squads[squad["name"]].members[member] == "Recruit":
            #         self.squads[squad["name"]].members[member] = RECRUIT

        if "bank" in db.keys():
            self.bank = db["bank"]
        
        if "offers" in db.keys():
            self.offers = db["offers"]
        else:
            self.offers = [
                Offer(None, OFFER_TYPES["update"], 200, "kernel"),
                Offer(None, OFFER_TYPES["update"], 100, "vsh"),
                Offer(None, OFFER_TYPES["update"], 100, "AI"),
                Offer(None, OFFER_TYPES["update"], 300, "miner"),
            ]
        
        db.close()

    def transfer(self, amount: int, destination: str=None, source: str=None) -> bool:
        if source == None:
            if amount > self.bank:
                return False

            self.by_nick[destination].wallet += amount
            self.bank -= amount
            
        else:
            if amount > self.by_nick[source].wallet:
                return False

            if destination == None:
                self.bank += amount
                self.by_nick[source].wallet -= amount
            else:
                self.by_nick[destination].wallet += amount
                self.by_nick[source].wallet -= amount
        
        return True

    def sys_mine(self):
        packet: Packet = None
        args: list = None

        packet = self.recv(SYSTEM_PORTS["mine"])
        args = packet.content.split()
        
        #print(args)

        if len(args) == 2 and args[1] in self.by_nick.keys() and args[0] == self.__cv_hash__:
            print(f"Found by {args[1]}")

            self.notifications.append((NOTIFICATION_CHANNEL, None, f"The CV hash has been found by {args[1]}."))
            
            if self.transfer(FOUND_CV_AMOUNT + self.by_nick[args[1]].software["miner"], args[1]) is True:
                self.direct_send((self.by_nick[args[1]].ip, 7676), (SYSTEM_IP, SYSTEM_PORTS["mine"]), "found")
            
            self.__cv_hash__ = str(randint(0, MAX_CV_HASH))


    def exploit(self, vm: VM, packet_source_ip: str, target_ip: str, target_port: int, exploit_id: int, attacker_nick: str=None, secret: str=None):
        attacker: VM = None
        answer: str = None

        if not target_ip in self.by_ip.keys():
            return "Exploit failed! Target not found."
        
        if attacker_nick == None:
            attacker_nick = vm.nick
        
        if not attacker_nick in self.by_nick.keys():
            return "Error! Exploit not found."
            
        attacker = self.by_nick[attacker_nick]

        if not target_ip in self.by_ip.keys():
            return "Error! Target not found."

        if exploit_id >= len(attacker.exploits):
            return "Error! Exploit not found."

        if target_port != self.by_ip[target_ip].port_config["vsh"]:
            if target_port in self.by_ip[target_ip].port_config.values():
                return "Error! Address responded with different protocol."
            
            return "Target didn't respond."

        if secret == None:
            secret = str(attacker.exploits[exploit_id].secret)

        self.direct_send((target_ip, target_port), (vm.ip, 2222), f"expl {exploit_id} {attacker_nick} {secret}")
        self.vsh(self.by_ip[target_ip])

        answer = self.recv(2222, vm).content
        
        if answer == "accept":
            vm.forward_to[packet_source_ip] = (target_ip, self.by_ip[target_ip].port_config["vsh"])
            
            return f"Connected to {self.by_ip[target_ip].nick}({target_ip})"
        
        elif answer == "no response":
            return "Target didn't respond."

        elif answer == "failed":
            return "Error! Exploit failed."

        return answer

    def handle_exploit(self, vm: VM, exploit_id: int, attacker_nick: str, secret: str) -> str:
        attacker: VM = None

        if not attacker_nick in self.by_nick.keys():
            return "args"
        
        attacker = self.by_nick[attacker_nick]

        if exploit_id >= len(attacker.exploits):
            return "id"

        if str(attacker.exploits[exploit_id].secret) != secret:
            return "secret"

        if attacker.exploits[exploit_id].os != vm.os:
            return "no response"

        if chance(attacker.exploits[exploit_id].success_rate) is True:
            if EXPLOITS[attacker.exploits[exploit_id].category] == "vsh":
                if attacker.exploits[exploit_id].lvl < vm.software["vsh"]:
                    return "failed"

                return "vsh"
            
            else:
                if attacker.exploits[exploit_id].lvl < vm.software["kernel"]:
                    return "failed"

                vm.add_to_log("Critical kernel error occured!")
                return "kernel"

        else:
            return "failed"

    def vsh(self, vm: VM) -> str:
        packet: Packet = None
        answer: Packet = None
        target: VM = None
        args: list = None
        iosout: str = None

        packet = self.recv(vm.port_config["vsh"], vm)
        
        if packet == None:
            return "Error! Connection refused."
        
        args = packet.content.split()


        if packet.source[0] in vm.logged_in:
            if packet.source[0] in vm.forward_to.keys():
                target = self.by_ip[vm.forward_to[packet.source[0]][0]]
                
                if args[0] == "exploit" and packet.source[0] == vm.nick:
                    self.direct_send((target.ip, vm.forward_to[packet.source[0]][1]), (vm.ip, 2222), f"{packet.content} {vm.nick} {vm.exploits[int(args[3])].secret}")
                else:
                    self.direct_send((target.ip, vm.forward_to[packet.source[0]][1]), (vm.ip, 2222), packet.content)
                
                self.vsh(target)
                answer = self.recv(2222, vm)
                
                if answer.content.split()[0] == "disconnect":
                    vm.forward_to.pop(packet.source[0])
                    iosout = f"Connection to {target.nick}({target.ip}) has been closed."
                    return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)

                elif answer.content.split()[0] == "proxy":
                    iosout = f"{answer.content} < {vm.nick}"
                    return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                
                elif answer.content == "access denied":
                    vm.forward_to.pop(packet.source[0])
                    iosout = "Access denied! Not authenticated."
                    return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                    
                iosout = answer.content
                return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)

            elif args[0] == "help":
                iosout = vm.help()
                return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
            
            elif args[0] == "passwd":
                self.set_passwd(vm.nick)
                iosout = "Password has been changed."
                return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)

            elif args[0] == "ls":
                iosout = vm.ls()
                return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)

            elif args[0] == "cat":
                if len(args) != 2:
                    iosout =  "Error! Incorrect amount of arguments. Check '> help' command."
                    return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)

                iosout = vm.cat(args[1])
                return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)

            elif args[0] == "transfer":
                if len(args) != 3:
                    iosout =  "Error! Incorrect amount of arguments. Check '> help' command."
                    return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                
                if args[2].isdigit() is False:
                    iosout =  "Error! Incorrect values of the arguments. Check '> help' command."
                    return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)

                if not args[1] in self.by_nick.keys():
                    iosout = "Error! Target VM not found."
                    return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)

                if int(args[2]) > vm.wallet - (50 * vm.software["kernel"]):
                    iosout = f"Error! Max transefr value: {vm.wallet - (50 * vm.software['kernel'])} [CV]"
                    return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                
                self.transfer(int(args[2]), args[1], vm.nick)
                vm.add_to_log(f"Transfered {int(args[2])} CV to {args[1]}.")
                self.by_nick[args[1]].add_to_log(f"Transaction: {int(args[2])} CV from {vm.nick}")

                iosout = f"Transfered {int(args[2])} [CV] to {args[1]}."
                return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)

            elif args[0] == "whoami":
                iosout = vm.whoami()
                return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)

            elif args[0] == "rm":
                if len(args) != 2:
                    iosout =  "Error! Incorrect amount of arguments. Check '> help' command."
                    return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                
                iosout = vm.remove(args[1])
                return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)

            elif args[0] == "ps":
                iosout = vm.ps()
                return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)

            elif args[0] == "scan":
                if len(args) != 2:
                    iosout = "Error! Incorrect amount of arguments. Check '> help' command."
                    return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                
                if args[1] == "target" and "target.config" in vm.files.keys():
                    iosout = self.start_scan(vm, vm.files["target.config"])
                    return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)

                iosout = self.start_scan(vm, args[1])
                return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)

            elif args[0] == "panel":
                iosout = vm.dashboard()
                return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
            
            elif args[0] == "clear":
                if len(args) != 2:
                    iosout = error(0, 1)
                    return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)

            elif args[0] == "exploit":
                #print(args)
                #print(f"{packet.source[0]} {vm.nick}")

                if (packet.source[0] != vm.nick and len(args) != 6) or (packet.source[0] == vm.nick and len(args) != 4):
                    iosout = "Error! Incorrect amount of arguments. Check '> help' command."
                    return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                
                if args[2].isnumeric() is False or args[3].isnumeric() is False:
                    iosout = "Error! Incorrect values of the arguments. Check '> help' command."
                    return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                
                if packet.source[0] != vm.nick:
                    iosout = self.exploit(vm, packet.source[0], args[1], int(args[2]), int(args[3]), args[4], args[5])
                
                else:
                    iosout = self.exploit(vm, packet.source[0], args[1], int(args[2]), int(args[3]))

                return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)

            elif args[0] == "exit":
                vm.exit(packet.source[0])
                
                iosout = "disconnect"
                return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
            
            elif args[0] == "proxy":
                iosout = f"proxy {vm.nick}"
                
                return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)

            elif args[0] == "close":
                iosout = vm.close()

                return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)

            elif args[0] == "vsh":
                if len(args) != 4:
                    iosout = "Error! Incorrect amount of arguments. Check '> help' command."
                    return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)

                if not args[1] in self.by_ip.keys():
                    iosout = "Error! IP address not found or not responding!"
                    return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)

                target = self.by_ip[args[1]]
        
                if args[2] != str(target.port_config["vsh"]):
                    if args[2] in target.port_config.values():
                        iosout = "Error! Address responded with different protocol."
                        return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)

                    iosout = "Error! Connection refused."
                    return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                
                self.direct_send((target.ip, target.port_config["vsh"]), (vm.ip, 2222), f"connect {args[3]}")
                self.vsh(target)
                
                answer = self.recv(2222, vm)
                print(answer.content)

                if answer.content != "accept":
                    iosout = f"Access denied! Incorrect credentials."
                    return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)

                vm.forward_to[packet.source[0]] = (target.ip, target.port_config["vsh"])

                iosout = f"Connected to {target.nick}({target.ip})"
                return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                
            elif len(args) >= 3 and args[1] == '<':
                if args[0].endswith(".sys") is True:
                    iosout = f"Access denied."
                    return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                
                if len(args[0]) > FILENAME_LIMIT:
                    iosout = f"Incorrect filename."
                    return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                
                if len(vm.files) >= 20 and not args[0] in vm.files.keys():
                    iosout = f"Max files amount reached."
                    return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                
                if args[0] in vm.files.keys():
                    iosout = "File updated."
                else:
                    iosout = "File has been created."
                
                vm.files[args[0]] = ' '.join(args[2:])

                return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)

            else:
                iosout = "Error! Command not found."
                return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
        
        else: # if not logged in:
            if args[0] == "connect":
                if len(args) != 2:
                    iosout = "args"
                    return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                if md5(args[1].encode('ascii')).hexdigest() != vm.files["shadow.sys"]:
                    vm.add_to_log(f"Connection failed from {packet.source[0]}.")
                    
                    iosout = "credentials"
                    return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)

                vm.add_to_log(f"{packet.source[0]} has just connected.")
                
                iosout = "accept"
                vm.logged_in.append(packet.source[0])
                return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
            
            elif args[0] == "expl":
                
                #"exploit <id> <nick> <secret>"
                print(args)

                if len(args) != 4 or args[1].isdigit() is False:
                    iosout = "args"
                    return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)

                iosout = self.handle_exploit(vm, int(args[1]), args[2], args[3])
                
                if iosout == "vsh":
                    iosout = vm.cat("shadow.sys")
                elif iosout == "kernel":
                    iosout = f"accept"
                    vm.logged_in.append(packet.source[0])
                
                return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                
            elif args[0] == "ping":
                iosout = "VSH"
                return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)

            else:
                iosout = "access denied"
                return self.direct_send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)

    def vm_miner(self, vm: VM):
        answer: Packet = None
        
        self.direct_send((SYSTEM_IP, SYSTEM_PORTS["mine"]), (vm.ip, 7676), f"{random.randint(0, MAX_CV_HASH)} {vm.files['miner.config']}")

        if 7676 in vm.network.keys():
            answer = self.recv(7676, vm)
            
            if answer.source[0] == SYSTEM_IP and answer.content == "found":
                vm.add_to_log(f"Found {FOUND_CV_AMOUNT + vm.software['miner']} [CV] by miner.")
    
    def start_ai(self, nick: str, args: list[str]) -> str:
        vm: VM = self.by_nick[nick]
        lvl: int = None

        if len(args) != 2:
            return error(0, 1)
        
        if args[1] == "max":
            lvl = vm.software["AI"]
        else:
            if args[1].isdigit() is False:
                return error(1, 1)
            
            lvl = int(args[1])

        if self.by_nick[nick].software["AI"] < lvl:
            return error(2, 2)

        if len(self.by_nick[nick].exploits) >= MAX_EXPLOITS_AMOUNT:
            return error(3)

        # self.by_nick[nick].files["AI.proc"] = f"{int(time())} {lvl}"
        vm.cpu.append(Process("ai", "pass"))
        vm.cpu[len(vm.cpu) - 1].memory["time"] = int(time())
        vm.cpu[len(vm.cpu) - 1].memory["lvl"] = lvl

        return "Searching for vulnerabilities..."

    def vm_ai(self, vm: VM, process: Process):
        start_time: int = process.memory["time"]
        lvl: int = process.memory["lvl"]

        if start_time + AI_TIME <= int(time()):
            # produce a random exploit (take a look at VM.exploits for a template)
            vm.exploits.append(Exploit(randint(0, len(EXPLOITS) - 1), lvl, randint(0, len(OS_LIST) - 1), randint(50, 100)))
            
            process.kill()
            
            print(f"Exploit found by {vm.nick}!")
            self.notifications.append((vm.squad, vm.nick, "Exploit found."))

    def start_bf(self, nick: str, hashed: str) -> str:

        self.by_nick[nick].cpu.append(Process("bf", "pass"))
        self.by_nick[nick].cpu[len(self.by_nick[nick].cpu) - 1].memory["hash"] = hashed
        self.by_nick[nick].cpu[len(self.by_nick[nick].cpu) - 1].memory["principle"] = 0
        
        return "Started brutforce on the hash."

    def vm_bf(self, vm: VM, process: Process):
        guess: str = ""
        principle: int = None
        
        principle = process.memory["principle"]

        if principle > MAX_GUESS:
            vm.add_to_log("Bruteforce failed.")
            self.notifications.append((vm.squad, vm.nick, "Bruteforce failed."))
            
            process.name = "temp"
            process.code = ["exit", ]
            return

        for i in range(0, PASSWD_LENGHT):
            guess += PASSWDS_ALPHABET[principle % len(PASSWDS_ALPHABET)]
            principle = principle // len(PASSWDS_ALPHABET)

        #print(guess)
        if md5(guess.encode("ascii")).hexdigest() == process.memory["hash"]:
            vm.add("pass.txt", f"{process.memory['hash']} => {guess}", True)
            vm.add_to_log("Bruteforce completed.")
            self.notifications.append((vm.squad, vm.nick, f"Bruteforce completed.\nPassword: {guess}\nAlso you can check > cat pass.txt to see the resoult."))

            process.name = "temp"
            process.code = ["exit", ]
            return
        
        process.memory["principle"] += 1

    def start_scan(self, vm: VM, target_ip: str) -> str:
        if not target_ip in self.by_ip.keys():
            return "Target not found."
        
        vm.cpu.append(Process("scan", "pass"))
        vm.cpu[len(vm.cpu) - 1].memory["ip"] = target_ip
        vm.cpu[len(vm.cpu) - 1].memory["recv"] = 0

        return "Scan started... Check > cat scan.txt to see the resoults."
    
    def vm_scan(self, vm: VM, process: Process):
        answer: Packet = None

        if process.memory["recv"] == 0:
            process.memory["recv"] = 1
            
            for port in range(1, 100):
                self.direct_send((process.memory["ip"], port), (vm.ip, int(f"{port}{port}")), "ping")

        else:
            vm.files["scan.txt"] = f"Target: {process.memory['ip']}\nOS: {OS_LIST[self.by_ip[process.memory['ip']].os]}\n{25 * '_'}\n\n\tPORT  ANSWER\n"
            
            # if "target.config" in vm.files.keys() and vm.files["target.config"].count('\n') == 0:
            #     vm.add("target.config", OS_LIST[self.by_ip[process.memory['ip']].os])

            for port in range(1, 100):
                answer = self.recv(int(f"{port}{port}"), vm)
                
                if answer == None:
                    continue
                
                vm.files["scan.txt"] += f"\t{port:<2}:    {answer.content}\n{25 * '_'}"
            
            process.name = "temp"
            process.code = ["exit", ]

    def sell_exploit(self, vm: VM, price: int, exploit_id: int) -> bool:
        if exploit_id >= len(vm.exploits):
            return False
        
        self.offers.append(Offer(vm.nick, OFFER_TYPES["exploit"], price, vm.exploits.pop(exploit_id)))

        return True

    def buy(self, offer_id: int, buyer: str) -> str:
        
        if self.offers[offer_id].type == OFFER_TYPES["update"] and self.by_nick[buyer].software[self.offers[offer_id].content] >= MAX_SOFTWARE[self.offers[offer_id].content]:
            return error(4, 3)

        if self.offers[offer_id].type == OFFER_TYPES["exploit"] and len(self.by_nick[buyer].exploits) >= MAX_EXPLOITS_AMOUNT:
            return error(4, 4)
        
        if self.transfer(self.offers[offer_id].price, self.offers[offer_id].seller, buyer) is False:
            return error(4, 5)
        

        if self.offers[offer_id].type == OFFER_TYPES["update"]:
            self.by_nick[buyer].software[self.offers[offer_id].content] += 1

        if self.offers[offer_id].type == OFFER_TYPES["exploit"]:
            self.offers[offer_id].content.reset()

            self.by_nick[buyer].exploits.append(self.offers[offer_id].content)
            
            self.offers.pop(offer_id)

        return f"{buyer} has just bought #{offer_id} from exchange."

    def __generate_ip__(self) -> str:
        ip: str = f"{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
        
        while ip in self.by_ip.keys() or ip == SYSTEM_IP:
            ip = f"{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"

        return ip

    def __generate_password__(self) -> str:
        return "".join(choices(PASSWDS_ALPHABET, k=PASSWD_LENGHT))


    def direct_send(self, destination: tuple, source: tuple, content: str) -> str:
        new_line_char: str = '\n'
        replacement: str = "\n\t"

        if destination[0] in self.by_ip.keys():
            self.by_ip[destination[0]].network[destination[1]] = Packet(source, content)
            
            if not source[0] in self.by_nick.keys():
                self.by_ip[destination[0]].add("network.dump", f"{str(source):<24} | {content.replace(new_line_char, replacement)}", True)

        elif destination[0] == SYSTEM_IP:
            self.system_network[destination[1]] = Packet(source, content)
        
        return content

    def recv(self, port: int, vm: VM=None) -> Packet:
        if vm != None:
            if not port in vm.network.keys():
                return None

            return vm.network.pop(port)
        else:
            if not port in self.system_network.keys():
                return None

            return self.system_network.pop(port)

    def set_passwd(self, nick: str):
        self.by_nick[nick].files["shadow.sys"] = md5(self.__generate_password__().encode('ascii')).hexdigest()

    def change_nick(self, current_nick: str, new_nick: str) -> bool:
        squad_name: str = None
        ip: str = None

        if not current_nick in self.by_nick.keys():
            return False
        
        if new_nick in self.by_nick.keys():
            return False
        
        self.by_nick[new_nick] = self.by_nick.pop(current_nick)

        self.by_nick[new_nick].nick = new_nick
        self.by_nick[new_nick].logged_in = [new_nick, ]
        self.by_nick[new_nick].files["miner.config"] = new_nick
        self.by_nick[new_nick].forward_to = {}

        ip = self.by_nick[new_nick].ip
        self.by_ip[ip] = self.by_nick[new_nick]

        squad_name = self.by_nick[new_nick].squad
        
        if squad_name == None:
            return True

        self.squads[squad_name].members[new_nick] = self.squads[squad_name].members.pop(current_nick)

        return True

    def cpu_loop(self):
        cmd: tuple = None
        name: str = None
        pid: int = None

        while self.running is True:
            for vm in self.by_nick.values():
                # self.vm_bf(vm)
                
                # self.vm_miner(vm)
                # self.sys_mine()
                pid = 0
                
                while pid < len(vm.cpu):
                    cmd = vm.cpu[pid].cmd()
                    name = vm.cpu[pid].name

                    if name == "miner":
                        for _ in range(0, (vm.software["miner"] // 4) + 1):
                            self.vm_miner(vm)
                            self.sys_mine()
                    
                    elif name == "scan":
                        self.vm_scan(vm, vm.cpu[pid])

                    elif name == "vsh":
                        self.vsh(vm)

                    elif name == "bf":
                        self.vm_bf(vm, vm.cpu[pid])
                    
                    elif name == "ai":
                        self.vm_ai(vm, vm.cpu[pid])
                    
                    
                    elif cmd[0] == "exit":
                        vm.cpu.pop(pid)
                        continue

                    else:
                        vm.execute(pid)
                    
                    vm.cpu[pid].forward()
                    pid += 1    

                for packet in vm.netout:
                    self.direct_send(packet.source, (vm.ip, int(f"{packet.source[1]}{packet.source[1]}")))

            sleep(FREQUENCY)

    def add_vm(self, old_name: str, nick: str, os: int, squad: str):
        ip: str = self.__generate_ip__()
        #password: str = self.__generate_password__()
        
        self.by_nick[nick] = VM(nick, squad, ip, os)
        self.by_ip[ip] = self.by_nick[nick]

        self.set_passwd(nick)
        #self.by_nick[nick].files["shadow.sys"] = md5(password.encode('ascii')).hexdigest()
        
        self.squads[squad].members[nick] = self.squads[squad].members.pop(old_name)

    def add_squad(self, name: str, leader: str):
        self.squads[name] = Squad(name, {}, True)
        self.squads[name].members[leader] = RANKS["leader"]

    def save(self):
        db: shelve.Shelf = None
        vms: list = []
        squads: list = []

        for vm in self.by_nick.values():
            vms.append(vm.export())
        for squad in self.squads.values():
            squads.append(squad.export())
        
        db = shelve.open(self.__db_filename__, "w")
        db["vms"] = vms
        db["squads"] = squads
        db["bank"] = self.bank
        db["offers"] = self.offers
        db.close()
