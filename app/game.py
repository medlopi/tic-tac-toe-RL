from app.game_config import Field, GameStates, PlayerType, PlayerIcon
from app.game_config import PROGRAM_VERSION, PROGRAM_VERSION_DESCRIPTION


class Game:
    _next_move: PlayerType = PlayerType.CROSS
    _field: list[list[PlayerType]] = [[PlayerType.NONE for _ in range(Field.WIDTH)] for _ in range(Field.HEIGHT)]
    __free_cells_count: int = (Field.WIDTH * Field.HEIGHT)  # для быстрой проверки ничьей, TODO: сделать её умнее
    _last_move: tuple[int, int] = ()  # TODO как вам план отдельный класс для хранения координат написать? че то кринж какой то


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
                    f"куда хотите походить? вы -- {PlayerIcon[self._next_move]} (строка и столбец через пробел): "
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


    def __check_game_state(self) -> GameStates:  # TODO можно проверять состояние игры после каждой проверки (я не русский), а не в конце за раз все. еще можно проверку по last_move прикрутить
        """
        Проверяет состояние игры
        """
        row, column = self._last_move
        # главная диагональ
        main_diagonal_line = 1
        d = 1  # TODO зачем?
        while row + d < Field.HEIGHT and column + d < Field.WIDTH and self._field[row + d][column + d] == self._field[row][column]:
            main_diagonal_line += 1
            d += 1

        d = 1  
        while row - d >= 0 and column - d >= 0 and self._field[row - d][column - d] == self._field[row][column]:
            main_diagonal_line += 1
            d += 1

        # побочная диагональ
        side_diagonal_line = 1
        d = 1
        while row + d < Field.HEIGHT and column - d >= 0 and self._field[row + d][column - d] == self._field[row][column]:
            side_diagonal_line += 1
            d += 1

        d = 1 
        while row - d >= 0 and column + d < Field.WIDTH and self._field[row - d][column + d] == self._field[row][column]:
            side_diagonal_line += 1
            d += 1

        # Проверка вертикали
        vertical_line = 1
        d = 1
        while row + d < Field.HEIGHT and self._field[row + d][column] == self._field[row][column]:
            vertical_line += 1
            d += 1

        d = 1 
        while row - d >= 0 and self._field[row - d][column] == self._field[row][column]:
            vertical_line += 1
            d += 1

        # Проверка горизонтали
        horizontal_line = 1
        d = 1
        while column - d >= 0 and self._field[row][column - d] == self._field[row][column]:
            horizontal_line += 1
            d += 1

        d = 1 
        while column + d < Field.WIDTH and self._field[row][column + d] == self._field[row][column]:
            horizontal_line += 1
            d += 1

     
        if max(main_diagonal_line, side_diagonal_line, vertical_line, horizontal_line) >= Field.STREAK_TO_WIN:
            return (GameStates.CROSS_WON if self._next_move == PlayerType.CROSS else GameStates.NAUGHT_WON)
        
        
        # ничья ?
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


    def _print_field(self) -> None:  # TODO косячно выводит)))
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
            self._last_move = (row, column)
            self._field[row][column] = self._next_move
            self.__free_cells_count -= 1

            self._print_field()

            game_status: GameStates = self.__check_game_state()
            if game_status == GameStates.CONTINUE:
                self._next_move = PlayerType(abs(self._next_move.value - 1))

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
    #     return 1 if self._next_move == PlayerType.CROSS else -1


    def _reset_game(self) -> None:
        """reset"""

        self._next_move = PlayerType.CROSS
        self._last_move = ()
        self._field = [[PlayerType.NONE for _ in range(Field.WIDTH)] for _ in range(Field.HEIGHT)]
        self.__free_cells_count = Field.WIDTH * Field.HEIGHT

        self._print_field()

    
    def start_game(self) -> None:
        """starts a game"""

        self._print_field()

        self.__get_coordinates()
