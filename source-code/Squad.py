from VM import VM


MAX_MEMBERS: int = 12

RANKS: dict = {
    "recruit": 0,
    "master": 1,
    "coleader": 2,
    "leader": 3,
}

INT_TO_RANK: tuple = ("Squad-Recruit", "Squad-Master", "Squad-CoLeader", "Squad-Leader",)


class Squad:
    name: str = None
    members: dict[str, int] = None# {nick: role}
    recruting: bool = None

    def __init__(self, name: str, members: dict, recruting: bool):
        self.name = name
        self.members = members
        self.recruting = recruting

    def panel(self) -> str:
        output: str = None

        output = f"""
 ______________________________
|{               self.name:^30}|
|==============================|
|{f' members: {len(self.members)}/{MAX_MEMBERS}':<30}|
|{f' recruitment: {self.recruting}':<30}|
|==============================|"""

        for member in self.members.keys():
            output += f"\n|{member:^14}|{INT_TO_RANK[self.members[member]]:^15}|"

        output += "\n|______________________________|"

        return output


    def export(self) -> dict:
        return {
            "name": self.name,
            "members": self.members,
            "recruting": self.recruting,
        }
    