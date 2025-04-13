from app.game_config import Field, GameStates, PlayerType, PlayerIcon, Cell
from app.game_config import PROGRAM_VERSION, PROGRAM_VERSION_DESCRIPTION


class Game:
    _who_moves: PlayerType = PlayerType.CROSS
    _field: list[list[PlayerType]] = [[PlayerType.NONE for _ in range(Field.WIDTH)] for _ in range(Field.HEIGHT)]
    __free_cells_count: int = (Field.WIDTH * Field.HEIGHT)  # для быстрой проверки ничьей, TODO: сделать её умнее
    _last_move: Cell = Cell()


    def __init__(self) -> None:
        print("Welcome to the MxNxK game! :D")
        print(PROGRAM_VERSION, PROGRAM_VERSION_DESCRIPTION)


    def __get_coordinates(self) -> None:  # TODO как будто тут логика поломана немного... while (True) как будто в start_game() должен быть чтоли... пофикшу.
        """
        запрашивает координаты у пользователя
        """

        while True:  # TODO добавить возмножность завершать программу без помощи Ctrl + C :D
            try:
                user_input = input(
                    f"куда хотите походить? вы -- {PlayerIcon[self._who_moves]} (строка и столбец через пробел): "
                )
                
                row, column = map(int, user_input.split())
                if 0 <= row < Field.HEIGHT and 0 <= column < Field.WIDTH:
                    self._make_move(row, column)
                else:
                    print(
                        f"координаты должны быть в диапазоне от (0, 0) до ({Field.HEIGHT - 1}, {Field.WIDTH - 1}). попробуйте снова:"
                    )
            except ValueError:
                print("unexpected format. try again:")


    def __check_win(self) -> bool:
        """
        Проверяет, закончилась ли игра победой
        """
        DIRECTIONS = [
            (-1, 0), (-1, 1), (0, 1), (1, 1),
            (1, 0), (1, -1), (0, -1), (-1, -1)
        ]
        for direction in range(4):
            count = 1
            for _ in range(2):
                row = self._last_move.row + DIRECTIONS[direction][0]
                col = self._last_move.col + DIRECTIONS[direction][1]
                while (
                    0 <= row < Field.HEIGHT and
                    0 <= col < Field.WIDTH and
                    self._field[row][col] == self._field[self._last_move.row][self._last_move.col]
                ):
                    count += 1
                    row += DIRECTIONS[direction][0]
                    col += DIRECTIONS[direction][1]
                direction = (direction + 4) % 8
            if count >= Field.STREAK_TO_WIN:
                return True
        return False


    def __check_game_state(self) -> GameStates:
        """
        Проверяет состояние игры
        """
        if self.__check_win():
            return (GameStates.CROSS_WON if self._who_moves == PlayerType.CROSS else GameStates.NAUGHT_WON)
        if self.__free_cells_count == 0:
            return GameStates.TIE
        return GameStates.CONTINUE


    # TODO зачем?
    # def get_possible_actions(self):
    #     if not self.isTerminal():
    #         empty_cells = []
    #         for i in range(Field.HEIGHT):
    #             for j in range(Field.WIDTH):
    #                 empty_cells.append((i, j))
    #         return empty_cells
    #     return []


    def _print_field(self) -> None:
        """Выводит игровое поле на экран"""

        print("-" * (3 * Field.WIDTH + 1 * (Field.WIDTH + 1)))  # в каждой клетке по 3 символа, еще есть разделители
        # print("-" * (4 * Field.WIDTH - 1))
        for row in self._field:
            print("| ", end="")
            print(" | ".join(PlayerIcon[cell] for cell in row), end=" |\n")
            print("-" * (3 * Field.WIDTH + 1 * (Field.WIDTH + 1)))  # в каждой клетке по 3 символа, еще есть разделители
            # print("-" * (4 * Field.WIDTH - 1))


    def _make_move(self, row: int, column: int) -> None:
        """Обрабатывает ходы"""

        if self._field[row][column] == PlayerType.NONE:
            self._last_move = Cell(row, column)
            self._field[row][column] = self._who_moves
            self.__free_cells_count -= 1

            self._print_field()

            game_status: GameStates = self.__check_game_state()
            if game_status == GameStates.CONTINUE:
                self._who_moves = PlayerType(abs(self._who_moves.value - 1))

                self.__get_coordinates()
            elif game_status == GameStates.TIE:
                print("Tie!")

                self._reset_game()
            else:
                winner = "Cross" if game_status == GameStates.CROSS_WON else "Nought"
                print(f"{winner} won! Restarting the Game . . .")

                self._reset_game()
        else:
            print("ur bad! try again")
        

    def is_terminal(self):
        return self.__check_game_state() != GameStates.CONTINUE


    # def get_reward(self):
    #     if self.isTerminal():
    #         if self.__check_game_state() == GameStates.CROSS_WON:
    #             return 1.0
    #         elif self.__check_game_state() == GameStates.NAUGHT_WON:
    #             return 0.0
    #         else:
    #             return 0.5
    #     return None

    # TODO зачем?
    # def get_current_player(self):
    #     return 1 if self._who_moves == PlayerType.CROSS else -1


    def _reset_game(self) -> None:
        """reset"""

        self._who_moves = PlayerType.CROSS
        self._last_move = Cell()
        self._field = [[PlayerType.NONE for _ in range(Field.WIDTH)] for _ in range(Field.HEIGHT)]
        self.__free_cells_count = Field.WIDTH * Field.HEIGHT

        self._print_field()

    
    def start_game(self) -> None:
        """starts a game"""

        self._print_field()

        self.__get_coordinates()
