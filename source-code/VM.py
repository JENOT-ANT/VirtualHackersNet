from hashlib import md5
from time import gmtime, asctime
from random import randint
from uuid import uuid4, UUID


OS_LIST: tuple[str, ...] = ("Penguin", "Parrot", "Racoon", "Turtle", )
EXPLOITS: tuple[str, ...] = ("kernel", "vsh", )
# EXPLOIT: dict = {
#     "secret": 4,
# }

MAX_SOFTWARE: dict = {
    "vtp": 100,
    "miner": 26,
    "AI": 100,
    "kernel": 100,
    "vsh": 100,
    "dns": 1,
}

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
    "log.sys": "VM Created, Welcome!\n",
    "shadow.sys": md5("admin".encode('ascii')).hexdigest(),
    "network.dump": "-- Network Traffic --",
}

VM_HELP: str = """
# Commands:
  
  ## Local (can be executed only on your VM):
    
    - $bf <hash> --------------> brutforce hash to find password

    - $whois <IP> -------------> display squad and nick of the player with that IP
    
    - $time -------------------> display server time
    
    - $ai <lvl> ---------------> generate random exploit of the level (lvl <= AI)

    - $archives ---------------> [🗃] list owned exploits

  ## General:

    - >help -------------------> [❔] display this commands' help message
    
    - >panel ------------------> [📟] display dashboard with info about the machine
    
    - >transfer <nick><value> -> transfer <value> of CV to the VM of the <nick> player

    - >close ------------------> [🛡] close external vsh connections to your VM
  
  ## Files:

    - >ls ---------------------> [📁] list files of currently logged user
    
    - >cat <filename> ---------> display content of the file
  
  ## VSH:

    - >exploit <IP><port><ID> -> run the exploit (with ID, check $archives first)
    
    - >vsh <IP><port><passwd> -> connect to IP's VM (Virtual Machine)

    - >whoami -----------------> display currently-logged user's nick and IP
  
    - >exit -------------------> close last vsh connection
  
    - >proxy ------------------> display your vsh connection path

"""

MAX_FILE_SIZE: int = 20


class Packet:
    source: tuple = None
    content: str = None

    def __init__(self, source: tuple, content: str):
        self.source = source
        self.content = content


class Process:
    system: bool = None 
    cmds: list[tuple[str]] = None
    pointer: int = None
    #memory: dict[str] = None

    def __init__(self, cmds: list[tuple[str]], system: bool):
        self.cmds = cmds
        self.system = system
        self.pointer = 0
        #self.memory = []
        self.indexes = {}

    def pop(self) -> tuple[str]:
        cmd: tuple[str] = self.cmds[self.pointer]
        
        self.pointer += 1
        self.pointer = self.pointer % len(self.cmds)
        
        return cmd


class Exploit:
    category: int = None
    lvl: int = None
    os: int = None
    success_rate: int = None
    secret: UUID = None

    def __init__(self, category: int, lvl: int, os: int, success_rate: int, secret: UUID):
        self.category = category
        self.lvl = lvl
        self.os = os
        self.success_rate = success_rate
        self.secret = secret
    
