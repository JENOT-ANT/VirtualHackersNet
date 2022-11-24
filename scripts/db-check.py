import shelve
from os import chdir
from os.path import dirname

GAME_DATA_DIR = "game-data"
DB_FILENAME: str = "vhn-database"

def main():
    db: shelve.Shelf = None

    chdir(f"{dirname(__file__)}/../{GAME_DATA_DIR}")
    
    db = shelve.open(DB_FILENAME, "r")
    for vm in db["vms"]:
        for attribute in vm.keys():
            print(f"{attribute}: {vm[attribute]}")

        print()

    print()

    for squad in db["squads"]:
        for attribute in squad.keys():
            print(f"{attribute}: {squad[attribute]}")

        print()

    print()
    print(db["bank"])
    db.close()

    

if __name__ == "__main__":
    main()
