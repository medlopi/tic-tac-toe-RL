from app.game_config import Field, GameStates, PlayerType, PlayerIcon


class Game:
    _next_move: PlayerType = PlayerType.CROSS
    _field: list[list[PlayerType]] = [[PlayerType.NONE for _ in range(Field.WIDTH)] for _ in range(Field.HEIGHT)]
    __free_cells_count: int = Field.WIDTH * Field.HEIGHT  # для быстрой проверки ничьей, TODO: сделать её умнее

    def __init__(self) -> None:
        print("Welcome to tic-tac-toe! :D")  # TODO: Нормальное приветствие?
        self._print_field()
        
        self.__get_coordinates()

    def __get_coordinates(self) -> None:
        """
        запрашивает координаты у пользователя
        """
        while True:
            try:
                user_input = input(f"куда хотите походить? вы -- {PlayerIcon[self._next_move]} (строка и столбец через пробел): ")
                row, column = map(int, user_input.split())

                if 0 <= row < Field.HEIGHT and 0 <= column < Field.WIDTH:
                    self._make_move(row, column)
                else:
                    print(f"координаты должны быть в диапазоне от (0, 0) до ({Field.HEIGHT - 1}, {Field.WIDTH - 1}). попробуйте снова:")
            except ValueError:
                print("unexpected format. try again:")

    def __check_game_state(self, row: int, column: int) -> GameStates:
        """
        Проверяет состояние игры
        """
        
        if not (Field.HEIGHT == 3 and Field.WIDTH == 3 and Field.STREAK_TO_WIN == 3):  # TODO: Это -- версия для 3x3, нужно сделать работающую с любым полем.
            return GameStates.ERROR

        # диагонали
        if (row == column and self._field[0][0] == self._field[1][1] == self._field[2][2] == self._next_move) or \
           (row + column == 2 and self._field[2][0] == self._field[1][1] == self._field[0][2] == self._next_move):
            return GameStates.CROSS_WON if self._next_move == PlayerType.CROSS else GameStates.NAUGHT_WON

        # строка
        if len(set(self._field[row])) == 1 and self._field[row][0] != PlayerType.NONE:
            return GameStates.CROSS_WON if self._field[row][0] == PlayerType.CROSS else GameStates.NAUGHT_WON

        # столбец
        column_values = set(self._field[i][column] for i in range(Field.HEIGHT))
        if len(column_values) == 1 and self._field[0][column] != PlayerType.NONE:
            return GameStates.CROSS_WON if self._field[0][column] == PlayerType.CROSS else GameStates.NAUGHT_WON
        
        # ничья ? 
        if self.__free_cells_count == 0:
            return GameStates.TIE

        return GameStates.CONTINUE

    def _print_field(self) -> None:
        """Выводит игровое поле на экран"""
        
        for row in self._field:
            print(" | ".join(PlayerIcon[cell] for cell in row))
            print("-" * (4 * Field.WIDTH - 1))

    def _make_move(self, row: int, column: int) -> None:
        """Обрабатывает ходы"""
        
        if self._field[row][column] == PlayerType.NONE:

            self._field[row][column] = self._next_move
            self.__free_cells_count -= 1
            self._print_field()

            game_status: GameStates = self.__check_game_state(row, column)
            if game_status == GameStates.ERROR:
                print("fatal error!")
            elif game_status == GameStates.CONTINUE:
                print(f"{PlayerIcon[self._next_move]}, u r welcome!")
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

    def _reset_game(self) -> None:
        """reset"""
        
        self._next_move = PlayerType.CROSS
        self._field = [[PlayerType.NONE for _ in range(Field.WIDTH)] for _ in range(Field.HEIGHT)]
        self.__free_cells_count = Field.WIDTH * Field.HEIGHT
        
        self._print_field()
