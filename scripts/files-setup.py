import shelve
from os import chdir
from os import mkdir
from os import listdir
from os.path import dirname

GAME_DATA_DIR = "game-data"
DB_FILENAME: str = "vhn-database"
DC_TOKEN_FILENAME: str = "discord-token.sec"


def main():
    db: shelve.Shelf = None
    token_file = None
    chdir(f"{dirname(__file__)}/..")
    
    if not (GAME_DATA_DIR in listdir()):
        mkdir(GAME_DATA_DIR)
    
    chdir(GAME_DATA_DIR)
    
    if not (f"{DB_FILENAME}.dat" in listdir()):
        db = shelve.open(DB_FILENAME)
        db["vms"] = []
        db["squads"] = [{"name": "default", "members": []}]
        db.close()
    
    if not (DC_TOKEN_FILENAME in listdir()):
        token_file = open(DC_TOKEN_FILENAME, "w")
        token_file.write("Discord API token here!\n")
        token_file.close()
    
if __name__ == "__main__":
    main()
