
class VM:
    '''class that represents single virtual machine'''
    nick: str = None
    squad: str = None
    ip: str = None

    badge: dict = None
    software: dict = None
    files: dict = None

    network: dict = None
    processor: dict = None #{(file, line): cmd}

    def __init__(self):
        pass