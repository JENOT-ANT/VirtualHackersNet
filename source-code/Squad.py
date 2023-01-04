from VM import VM


RANKS: dict = {
    "recruit": 0,
    "master": 1,
    "coleader": 2,
    "leader": 3,
}


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
    