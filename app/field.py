from app.game_config import (
    CONST_FIELD_HEIGHT,
    CONST_FIELD_WIDTH,
    CONST_STREAK_TO_WIN_SIZE,
)

from enum import Enum

class Field:
    HEIGHT = CONST_FIELD_HEIGHT
    WIDTH = CONST_FIELD_WIDTH
    STREAK_TO_WIN = CONST_STREAK_TO_WIN_SIZE

    class Cell:
        def __init__(self, row=-1, col=-1):
            self.row = row
            self.col = col

        def __eq__(self, other):
            return (self.row, self.col) == (other.row, other.col)
        
        def __hash__(self):
            return hash((self.row, self.col))


class GameStates(Enum):
        CROSS_WON = 0
        NAUGHT_WON = 1
        CONTINUE = 2
        TIE = 3
        