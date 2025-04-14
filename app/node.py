from app.game_config import Field, Cell, PlayerType
from typing import ForwardRef

class Node:
    parent : ForwardRef('Node') = None
    who_moves: PlayerType = PlayerType.CROSS
    field: list[list[PlayerType]] = [[PlayerType.NONE for _ in range(Field.WIDTH)] for _ in range(Field.HEIGHT)]
    free_cells_count: int = (Field.WIDTH * Field.HEIGHT)  # для быстрой проверки ничьей, TODO: сделать её умнее
    last_move: Cell = Cell()


    def __hash__(self):
        """
        вычисление хеш-функции состояния игры
        """
        return hash(tuple(tuple(row) for row in self.field))

        