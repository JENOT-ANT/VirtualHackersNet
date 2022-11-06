import shelve
from Squad import Squad
from VM import VM


class Network:
    '''class for handling virtual network'''
    
    squads: dict = None

    by_ip: dict = None
    by_nick: dict = None

    def __load__(self, db_filename: str):
        db = shelve.open(db_filename, "r")
        
        for vm in db["vms"]:
            self.by_nick[vm["nick"]] = VM(vm["nick"], vm["squad"], vm["ip"], vm["software"], vm["files"])
            self.by_ip[vm["ip"]] = self.by_nick[vm["nick"]]

        for squad in db["squads"]:
            pass

        db.close()


    def __init__(self):
        self.squads = {}
        self.by_ip = {}
        self.by_nick = {}

    