import shelve
import random
from Squad import Squad
from VM import VM, Packet, Process
from hashlib import md5


class Network:
    '''class for handling virtual network'''
    
    squads: dict = None

    by_ip: dict = None
    by_nick: dict = None

    __db_filename__: str = None

    # def __connect__(self, address: tuple, passwd: str, source: tuple) -> str:
    #     target: VM = None

    #     target = self.by_ip[address[0]]
        
    #     if target.port_config["vsh"] != address[1]:
    #         if address[1] in target.port_config.values():
    #             return "Error! Address responded with different protocol."
    #         return "Error! Connection refused."
        
    #     self.send(address, source, f"connect {source[0]} {source[1]} {passwd}")
    #     return self.vsh(target)

    def vsh(self, vm: VM) -> str:
        packet: Packet = None
        answer: Packet = None
        target: VM = None
        args: list = None
        iosout: str = None

        packet = self.recv(vm, vm.port_config["vsh"])
        
        args = packet.content.split()

        if packet.source[0] in vm.logged_in:
            if packet.source[0] in vm.forward_to.keys():
                target = self.by_ip[vm.forward_to[packet.source[0]][0]]
                self.send((target.ip, vm.forward_to[packet.source[0]][1]), (vm.ip, 2222), packet.content)
                
                self.vsh(target)
                answer = self.recv(vm, 2222)
                
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

            elif args[0] == ">vsh":
                if len(args) != 4:
                    iosout = "Error! Incorrect amount of arguments. Check '>help' command."
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
                
                answer = self.recv(vm, 2222)
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
                    iosout = "credentials"
                    self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                    return iosout

                iosout = "accept"
                vm.logged_in.append(packet.source[0])
                self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                return iosout

            else:
                iosout = "Access denied! Not authenticated."
                self.send(packet.source, (vm.ip, vm.port_config["vsh"]), iosout)
                return iosout


    def __generate_ip__(self) -> str:
        ip: str = f"{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
        
        while ip in self.by_ip.keys():
            ip = f"{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"

        return ip

    def __load__(self):
        port_config: dict = None
        db: shelve.Shelf = shelve.open(self.__db_filename__, "r")
        
        for vm in db["vms"]:
            if "port_config" in vm.keys():
                port_config = vm["port_config"]
            else:
                port_config = {}
            
            self.by_nick[vm["nick"]] = VM(vm["nick"], vm["squad"], vm["ip"], vm["software"], vm["files"], port_config)
            self.by_ip[vm["ip"]] = self.by_nick[vm["nick"]]

        for squad in db["squads"]:
            self.squads[squad["name"]] = Squad(squad["name"], squad["members"], squad["recruting"])

        db.close()


    def __init__(self, db_filename: str):
        self.__db_filename__ = db_filename
        self.squads = {}
        self.by_ip = {}
        self.by_nick = {}
        self.__load__()

    def send(self, destination: tuple, source: tuple, content: str) -> None:
        if destination[0] in self.by_ip.keys():
            self.by_ip[destination[0]].network[destination[1]] = Packet(source, content)

    def recv(self, vm: VM, port: int) -> Packet:
        return vm.network.pop(port)

    def forward(self, ip: str) -> str:
        vm: VM = None
        iosout: str = None


        vm = self.by_ip[ip]

        for process in vm.processor:
            pass

        return iosout

    def add_vm(self, nick: str, password: str, squad: str, role: str):
        ip: str = self.__generate_ip__()
        self.by_nick[nick] = VM(nick, squad, ip, {}, {}, {})
        self.by_ip[ip] = self.by_nick[nick]

        self.by_nick[nick].files["shadow.sys"] = md5(password.encode('ascii')).hexdigest()
        
        self.squads[squad].members[nick] = role

    def add_squad(self, name: str):
        self.squads[name] = Squad(name, {}, True)

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
        db.close()
