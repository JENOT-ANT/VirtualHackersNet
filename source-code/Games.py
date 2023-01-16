
#  0 | 1 | 2
# ===========
# 3 | 4 | 5
# ===========
#  5 | 6 | 7

GAMES: dict[str, int] = {
    "None": -1,
    "TicTacToe": 0,
}

TTT: dict[str, int] = {
    "EMPTY": -1,
    'O': 0,
    'X': 1,
}

INT_2_TTT: tuple = ('O', 'X')


class TicTacToe:
    field: list[list[int]] = None
    size: int = None
    players: list = None
    win_condition: int = None

    turn: int = None
    winner: str = None

    def __init__(self, players: list[str], size: int=3, win_condition: int=3):
        self.players = players
        self.size = size
        self.field = [[TTT['EMPTY'] for j in range(self.size)] for i in range(self.size)]
        self.win_condition = win_condition
        self.turn = 0

    def is_correct_move(self, player: str, index: int) -> bool:
        if self.players[self.turn] != player:
            return False

        if index >= self.size ** 2 or self.field[index // self.size][index % self.size] != TTT['EMPTY']:
            return False
        
        return True

    def forward(self, index: int) -> bool:
        counter_x: int = 0
        counter_y: int = 0
        empty: int = 0

        self.field[index // self.size][index % self.size] = self.turn

        # rows and columns:
        for i in range(0, self.size):
            for j in range(0, self.size):
                if self.field[i][j] == TTT['EMPTY']:
                    empty += 1

                if self.field[i][j] == self.turn:
                    counter_x += 1
                else:
                    counter_x = 0

                if self.field[j][i] == self.turn:
                    counter_y += 1
                else:
                    counter_y = 0
                
                if counter_x == self.win_condition or counter_y == self.win_condition:
                    print(self.players[self.turn])
                    self.winner = self.players[self.turn]
                    return True
        
        # diagonal:
        counter_x = 0
        counter_y = 0

        for i in range(0, self.size):
            if self.field[i][i] == self.turn:
                counter_x += 1
            else:
                counter_x = 0

            if self.field[i][self.size - 1 - i] == self.turn:
                counter_y += 1
            else:
                counter_y = 0
            
            if counter_x == self.win_condition or counter_y == self.win_condition:
                self.winner = self.players[self.turn]
                print("diagonal")
                return True

        if empty == 0:
            print("draw")
            return True
        
        self.turn += 1
        self.turn = self.turn % len(self.players)

        #print(self.turn)

        return False

    def render(self) -> str:
        output: str = ""
        counter: int = 0

        for i in range(0, self.size):
            for j in range(0, self.size):
                if self.field[i][j] == TTT["EMPTY"]:
                    output += f"{'|' if j == (self.size -1) else ''} {str(counter)} {'|' if j == 0 else ''}"
                else:
                    output += f"{'|' if j == (self.size -1) else ''} {INT_2_TTT[self.field[i][j]]} {'|' if j == 0 else ''}"
                
                counter += 1
            
            if i != (self.size - 1):
                output += f"\n{(4 * self.size - 1) * '='}\n"
        
        return output

# class Games:
#     state: bool = None
#     game: str = None

#     ttt: TicTacToe = None

#     def __init__(self):
#         self.game = None
    
#     def handle_cmd(self, cmd: list, author: str) -> str:
#         if cmd[0] == "!stop":
#             return "Game over."
        
#         if cmd[0] == "!start":
            
#         if self.game == "TicTacToe":
#             if self.cmd[0] == "tic":
#                 self.move_ttt(int(cmd[1]))

#     def start_ttt(self, player1: str, player2: str):
#         self.game = "TicTacToe"
#         self.ttt = TicTacToe([player1, player2,])

#     def move_ttt(self, index: int) -> str:

#         if index >= self.game.size ** 2 or self.game.field[index // self.game.size][index % self.game.size] != TTT['EMPTY']:
#             return "Incorrect field."
        
#         if self.ttt.forward(index) is True:
#             return self.ttt.players[self.ttt.turn]
#         else:
#             return self.ttt.render()
    