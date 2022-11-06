import shelve
from os import chdir
from os.path import dirname


def main():
    db: shelve.Shelf = None
    chdir(f"{dirname(__file__)}/../game-data")
    
    db = shelve.open()

    
if __name__ == "__main__":
    main()
