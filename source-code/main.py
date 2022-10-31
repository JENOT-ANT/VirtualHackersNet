from Server import Server
from os import chdir
from os.path import dirname


DATABASE_FILENAME: str = "vhn-database"
TOKEN_FILENAME: str = "discord-token.sec"


def main() -> None:
    server: Server = None
    
    chdir(f"{dirname(__file__)}/../game-data")

    server = Server()



if __name__ == "__main__":
    main()
