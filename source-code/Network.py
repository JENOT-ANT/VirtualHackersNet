import shelve
import random
from Squad import Squad
from VM import VM


class Network:
    '''class for handling virtual network'''
    
    squads: dict = None

    by_ip: dict = None
    by_nick: dict = None

    __db_filename__: str = None


    def __generate_ip__(self) -> str:
        ip: str = f"{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
        
        while ip in self.by_ip.keys():
            ip = f"{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"

        return ip

    def __load__(self):
        
        db: shelve.Shelf = shelve.open(self.__db_filename__, "r")
        
        for vm in db["vms"]:
            self.by_nick[vm["nick"]] = VM(vm["nick"], vm["squad"], vm["ip"], vm["software"], vm["files"])
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

    def add_vm(self, nick: str, password: str, squad: str):
        ip: str = self.__generate_ip__()
        self.by_nick[nick] = VM(nick, squad, ip, {}, {})
        self.by_ip[ip] = self.by_nick[nick]

        self.by_nick[nick].files["shadow.sys"] = str(hash(password))
        
        self.squads[squad].members.append(nick)

    def add_squad(self, name: str):
        self.squads[name] = Squad(name, [], True)

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
