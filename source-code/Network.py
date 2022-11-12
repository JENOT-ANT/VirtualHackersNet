import shelve
from Squad import Squad
from VM import VM


class Network:
    '''class for handling virtual network'''
    
    squads: dict = None

    by_ip: dict = None
    by_nick: dict = None

    __db_filename__: str = None

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
