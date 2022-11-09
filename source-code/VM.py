
class VM:
    '''class that represents single virtual machine'''
    nick: str = None
    squad: str = None
    ip: str = None

    software: dict = None
    files: dict = None

    network: dict = None
    processor: dict = None #{(file, line): cmd}


    def __init__(self, nick: str, squad: str, ip: str, software: dict, files: dict):
        self.nick = nick
        self.squad = squad
        self.ip = ip
        self.software = software
        self.files = files

    def export(self):
        return {
            "nick": self.nick,
            "squad": self.squad,
            "ip": self.ip,
            "software": self.software,
            "files": self.files,
        }