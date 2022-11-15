
DEFAULT_SOFTWARE: dict = {
    "vtp": 1,
    "miner": 1,
    "AI": 1,
    "kernel": 1,
    "vsh": 1,
    "dns": 0,
}

DEFAULT_FILES: dict = {
    "log.sys": "o [----------] -> VM Created, Welcome!\n",
    "shadow.sys": str(hash("admin")),
}

class VM:
    '''class that represents single virtual machine'''
    nick: str = None
    squad: str = None
    ip: str = None

    software: dict = None#{vtp, miner, AI, kernel, vsh, dns}
    files: dict = None

    network: dict = None
    processor: dict = None #{(file, line): cmd}


    def __init__(self, nick: str, squad: str, ip: str, software: dict, files: dict):
        self.nick = nick
        self.squad = squad
        self.ip = ip
        self.software = software
        self.files = files

        for program_name in DEFAULT_SOFTWARE.keys():
            if not program_name in self.software.keys():
                self.software[program_name] = DEFAULT_SOFTWARE[program_name]
        
        for file_name in DEFAULT_FILES.keys():
            if not file_name in self.files.keys():
                self.files[file_name] = DEFAULT_FILES[file_name]

    def export(self):
        return {
            "nick": self.nick,
            "squad": self.squad,
            "ip": self.ip,
            "software": self.software,
            "files": self.files,
        }
