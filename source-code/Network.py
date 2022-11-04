import shelve
from Squad import Squad
from VM import VM


class Network:
    '''class for handling virtual network'''
    
    vms: list = None
    squads: list = None

    by_ip: dict = None
    by_nick: dict = None

    def __init__(self):
        pass
    