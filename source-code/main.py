from Server import Server
from os import chdir
from os.path import dirname


DATABASE_FILENAME: str = "vhn-database"
TOKEN_FILENAME: str = "discord-token.sec"

def load_token():
    token_file = None
    token: str = None

    token_file = open(TOKEN_FILENAME, 'r')
    
    token = token_file.read()
    token = token.removesuffix('\n')

    token_file.close()
    
    return token


def main() -> None:
    server: Server = None
    
    chdir(f"{dirname(__file__)}/../game-data")

    server = Server(DATABASE_FILENAME)
    server.start(load_token())


if __name__ == "__main__":
    main()
