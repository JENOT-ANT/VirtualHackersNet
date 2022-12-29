from VM import VM


RECRUIT: int = 0
MASTER: int = 1
COLEADER: int = 2
LEADER: int = 3


class Squad:
    name: str = None
    members: dict[str, int] = None# {nick: role}
    recruting: bool = None

    def __init__(self, name: str, members: dict, recruting: bool):
        self.name = name
        self.members = members
        self.recruting = recruting

    def export(self) -> dict:
        return {
            "name": self.name,
            "members": self.members,
            "recruting": self.recruting,
        }
    