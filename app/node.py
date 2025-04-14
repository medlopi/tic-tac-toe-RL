from app.field import Field
from app.player import Player

from typing import ForwardRef


class Node:
    parent: ForwardRef("Node") = None
    who_moves: Player.Type = Player.Type.CROSS
    field: list[list[Player.Type]] = [
        [Player.Type.NONE for _ in range(Field.WIDTH)] for _ in range(Field.HEIGHT)
    ]  # TODO а зачем?..
    free_cells_count: int = Field.WIDTH * Field.HEIGHT
    last_move: Field.Cell = Field.Cell()

    def __hash__(self):
        """
        вычисление хеш-функции состояния игры
        """
        return hash(tuple(tuple(row) for row in self.field))
