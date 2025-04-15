from app.field import Field, GameStates
from app.player import Player
from typing import ForwardRef
import copy
import random

DIRECTIONS = [
    (-1, 0), (-1, 1), (0, 1), (1, 1),
    (1, 0), (1, -1), (0, -1), (-1, -1)
]

class Node:
    parent: ForwardRef("Node") = None
    who_moves: Player.Type = Player.Type.CROSS
    field: list[list[Player.Type]] = [
        [Player.Type.NONE for _ in range(Field.WIDTH)] for _ in range(Field.HEIGHT)
    ] 
    free_cells_count: int = Field.WIDTH * Field.HEIGHT
    last_move: Field.Cell = Field.Cell()

    def check_win(self) -> bool:
        """
        Проверяет, закончилась ли игра победой
        """

        if self.last_move.row == -1:
            return False
        
        for direction in range(4):
            count = 1

            for _ in range(2):
                row = self.last_move.row + DIRECTIONS[direction][0]
                col = self.last_move.col + DIRECTIONS[direction][1]

                while (
                    0 <= row < Field.HEIGHT and
                    0 <= col < Field.WIDTH and
                    self.field[row][col] == self.field[self.last_move.row][self.last_move.col]
                ):
                    count += 1
                    row += DIRECTIONS[direction][0]
                    col += DIRECTIONS[direction][1]

                direction = (direction + 4) % 8

            if count >= Field.STREAK_TO_WIN:
                return True
            
        return False


    def create_child(self, cell : Field.Cell):
        row, column = cell.row, cell.col
        child: Node = Node()
        child.last_move = cell
        child.field = copy.deepcopy(
            self.field
        )  
        child.field[row][column] = self.who_moves
        child.free_cells_count = self.free_cells_count - 1
        child.parent = self
        child.who_moves = Player.Type(
            abs(self.who_moves.value - 1)
        )


        return child


    def get_children(self):
        empty_cells = []
        if not self.is_terminal():
            
            for row in range(Field.HEIGHT):
                for column in range(Field.WIDTH):
                    
                    if self.field[row][column] == Player.Type.NONE:
                        
                        empty_cells.append(self.create_child(Field.Cell(row, column)))

        

        return empty_cells

    def get_random_child(self):
        empty_cells = []
        if not self.is_terminal():
            
            for row in range(Field.HEIGHT):
                for column in range(Field.WIDTH):
                    
                    if self.field[row][column] == Player.Type.NONE:
                        empty_cells.append(Field.Cell(row, column))

        return self.create_child(random.choice(empty_cells))
    

    def check_game_state(self) -> GameStates:
        """
        Проверяет состояние игры
        """

        if self.check_win():
            return (
                GameStates.CROSS_WON
                if self.who_moves == Player.Type.NAUGHT
                else GameStates.NAUGHT_WON
            )

        if self.free_cells_count == 0:
            return GameStates.TIE

        return GameStates.CONTINUE

    def is_terminal(self):
        return self.check_game_state() != GameStates.CONTINUE



    def get_reward(self):
        if self.is_terminal():
            if self.check_game_state() == GameStates.CROSS_WON:
                return 1.0
            elif self.check_game_state() == GameStates.NAUGHT_WON:
                return 0.0
            else:
                return 0.5
        return None


    def __hash__(self):
        """
        вычисление хеш-функции состояния игры
        """
        return hash(tuple(tuple(row) for row in self.field))

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return self.field == other.field
