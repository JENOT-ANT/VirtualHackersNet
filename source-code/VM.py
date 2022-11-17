
DEFAULT_SOFTWARE: dict = {
    "vtp": 1,
    "miner": 1,
    "AI": 1,
    "kernel": 1,
    "vsh": 1,
    "dns": 0,
}

DEFAULT_PORT_CONFIG: dict = {
    "vtp": 80,
    "vsh": 22,
}

DEFAULT_FILES: dict = {
    "log.sys": "o [----------] -> VM Created, Welcome!\n",
    "shadow.sys": str(hash("admin")),
}


class Packet:
    source: tuple = None
    content: str = None

    def __init__(self, source: tuple, content: str):
        self.source = source
        self.content = content


class Process:
    cmd: str = None
    file: str = None
    line: int = None

    def __init__(self, cmd: str, file: str=None, line: int=None):
        self.cmd = cmd
        self.file = file
        self.line = line


class VM:
    '''class that represents single virtual machine'''
    nick: str = None
    squad: str = None
    ip: str = None

    software: dict = None#{vtp, miner, AI, kernel, vsh, dns}
    files: dict = None

    network: dict = None
    processor: list = None

    port_config: dict = None#{software: port}

    def start(self, cmd: str, file: str=None, line: int=None):
        self.processor.append(Process(cmd, file, line))


    def __init__(self, nick: str, squad: str, ip: str, software: dict, files: dict, port_config: dict):
        self.nick = nick
        self.squad = squad
        self.ip = ip
        self.software = software
        self.files = files
        self.port_config = port_config
        self.processor = []
        self.network = {}

        self.start("vsh-server")

        for program_name in DEFAULT_SOFTWARE.keys():
            if not program_name in self.software.keys():
                self.software[program_name] = DEFAULT_SOFTWARE[program_name]
        
        for file_name in DEFAULT_FILES.keys():
            if not file_name in self.files.keys():
                self.files[file_name] = DEFAULT_FILES[file_name]
        
        for program in DEFAULT_PORT_CONFIG.keys():
            if not program in self.port_config.keys():
                self.port_config[program] = DEFAULT_PORT_CONFIG[program]

    def export(self):
        return {
            "nick": self.nick,
            "squad": self.squad,
            "ip": self.ip,
            "software": self.software,
            "files": self.files,
            "port_config": self.port_config,
        }