class VM:
    '''class that represents single virtual machine'''
    nick: str = None
    squad: str = None
    ip: str = None
    os: int = None
    wallet: int = None
    #t_zone: int = None

    software: dict = None#{vtp, miner, AI, kernel, vsh, dns}
    files: dict[str, str] = None
    exploits: list[Exploit] = None#list[tuple[int, int, int, int, int]] = None # [(category<EXPLOITS>, lvl, os<OS_LIST>, success_rate<50-80>, secret<0-100>[to prevent unpriviliged useage])]

    network: dict = None
    processor: list[Process] = None

    port_config: dict = None#{software: port}
    logged_in: list = None
    forward_to: dict[str, tuple] = None#{user-from-logged_in: target-address}


    def add(self, file_name: str, content: str, overwrite: bool=False) -> str:
        lines_amount: int = self.files[file_name].count('\n') + 2

        if file_name in self.files.keys():
            if lines_amount <= MAX_FILE_SIZE:
                self.files[file_name] += f"\n{content}"
            else:
                if overwrite is True:
                    self.files[file_name] += f"\n{content}"
                    self.files[file_name] = '\n'.join(self.files[file_name].splitlines()[lines_amount - MAX_FILE_SIZE:])

                return "Failed to add! Max file size reached."
        else:
            self.files[file_name] = content
        
        return "File has been updated."
    
    def add_to_log(self, content: str):
        self.add("log.sys", f"o [{gmtime().tm_mon:0>2}/{gmtime().tm_mday:0>2}; {gmtime().tm_hour:0>2}:{gmtime().tm_min:0>2}] -> {content}", True)
        
        #lines_amount: int = self.files["log.sys"].count('\n') + 2
        
        # self.files["log.sys"] += f"\no [{gmtime().tm_mon:0>2}/{gmtime().tm_mday:0>2}; {gmtime().tm_hour:0>2}:{gmtime().tm_min:0>2}] -> {content}"

        # if lines_amount > 20:
        #     self.files["log.sys"] = "\n".join(self.files["log.sys"].splitlines()[lines_amount - 20:])

    def start(self, code: str, by_system=False):
        cmds: list[tuple[str]] = []

        for line in code.splitlines():
            if line != '':
                cmds.append(tuple(line.split()))

        self.processor.append(Process(cmds, by_system))

    def help(self) -> str:
        return VM_HELP
    
    def ls(self) -> str:
        # files: str = '\n'.join(list(self.files.keys()))
        files: str = ""

        for filename in self.files.keys():
            if filename.endswith(".proc"):
                continue
            
            files += f"\t{filename}\n"

        return f"Files at {self.nick}({self.ip}):\n{files}"

    def cat(self, filename: str) -> str:
        if not filename in self.files.keys():
            return "Error! File not found."

        return f"'{filename}' at {self.nick}({self.ip}):\n{self.files[filename]}"

    def whoami(self) -> str:
        return f"{self.nick} {self.ip}"
    
    def archives(self) -> str:
        output: str = " ID |   TYPE   | LVL |    OS    | SUCCESS\n=========================================\n"

        for i in range(0, len(self.exploits)):
            # output += f"{i:^4}|{EXPLOITS[self.exploits[i][0]]:^10}|{self.exploits[i][1]:^5}|{OS_LIST[self.exploits[i][2]]:^10}|{f'{self.exploits[i][3]} %':^10}\n"
            output += f"{i:^4}|{EXPLOITS[self.exploits[i].category]:^10}|{self.exploits[i].lvl:^5}|{OS_LIST[self.exploits[i].os]:^10}|{f'{self.exploits[i].success_rate} %':^10}\n"

        return output

    def dashboard(self) -> str:
        lines: list = self.files["log.sys"].splitlines()
        lines_amount: int = len(lines)
        line1: str = None
        line2: str = None
        line3: str = None
        bf_state: str = "off"
        ai_state: str = "off"
        
        if lines_amount >= 1:
            line1 = lines[lines_amount - 1][20:]
        if lines_amount >= 2:
            line2 = lines[lines_amount - 2][20:]
        if lines_amount >= 3:
            line3 = lines[lines_amount - 3][20:]
        
        if "BF.proc" in self.files.keys() and self.files["BF.proc"] != "False":
            bf_state = "on"
        if "AI.proc" in self.files.keys() and self.files["AI.proc"] != "False":
            ai_state = "on"

        return f"""
_______________________________________
|>{                self.whoami():^35}<|
|-------------------------------------|
|{f'{self.wallet} [CV]':<12} {asctime(gmtime()):>24}|
|=====================================|
|{f'OS ({OS_LIST[self.os]}): {self.software["kernel"]}':^18}|{f'Miner: {self.software["miner"]}':^18}|
|{f'AI: {self.software["AI"]}':^18}|{f'vsh: {self.software["vsh"]}':^18}|
|=====================================|
| {f'BrutForce: {bf_state}':^16} | {f'AI: {ai_state}':^16} |
|{               'Latest-Events':=^37}|
|{                          line1:^37}|
|{                          line2:^37}|
|{                          line3:^37}|
|_____________________________________|
        """

    def exit(self, client_ip: str):
        if client_ip != self.nick:
            self.logged_in.remove(client_ip)

    def close(self):
        counter: int = 0

        for i in range(len(self.logged_in)):
            if self.logged_in[i] != self.nick:
                self.logged_in.pop(i)
                counter += 1
        
        return f"{counter} connection(s) closed."


    #def start(self, cmd: str, file: str=None, line: int=None):
    #    self.processor.append(Process(cmd, file, line))


    def __init__(self, nick: str, squad: str, ip: str, os: int, wallet: int=0, software: dict={}, files: dict={}, exploits: list=[], port_config: dict={}):
        self.nick = nick
        self.squad = squad
        self.ip = ip
        self.os = os
        self.wallet = wallet
        self.software = software
        self.files = files
        self.exploits = exploits
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
            "exploits": self.exploits,
            "port_config": self.port_config,
            #"time_zone": self.t_zone,
        }
