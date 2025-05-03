from app.game_config import (
    CONST_FIELD_HEIGHT,
    CONST_FIELD_WIDTH,
    CONST_STREAK_TO_WIN_SIZE,
)


class Field:
    HEIGHT = CONST_FIELD_HEIGHT
    WIDTH = CONST_FIELD_WIDTH
    STREAK_TO_WIN = CONST_STREAK_TO_WIN_SIZE

    @classmethod
    def set_dimensions(cls, width, height, streak):
        cls.WIDTH = width
        cls.HEIGHT = height
        cls.STREAK_TO_WIN = streak

    class Cell:
        def __init__(self, row=-1, col=1):
            self.row = row
            self.col = col
