import shelve
from os import chdir
from os.path import dirname

GAME_DATA_DIR = "game-data"
DB_FILENAME: str = "vhn-database"

def main():
    db: shelve.Shelf = None

    chdir(f"{dirname(__file__)}/../{GAME_DATA_DIR}")
    
    db = shelve.open(DB_FILENAME, "r")
    print(f"{tuple(db.keys())[0]}: {tuple(db.values())[0]}\n{tuple(db.keys())[1]}: {tuple(db.values())[1]}")
    db.close()

    

if __name__ == "__main__":
    main()
