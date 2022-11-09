import shelve
from os import chdir
from os.path import dirname

DB_FILENAME: str = "vhn-database"
DC_TOKEN_FILENAME: str = "discord-token.sec"


def main():
    db: shelve.Shelf = None
    token_file = None
    chdir(f"{dirname(__file__)}/../game-data")
    
    db = shelve.open(DB_FILENAME)
    db["vms"] = {}
    db["squads"] = {}
    db.close()

    token_file = open(DC_TOKEN_FILENAME, "w")
    token_file.write("Discord API token here!\n")
    token_file.close()
    
if __name__ == "__main__":
    main()
