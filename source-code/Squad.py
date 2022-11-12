from VM import VM

class Squad:
    name: str = None
    members: list = None
    recruting: bool = None

    def __init__(self, name: str, members: list, recruting: bool):
        self.name = name
        self.members = members
        self.recruting = recruting

    def export(self) -> dict:
        return {
            "name": self.name,
            "members": self.members,
            "recruting": self.recruting,
        }