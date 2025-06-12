from app.game_config import (
    CONST_FIELD_HEIGHT,
    CONST_FIELD_WIDTH,
    CONST_STREAK_TO_WIN_SIZE,
    CONST_COUNT_FEATURES
)

from enum import Enum

class Field:
    HEIGHT = CONST_FIELD_HEIGHT
    WIDTH = CONST_FIELD_WIDTH
    STREAK_TO_WIN = CONST_STREAK_TO_WIN_SIZE
    COUNT_FEATURES = CONST_COUNT_FEATURES

    @classmethod
    def set_dimensions(cls, width, height, streak, features):
        cls.WIDTH = width
        cls.HEIGHT = height
        cls.STREAK_TO_WIN = streak
        cls.COUNT_FEATURES = features
        
    class Cell:
        def __init__(self, row=-1, col=-1, figure=-1):
            self.row = row
            self.col = col
            self.figure = figure

        def __eq__(self, other):
            return (self.row, self.col, self.figure) == (other.row, other.col, other.figure)
        
        def __hash__(self):
            return hash((self.row, self.col, self.figure))


class GameStates(Enum):
        CROSS_WON = 0
        NAUGHT_WON = 1
        CONTINUE = 2
        TIE = 3
        