from hashlib import md5
from time import gmtime, asctime

DEFAULT_SOFTWARE: dict = {
    "vtp": 1,
    "miner": 1,
    "AI": 1,
    "kernel": 1,
    "vsh": 1,
    "dns": 0,
}

# ports > 1000 are not allowed, they are for responding connections, np. respond from vsh: 2222, from vtp: 8080, etc.
DEFAULT_PORT_CONFIG: dict = {
    "vtp": 80,
    "vsh": 22,
}

DEFAULT_FILES: dict = {
    "log.sys": "o [--------------] -> VM Created, Welcome!\n",
    "shadow.sys": md5("admin".encode('ascii')).hexdigest(),
}

VM_HELP: str = """
# Commands:

  - >help -------------------> display this commands' help message
  - >panel ------------------> display dashboard with info about the machine
  - >ls ---------------------> list files of currently logged user
  - >cat <filename> ---------> display content of the file
  - >whoami -----------------> display currently-logged user's nick and IP
  - >exit -------------------> close last vsh connection
  - >vsh <IP><port><passwd> -> connect to IP's VM (Virtual Machine)
  - >proxy ------------------> display your vsh connection path
"""


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
    os: str = None
    wallet: int = None
    #t_zone: int = None

    software: dict = None#{vtp, miner, AI, kernel, vsh, dns}
    files: dict = None

    network: dict = None
    processor: list = None

    port_config: dict = None#{software: port}
    logged_in: list = None
    forward_to: dict = None#{user-form-logged_in: target-address}

    def add_to_log(self, content: str):
        lines_amount: int = self.files["log.sys"].count("\n") + 1
        
        self.files["log.sys"] += f"\no [{gmtime().tm_mon:0>2}/{gmtime().tm_mday:0>2}; {gmtime().tm_hour:0>2}:{gmtime().tm_min:0>2}] -> {content}"
        
        if lines_amount > 20:
            "\n".join(self.files["log.sys"].splitlines()[lines_amount - 20:])
            
    def help(self) -> str:
        return VM_HELP
    
    def ls(self) -> str:
        return f"Files at {self.nick}({self.ip}):\n{tuple(self.files.keys())}"

    def cat(self, filename: str) -> str:
        return f"'{filename}' at {self.nick}({self.ip}):\n{self.files[filename]}"

    def whoami(self) -> str:
        return f"{self.nick} {self.ip}"
    
    def dashboard(self) -> str:
        lines: list = self.files["log.sys"].splitlines()
        lines_amount: int = len(lines)
        line1: str = None
        line2: str = None
        line3: str = None
        
        if lines_amount >= 1:
            line1 = lines[lines_amount - 1][20:]
        if lines_amount >= 2:
            line2 = lines[lines_amount - 2][20:]
        if lines_amount >= 3:
            line3 = lines[lines_amount - 3][20:]
        
        return f"""
_______________________________________
|>{                self.whoami():^35}<|
|-------------------------------------|
|{f'{self.wallet} [CV]':<12} {asctime(gmtime()):>24}|
|=====================================|
|{f'OS ({self.os}): {self.software["kernel"]}':^18}|{f'Miner: {self.software["miner"]}':^18}|
|{f'AI: {self.software["AI"]}':^18}|{f'vsh: {self.software["vsh"]}':^18}|
|{               'Latest-events':=^37}|
|{                          line1:^37}|
|{                          line2:^37}|
|{                          line3:^37}|
|_____________________________________|
        """

    def exit(self, client_ip: str):
        self.logged_in.remove(client_ip)

    def start(self, cmd: str, file: str=None, line: int=None):
        self.processor.append(Process(cmd, file, line))


    def __init__(self, nick: str, squad: str, ip: str, os: str, wallet: int, software: dict, files: dict, port_config: dict):
        self.nick = nick
        self.squad = squad
        self.ip = ip
        self.os = os
        self.wallet = wallet
        self.software = software
        self.files = files
        self.port_config = port_config
        #self.t_zone = t_zone

        self.processor = []
        self.network = {}
        self.logged_in = [nick, ]
        self.forward_to = {}

        self.start("vsh-server")

        for program_name in DEFAULT_SOFTWARE.keys():
            if not program_name in self.software.keys():
                self.software[program_name] = DEFAULT_SOFTWARE[program_name]
        
        for file_name in DEFAULT_FILES.keys():
            if not file_name in self.files.keys():
                self.files[file_name] = DEFAULT_FILES[file_name]

        if not "miner.config" in self.files.keys():
            self.files["miner.config"] = self.nick

        for program in DEFAULT_PORT_CONFIG.keys():
            if not program in self.port_config.keys():
                self.port_config[program] = DEFAULT_PORT_CONFIG[program]

    def export(self):
        return {
            "nick": self.nick,
            "squad": self.squad,
            "ip": self.ip,
            "os": self.os,
            "wallet": self.wallet,
            "software": self.software,
            "files": self.files,
            "port_config": self.port_config,
            #"time_zone": self.t_zone,
        }
