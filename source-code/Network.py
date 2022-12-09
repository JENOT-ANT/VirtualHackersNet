import shelve
import random
from Squad import Squad
from VM import VM, Packet, Process
from hashlib import md5
from random import randint, choices
from time import sleep


FREQUENCY: int = 0.5
MAX_CV: int = int(1e9)
MAX_CV_HASH: int = 10000
FOUND_CV_AMOUNT: int = 4

PASSWD_LENGHT: int = 4
PASSWDS_ALPHABET: str = "02458AMPQYZ"

SYSTEM_IP: str = "0.0.0.0"

SYSTEM_PORTS: dict = {
    "mine": 76,
}

DEFAULT_OS: str = "Debian"

OFFER_TYPES: dict = {
    "update": 0,
    "exploit": 1,
    "ip_list": 2,
}

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
    offers: list = None
    squads: dict = None

    by_ip: dict = None
    by_nick: dict = None

    system: dict = None

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
            if self.transfer(FOUND_CV_AMOUNT + self.by_nick[args[1]].software["miner"], args[1]) is True:
                self.send((self.by_nick[args[1]].ip, 7676), (SYSTEM_IP, SYSTEM_PORTS["mine"]), "found")
            
            self.__cv_hash__ = str(randint(0, MAX_CV_HASH))

    def vsh(self, vm: VM) -> str:
        packet: Packet = None
        answer: Packet = None
        target: VM = None
        args: list = None
        iosout: str = None

        packet = self.recv(vm.port_config["vsh"], vm)
        
        args = packet.content.split()

        if packet.source[0] in vm.logged_in:
            if packet.source[0] in vm.forward_to.keys():
                target = self.by_ip[vm.forward_to[packet.source[0]][0]]
                self.send((target.ip, vm.forward_to[packet.source[0]][1]), (vm.ip, 2222), packet.content)
                
                self.vsh(target)
                answer = self.recv(2222, vm)
                
                if answer.content.split()[0] == "disconnect":
                    vm.forward_to.pop(packet.source[0])
                    iosout = f"Connection to {target.nick}({target.ip}) has been closed."
                    self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                    return iosout
                elif answer.content.split()[0] == "proxy":
                    iosout = f"{answer.content}<{vm.nick}"
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
                
                if not args[1] in vm.files.keys():    
                    iosout = "Error! File not found."
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

            elif args[0] == ">exit":
                vm.exit(packet.source[0])
                
                iosout = "disconnect"
                self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                return iosout
            
            elif args[0] == ">proxy":
                iosout = f"proxy {vm.nick}"
                
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

            else:
                iosout = "Access denied! Not authenticated."
                self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                return iosout
    
    def vm_miner(self, vm: VM):
        answer: Packet = None
        
        self.send((SYSTEM_IP, SYSTEM_PORTS["mine"]), (vm.ip, 7676), f"{random.randint(0, MAX_CV_HASH)} {vm.files['miner.config']}")

        if 7676 in vm.network.keys():
            answer = self.recv(7676, vm)
            
            if answer.source[0] == SYSTEM_IP and answer.content == "found":
                vm.add_to_log(f"Found {FOUND_CV_AMOUNT + vm.software['miner']} [CV] by miner.")
    
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

    def __load__(self):
        port_config: dict = None
        wallet: int = None
        os: str = None

        db: shelve.Shelf = shelve.open(self.__db_filename__, "r")
        
        for vm in db["vms"]:
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
            
            self.by_nick[vm["nick"]] = VM(vm["nick"], vm["squad"], vm["ip"], os, wallet, vm["software"], vm["files"], port_config)
            self.by_ip[vm["ip"]] = self.by_nick[vm["nick"]]

        for squad in db["squads"]:
            self.squads[squad["name"]] = Squad(squad["name"], squad["members"], squad["recruting"])

        if "bank" in db.keys():
            self.bank = db["bank"]

        db.close()


    def __init__(self, db_filename: str):
        self.running = True
        self.__db_filename__ = db_filename
        self.__cv_hash__ = str(randint(0, MAX_CV_HASH))
        self.squads = {}
        self.by_ip = {}
        self.by_nick = {}
        self.system = {}
        self.bank = MAX_CV
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
            self.system[destination[1]] = Packet(source, content)

    def recv(self, port: int, vm: VM=None) -> Packet:
        if vm != None:
            return vm.network.pop(port)
        else:
            return self.system.pop(port)

    def cpu_loop(self):

        while self.running is True:
            for vm in self.by_nick.values():
                self.vm_miner(vm)
                self.sys_mine()

                for _ in range(0, int(vm.software["miner"] / 2)):
                    self.vm_miner(vm)
                    self.sys_mine()
            
            sleep(FREQUENCY)

    def add_vm(self, old_name: str, nick: str, os: str, squad: str):
        ip: str = self.__generate_ip__()
        password: str = self.__generate_password__()
        
        self.by_nick[nick] = VM(nick, squad, ip, os, 0, {}, {}, {})
        self.by_ip[ip] = self.by_nick[nick]

        self.by_nick[nick].files["shadow.sys"] = md5(password.encode('ascii')).hexdigest()
        
        self.squads[squad].members[nick] = self.squads[squad].members.pop(old_name)

    def add_squad(self, name: str, leader: str):
        self.squads[name] = Squad(name, {}, True)
        self.squads[name].members[leader] = "Squad-Leader"

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
