from VM import VM

class Squad:
    name: str = None
    members: list = None

    def __init__(self, name: str, members: list):
        self.name = name
        self.members = members

    def export(self) -> dict:
        return {
            "name": self.name,
            "members": self.members,
        }