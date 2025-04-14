from app.game_config import PROGRAM_VERSION, PROGRAM_VERSION_DESCRIPTION
from app.field import Field
from app.player import Player
from app.node import Node
from app.solver import check_win

import copy
from typing import ForwardRef
from enum import Enum


class Game:
    class GameStates(Enum):
        CROSS_WON = 0
        NAUGHT_WON = 1
        CONTINUE = 2
        TIE = 3

    class InputCommandType(Enum):
        EXIT = 0
        MAKE_MOVE = 1
        ROLL_BACK = 2
        ERROR = 3

    def __init__(self) -> None:
        """
        Выводит информацию о игре
        """

        print("Welcome to the MxNxK game! :D")
        print(PROGRAM_VERSION, PROGRAM_VERSION_DESCRIPTION)

        self.current_state: ForwardRef("Node") = Node()

    def start_processing_input(self):
        """
        Принимает команды игрока
        """

        if (
            min(Field.HEIGHT, Field.WIDTH) < 1
        ):  # косяк. #TODO надо бы пользователя уведомить, В ЧЕМ ИМЕННО он не прав по жизни...
            return

        while True:
            self.__print_field()

            user_input = input(
                f"""                               
Enter <<[row_index] [column_index]>> to make a move to the selected square.
Enter <<-1>> to cancel a postposted move.
Enter <<Q>> to exit.

You are {Player.Icon[self.current_state.who_moves]}.
Your command is >   """
            )
            print()  # для красоты

            command_type: Game.InputCommandType = self.__process_input_command(
                user_input
            )
            if command_type == Game.InputCommandType.EXIT:
                return

    def __print_field(
        self,
    ) -> (
        None
    ):  # тут обрезаем длину номера до 3 символов. больше наш интерфейс не вывезет
        """
        Печатает игровое поле
        """

        """
        нужные локально функции
        """

        def __print_horizontal_line():
            for i in range(
                4 + (Field.WIDTH * 4) + 1
            ):  # клетка + левая граница дают 4 (первая клетка -- под №), одной границы не хватает
                print("-" if i % 4 else "+", end="")
            print()

        def __enumerate_columns():
            print(
                "|  №|"
                + "|".join([str(i)[-3:].rjust(3) for i in range(Field.WIDTH)])
                + "|"
            )

        def __print_row(row_index, row):
            print("|" + str(row_index)[-3:].rjust(3) + "| ", end="")  # нумеруем строки
            print(" | ".join(Player.Icon[cell] for cell in row), end=" |\n")

        """
        собственно печать игрового поля
        """
        __print_horizontal_line()
        __enumerate_columns()

        for row_index, row in enumerate(self.current_state.field):
            __print_horizontal_line()
            __print_row(row_index, row)

        __print_horizontal_line()

    def __is_correct_coordinates(self, user_input: str) -> bool:
        """
        Проверяет, является ли входящая строка корректными координатами данного поля
        """

        return len(user_input.split()) == 2 and all(
            [may_be_num.isalnum() for may_be_num in user_input.split()]
        )

    def __process_input_command(self, user_input: str) -> InputCommandType:
        """
        Обрабатывает входящие команды и классифицирует их
        """

        """
        нужные локально функции
        """

        def __say_goodbye() -> None:
            print("Have a good day!")

        def __go_back_to_parent(self) -> None:
            if self.current_state.parent:
                self.current_state = self.current_state.parent

                print("Magic roll back!")
            else:
                print("You can't roll back now!")

        def __catch_unexpected_command() -> None:
            print("Unexpected command. Try again please")

        """
        начинаем обработку ввода
        """
        if user_input == "Q":
            __say_goodbye()

            return Game.InputCommandType.EXIT

        if user_input == "-1":
            __go_back_to_parent()

            return Game.InputCommandType.ROLL_BACK

        if self.__is_correct_coordinates(user_input):
            row, column = map(int, user_input.split())
            self.__make_move(row, column)

            return Game.InputCommandType.MAKE_MOVE

        else:
            __catch_unexpected_command()

            return Game.InputCommandType.ERROR

    def __make_move(self, row: int, column: int) -> None:
        """
        Обрабатывает команду сделать ход
        """

        """
        нужные локально функции
        """

        def __wrong_ceil_chosen() -> None:
            print(
                f"Invalid coordinates! You must choose a free cell within [0, 0]--[{Field.HEIGHT - 1}, {Field.WIDTH - 1}]. Try again please"
            )

        def __successful_move() -> None:
            print("Nice move!")

        def __tie_happened() -> None:
            self.__print_field()
            print("Tie! Restarting the Game . . .", end="\n\n")

            self.__reset_game()

        def __someone_won(game_status: Game.GameStates) -> None:
            self.__print_field()

            winner = "Cross" if game_status == Game.GameStates.CROSS_WON else "Nought"
            print(f"{winner} won! Restarting the Game . . .", end="\n\n")

            self.__reset_game()

        """
        обработка хода начинается
        """
        if not (0 <= row < Field.HEIGHT and 0 <= column < Field.WIDTH):
            __wrong_ceil_chosen()
            return

        if self.current_state.field[row][column] == Player.Type.NONE:
            state_after_move: Node = Node()
            state_after_move.last_move = Field.Cell(row, column)
            state_after_move.field = copy.deepcopy(
                self.current_state.field
            )  # TODO точно ли нужно поле копировать?
            state_after_move.field[row][column] = self.current_state.who_moves
            state_after_move.free_cells_count = self.current_state.free_cells_count - 1
            state_after_move.parent = self.current_state
            state_after_move.who_moves = Player.Type(
                abs(self.current_state.who_moves.value - 1)
            )

            self.current_state = state_after_move

            game_status: Game.GameStates = self.__check_game_state()
            if game_status == Game.GameStates.CONTINUE:
                __successful_move()

            elif game_status == Game.GameStates.TIE:
                __tie_happened()

            else:
                __someone_won(game_status)
        else:
            __wrong_ceil_chosen()

    def __check_game_state(self) -> GameStates:
        """
        Проверяет состояние игры
        """

        if check_win(self.current_state):
            return (
                Game.GameStates.CROSS_WON
                if self.current_state.who_moves == Player.Type.NAUGHT
                else Game.GameStates.NAUGHT_WON
            )

        if self.current_state.free_cells_count == 0:
            return Game.GameStates.TIE

        return Game.GameStates.CONTINUE

    def __reset_game(self) -> None:
        """
        Сбрасывает игровое поле
        """

        self.current_state.who_moves = Player.Type.CROSS
        self.current_state.last_move = Field.Cell()
        self.current_state.field = [
            [Player.Type.NONE for _ in range(Field.WIDTH)] for _ in range(Field.HEIGHT)
        ]
        self.current_state.free_cells_count = Field.WIDTH * Field.HEIGHT

    # TODO заготовки под MCTS

    # def is_terminal(self):
    #     return self.__check_game_state() != GameStates.CONTINUE

    # def children(self):
    #     if not self.isTerminal():
    #         empty_cells = []
    #         for i in range(Field.HEIGHT):
    #             for j in range(Field.WIDTH):
    #                 empty_cells.append((i, j))
    #         return empty_cells
    #     return []

    # def get_reward(self):
    #     if self.isTerminal():
    #         if self.__check_game_state() == GameStates.CROSS_WON:
    #             return 1.0
    #         elif self.__check_game_state() == GameStates.NAUGHT_WON:
    #             return 0.0
    #         else:
    #             return 0.5
    #     return None

    # def get_current_player(self):
    #     return 1 if self._who_moves == Player.Type.CROSS else -1
