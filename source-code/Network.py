import shelve
import random
from Squad import Squad, RANKS
from VM import VM, Packet, OS_LIST, EXPLOITS, Exploit#, EXPLOIT
from hashlib import md5
from random import randint, choices
from time import sleep, time
from uuid import uuid4, UUID

FREQUENCY: float = 0.5
AI_TIME: int = 60 * 1
NOTIFICATION_CHANNEL: str = "terminal"
MAX_CV: int = int(1e9)
MAX_CV_HASH: int = 10000
FOUND_CV_AMOUNT: int = 4

PASSWD_LENGHT: int = 4
PASSWDS_ALPHABET: str = "02458AMPQYZ"
MAX_GUESS: int = len(PASSWDS_ALPHABET)**4

SYSTEM_IP: str = "0.0.0.0"

SYSTEM_PORTS: dict = {
    "mine": 76,
}

DEFAULT_OS: int = 0

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
    content: str = None


    def __init__(self, seller: str, type: int, price: int, content: str):
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
                self.send((self.by_nick[args[1]].ip, 7676), (SYSTEM_IP, SYSTEM_PORTS["mine"]), "found")
            
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

        if secret == None:
            secret = str(attacker.exploits[exploit_id].secret)

        self.send((target_ip, target_port), (vm.ip, 2222), f"exploit {exploit_id} {attacker_nick} {secret}")
        self.vsh(self.by_ip[target_ip])

        answer = self.recv(2222, vm).content
        
        if answer == "accept":
            vm.forward_to[packet_source_ip] = (target_ip, self.by_ip[target_ip].port_config["vsh"])
            
            return f"Connected to {self.by_ip[target_ip].nick}({target_ip})"

        return answer

    def handle_exploit(self, vm: VM, exploit_id: int, attacker_nick: str, secret: str) -> str:
        attacker: VM = None
        category: str = None

        if not attacker_nick in self.by_nick.keys():
            return "args"
        
        attacker = self.by_nick[attacker_nick]

        if exploit_id >= len(attacker.exploits):
            return "id"

        if str(attacker.exploits[exploit_id].secret) != secret:
            return "secret"

        if attacker.exploits[exploit_id].os != vm.os:
            return "no response"
        
        if EXPLOITS[attacker.exploits[exploit_id].category] == "vsh":
            if attacker.exploits[exploit_id].lvl < vm.software["vsh"]:
                return "failed"
            
            category = "vsh"

        else:
            if attacker.exploits[exploit_id].lvl < vm.software["kernel"]:
                return "failed"

            category = "kernel"

        if chance(attacker.exploits[exploit_id].success_rate) is True:
            return category
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

        #print(vm.logged_in)
        #print(vm.forward_to)

        if packet.source[0] in vm.logged_in:
            if packet.source[0] in vm.forward_to.keys():
                target = self.by_ip[vm.forward_to[packet.source[0]][0]]
                
                if args[0] == ">exploit" and packet.source[0] == vm.nick:
                    self.send((target.ip, vm.forward_to[packet.source[0]][1]), (vm.ip, 2222), f"{packet.content} {vm.nick} {vm.exploits[int(args[3])].secret}")
                else:
                    self.send((target.ip, vm.forward_to[packet.source[0]][1]), (vm.ip, 2222), packet.content)
                
                self.vsh(target)
                answer = self.recv(2222, vm)
                
                if answer.content.split()[0] == "disconnect":
                    vm.forward_to.pop(packet.source[0])
                    iosout = f"Connection to {target.nick}({target.ip}) has been closed."
                    self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                    return iosout

                elif answer.content.split()[0] == "proxy":
                    iosout = f"{answer.content} < {vm.nick}"
                    self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                    return iosout
                
                elif answer.content == "access denied":
                    vm.forward_to.pop(packet.source[0])
                    iosout = "Access denied! Not authenticated."
                    self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                    return iosout
                    
                iosout = answer.content
                self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                return iosout

            if args[0] == ">help":
                iosout = vm.help()
                self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                return iosout
            # elif args[0] == ">pass":
            #     self.by_nick[args[1]].files["shadow.sys"] = md5(args[2].encode('ascii')).hexdigest()
            #     return 'Password changed...'
            
            elif args[0] == ">ls":
                iosout = vm.ls()
                self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                return iosout

            elif args[0] == ">cat":
                if len(args) != 2:
                    iosout =  "Error! Incorrect amount of arguments. Check '>help' command."
                    self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                    return iosout

                iosout = vm.cat(args[1])
                self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                return iosout

            elif args[0] == ">whoami":
                iosout = vm.whoami()
                self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                return iosout

            elif args[0] == ">panel":
                iosout = vm.dashboard()
                self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                return iosout

            elif args[0] == ">exploit":
                #print(args)
                #print(f"{packet.source[0]} {vm.nick}")

                if (packet.source[0] != vm.nick and len(args) != 6) or (packet.source[0] == vm.nick and len(args) != 4):
                    iosout =  "Error! Incorrect amount of arguments. Check '>help' command."
                    self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                    return iosout
                
                if args[2].isnumeric() is False or args[3].isnumeric() is False:
                    iosout =  "Error! Incorrect values of the arguments. Check '>help' command."
                    self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                    return iosout
                
                if packet.source[0] != vm.nick:
                    iosout = self.exploit(vm, packet.source[0], args[1], int(args[2]), int(args[3]), args[4], args[5])
                
                else:
                    iosout = self.exploit(vm, packet.source[0], args[1], int(args[2]), int(args[3]))

                self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                return iosout

            elif args[0] == ">exit":
                vm.exit(packet.source[0])
                
                iosout = "disconnect"
                self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                return iosout
            
            elif args[0] == ">proxy":
                iosout = f"proxy {vm.nick}"
                
                self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                return iosout

            elif args[0] == ">close":
                iosout = vm.close()

                self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                return iosout

            elif args[0] == ">vsh":
                if len(args) != 4:
                    iosout = "Error! Incorrect amount of arguments. Check '>help' command."
                    self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                    return iosout
                
                if args[1] == SYSTEM_IP:
                    if args[2] in SYSTEM_PORTS:
                        iosout = "Error! Address responded with different protocol."
                        self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                        return iosout

                    iosout = "Error! Connection refused."
                    self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                    return iosout

                if not args[1] in self.by_ip.keys():
                    iosout = "Error! IP address not found or not responding!"
                    self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                    return iosout

                target = self.by_ip[args[1]]
        
                if args[2] != str(target.port_config["vsh"]):
                    if args[2] in target.port_config.values():
                        iosout = "Error! Address responded with different protocol."
                        self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                        return iosout

                    iosout = "Error! Connection refused."
                    self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                    return iosout
                
                self.send((target.ip, target.port_config["vsh"]), (vm.ip, 2222), f"connect {args[3]}")
                self.vsh(target)
                
                answer = self.recv(2222, vm)
                print(answer.content)

                if answer.content != "accept":
                    iosout = f"Access denied! Incorrect credentials."
                    self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                    return iosout

                vm.forward_to[packet.source[0]] = (target.ip, target.port_config["vsh"])

                iosout = f"Connected to {target.nick}({target.ip})"
                self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                return iosout
                    

            else:
                iosout = "Error! Command not found."
                self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                return iosout
        
        else:
            if args[0] == "connect":
                if len(args) != 2:
                    iosout = "args"
                    self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                    return iosout
                if md5(args[1].encode('ascii')).hexdigest() != vm.files["shadow.sys"]:
                    vm.add_to_log(f"Connection failed from {packet.source[0]}")
                    
                    iosout = "credentials"
                    self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                    return iosout

                vm.add_to_log(f"{packet.source[0]} has just connected.")
                
                iosout = "accept"
                vm.logged_in.append(packet.source[0])
                self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                return iosout
            
            if args[0] == "exploit":
                
                #"exploit <id> <nick> <secret>"
                print(args)

                if len(args) != 4 or args[1].isdigit() is False:
                    iosout = "args"
                    self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                    return iosout

                iosout = self.handle_exploit(vm, int(args[1]), args[2], args[3])
                
                if iosout == "vsh":
                    iosout = vm.cat("shadow.sys")
                elif iosout == "kernel":
                    iosout = f"accept"
                    vm.logged_in.append(packet.source[0])
                
                self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                return iosout
                
            else:
                iosout = "access denied"
                self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                return iosout
    

    def vm_miner(self, vm: VM):
        answer: Packet = None
        
        self.send((SYSTEM_IP, SYSTEM_PORTS["mine"]), (vm.ip, 7676), f"{random.randint(0, MAX_CV_HASH)} {vm.files['miner.config']}")

        if 7676 in vm.network.keys():
            answer = self.recv(7676, vm)
            
            if answer.source[0] == SYSTEM_IP and answer.content == "found":
                vm.add_to_log(f"Found {FOUND_CV_AMOUNT + vm.software['miner']} [CV] by miner.")
    
    def start_ai(self, nick: str, lvl: int) -> bool:
        if self.by_nick[nick].software["AI"] < lvl or lvl < 1 or len(self.by_nick[nick].exploits) >= 20:
            return False

        self.by_nick[nick].files["AI.proc"] = f"{int(time())} {lvl}"
        return True

    def vm_ai(self, vm: VM):
        start_time: int = None # int(vm.files["AI.proc"].split()[0])
        lvl: int = None # int(vm.files["AI.proc"].split()[1])
        
        if not "AI.proc" in vm.files.keys():
            return
        if vm.files["AI.proc"] == "False":
            return

        start_time = int(vm.files["AI.proc"].split()[0])
        lvl = int(vm.files["AI.proc"].split()[1])

        if start_time + AI_TIME <= int(time()):
            # produce a random exploit (take a look at VM.exploits for a template)
            vm.exploits.append(Exploit(randint(0, len(EXPLOITS) - 1), lvl, randint(0, len(OS_LIST) - 1), randint(50, 100), uuid4()))
            
            vm.files["AI.proc"] = "False"
            
            print(f"Exploit found by {vm.nick}!")
            self.notifications.append((vm.squad, vm.nick, "Exploit found."))

    def start_bf(self, nick: str, hashed: str) -> str:
        self.by_nick[nick].files["BF.proc"] = f"{hashed} 0"
        return "Started brutforce on the hash."

    def vm_bf(self, vm: VM):
        guess: str = ""
        hashed: str = None
        principle = None
        
        if not "BF.proc" in vm.files.keys():
            return
        if vm.files["BF.proc"] == "False":
            return

        hashed, principle = vm.files["BF.proc"].split()
        principle = int(principle)
        
        if principle > MAX_GUESS:
            vm.add_to_log("Bruteforce failed.")
            self.notifications.append((vm.squad, vm.nick, "Bruteforce faild."))
            vm.files["BF.proc"] = "False"
            return
        
        vm.files["BF.proc"] = f"{hashed} {principle + 1}"

        for i in range(0, PASSWD_LENGHT):
            guess += PASSWDS_ALPHABET[principle % len(PASSWDS_ALPHABET)]
            principle = principle // len(PASSWDS_ALPHABET)

        #print(guess)
        if md5(guess.encode("ascii")).hexdigest() == hashed:
            vm.files["BF.proc"] = "False"
            vm.add("pass.txt", f"{hashed} => {guess}")
            vm.add_to_log("Bruteforce completed.")
            self.notifications.append((vm.squad, vm.nick, "Bruteforce completed. Check >cat pass.txt to see the resoult."))

    def buy(self, id: int, buyer: str) -> str:

        if self.transfer(self.offers[id].price, self.offers[id].seller, buyer) is False:
            return "Purchase failed."
        else:
            if self.offers[id].type == OFFER_TYPES["update"]:
                self.by_nick[buyer].software[self.offers[id].content] += 1
            
            return f"{buyer} has just bought #{id} from exchange."

    def __generate_ip__(self) -> str:
        ip: str = f"{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
        
        while ip in self.by_ip.keys() or ip == SYSTEM_IP:
            ip = f"{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"

        return ip

    def __generate_password__(self) -> str:
        return "".join(choices(PASSWDS_ALPHABET, k=PASSWD_LENGHT))

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
        
        self.offers = [
            Offer(None, OFFER_TYPES["update"], 200, "kernel"),
            Offer(None, OFFER_TYPES["update"], 100, "vsh"),
            Offer(None, OFFER_TYPES["update"], 100, "AI"),
            Offer(None, OFFER_TYPES["update"], 300, "miner"),
        ]
        self.__load__()

    def send(self, destination: tuple, source: tuple, content: str) -> None:
        if destination[0] in self.by_ip.keys():
            self.by_ip[destination[0]].network[destination[1]] = Packet(source, content)
        
        elif destination[0] == SYSTEM_IP:
            self.system_network[destination[1]] = Packet(source, content)

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

    def cpu_loop(self):
        # cmd: tuple = None

        while self.running is True:
            for vm in self.by_nick.values():
                self.vm_bf(vm)
                self.vm_ai(vm)
                
                self.vm_miner(vm)
                self.sys_mine()

                for _ in range(0, int(vm.software["miner"] / 2)):
                    self.vm_miner(vm)
                    self.sys_mine()
                
                # for i in range(0, len(vm.processor)):
                #     cmd = vm.processor[i].pop()
                    
                #     if cmd[0] == "QUIT":
                #         pass

            
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

        db.close()

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
        db.close()
