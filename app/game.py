from app.game_config import PROGRAM_VERSION, PROGRAM_VERSION_DESCRIPTION, MAX_FIELD_SIZE_FOR_SOLVER
from app.field import Field, GameStates
from app.player import Player
from app.node import Node
from app.mcts import MCTSPlayer
from app.solver import get_position_status_and_best_move
import numpy as np

from typing import ForwardRef
from enum import Enum


class Game:

    class InputCommandType(Enum):
        EXIT = 0
        MAKE_MOVE = 1
        ROLL_BACK = 2
        ERROR = 3

    def __init__(self, mcts_player: MCTSPlayer) -> None:
        """
        Выводит информацию о игре
        """

        print("Welcome to the MxNxK game! :D")
        print(PROGRAM_VERSION, PROGRAM_VERSION_DESCRIPTION)
        self.mcts_player: MCTSPlayer = mcts_player
        self.current_state: ForwardRef("Node") = Node()


    def start_processing_input(self):
        """
        Принимает команды игрока
        """

        def __print_prediction_with_solver():
            pos, really_best_cell = get_position_status_and_best_move(self.current_state)
            print("Solver says that", really_best_cell.row, really_best_cell.col, really_best_cell.figure, "is a greate move")

        def __print_prediction_no_solver():
            maybe_best_cell: Field.Cell = self.mcts_player.get_move()
            print("MCTS says that", maybe_best_cell.row, maybe_best_cell.col, maybe_best_cell.figure, "a greate move")

        if (
            min(Field.HEIGHT, Field.WIDTH) < 1
        ):  # косяк. #TODO надо бы пользователя уведомить, В ЧЕМ ИМЕННО он не прав по жизни...
            return

        while True:
            self.__print_field()

            if max(Field.HEIGHT, Field.WIDTH) <= MAX_FIELD_SIZE_FOR_SOLVER:
                __print_prediction_with_solver()
            if self.current_state.who_moves == Player.Type.NAUGHT:
                __print_prediction_no_solver()
            print()

            user_input = input(
                f"""                               
Enter <<[row_index] [column_index] [figure_value]>> to make a move to the selected square.
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
            print(" | ".join(
                f'{cell:0{Field.COUNT_FEATURES}b}' if cell != -1 else '-' * Field.COUNT_FEATURES for cell in row
            ), end=" |\n")

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
        def __wrong_ceil_chosen() -> None:
            print(
                f"Invalid coordinates! You must choose a free cell within [0, 0]--[{Field.HEIGHT - 1}, {Field.WIDTH - 1}]. Try again please"
            )

        if len(user_input.split()) == 2 and all([may_be_num.isalnum() for may_be_num in user_input.split()]):
            row, column = [int(num) for num in user_input.split()]

            if (0 <= row and row < Field.HEIGHT) and (0 <= column and column < Field.WIDTH):
                return True
            else:
                __wrong_ceil_chosen()
            
        return False  # TODO не пересчитывать заново MC

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
            __go_back_to_parent(self)

            return Game.InputCommandType.ROLL_BACK
        
        # if self.__is_correct_coordinates(user_input):
        #     row, column = map(int, user_input.split())
            
        #     self.mcts_player.move_and_update(Field.Cell(row, column))
        #     self.__make_move(Field.Cell(row, column))

        #     return Game.InputCommandType.MAKE_MOVE

        # else:
        #     __catch_unexpected_command()

        #     return Game.InputCommandType.ERROR

        cell = Field.Cell(*map(int, user_input.split()))
            
        self.mcts_player.move_and_update(cell)
        self.__make_move(cell)

        return Game.InputCommandType.MAKE_MOVE

    def __make_move(self, cell: Field.Cell) -> None:
        """
        Обрабатывает команду сделать ход
        """

        """
        нужные локально функции
        """
        row, column, figure = cell.row, cell.col, cell.figure
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

        def __someone_won(game_status: GameStates) -> None:
            self.__print_field()

            winner = "Cross" if game_status == GameStates.CROSS_WON else "Nought"
            print(f"{winner} won! Restarting the Game . . .", end="\n\n")

            self.__reset_game()

        """
        обработка хода начинается
        """
        if not (0 <= row < Field.HEIGHT and 0 <= column < Field.WIDTH):
            __wrong_ceil_chosen()
            return

        if self.current_state.field[row][column] == -1:

            state_after_move = Node(
                parent=self.current_state,
                move=cell
            )

            self.current_state = state_after_move

            game_status: GameStates = self.current_state.check_game_state()
            if game_status == GameStates.CONTINUE:
                __successful_move()

            elif game_status == GameStates.TIE:
                __tie_happened()

            else:
                __someone_won(game_status)
        else:
            __wrong_ceil_chosen()

    def make_silent_move(self, cell: Field.Cell) -> None:
        if self.current_state.field[cell.row][cell.col] == -1:
            state_after_move = Node(
                parent=self.current_state,
                move=cell
            )
            self.current_state = state_after_move
        else:
            print("The cell is not empty")

    def start_self_play(self, player, temperature_contant: float = 1e-3):
        """ start a self-play game using a MCTS player, reuse the search tree,
        and store the self-play data: (state, mcts_probs, z) for training.
        player: MCTS_alphazero_player
        Also player.is_selfplay=True is needed
        """
        self.__reset_game()

        states, mcts_probs, current_players = [], [], []
        while True:
            move, move_probs = player.get_move(
                temperature_contant,
                return_prob=True
            )
            # store the data
            states.append(self.current_state.current_state())
            mcts_probs.append(move_probs)
            current_players.append(self.current_state.who_moves)
            # perform a move
            self.make_silent_move(move)
      
            game_state = self.current_state.check_game_state()
            if game_state != GameStates.CONTINUE:
                winner = self.current_state.define_winner(game_state)
                # winner from the perspective of the current player of each state
                winners_z = np.zeros(len(current_players))
                if winner != Player.Type.NONE:
                    winners_z[np.array(current_players) == winner] = 1.0
                    winners_z[np.array(current_players) != winner] = -1.0
                # reset MCTS root node
                player.reset_player()
                
                return winner, zip(states, mcts_probs, winners_z)
            

    def start_bot_play(self, player1, player2, start_player: int) -> Player.Type:
        """
        player1, player2: MCTS_alphazero_player | MCTS_pure_player
        """
        self.__reset_game()

        if start_player == 1:
            player1, player2 = player2, player1

        players = {
            Player.Type.CROSS: player1,
            Player.Type.NAUGHT: player2
        }
        current = self.current_state.who_moves
        opponent = Player.Type(abs(current.value - 1))

        while True:
            move = players[current].get_move()
            players[current].move_and_update(move)
            players[opponent].move_and_update(move)
            self.make_silent_move(move)

            game_state = self.current_state.check_game_state()
            if game_state != GameStates.CONTINUE:
                player1.reset_player()
                player2.reset_player()
                if game_state == GameStates.TIE:
                    return -1
                elif game_state == GameStates.CROSS_WON:
                    return start_player == 0
                else:
                    return start_player == 1
                
            current, opponent = opponent, current


    def __reset_game(self) -> None:
        """
        Сбрасывает игровое поле
        """
        self.current_state = Node()
        self.mcts_player.reset_player()
