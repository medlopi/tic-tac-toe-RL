from enum import Enum


class Field:
    HEIGHT = 3
    WIDTH = 3
    STREAK_TO_WIN = 3


class GameStates(Enum):
    ERROR = -1
    CROSS_WON = 0
    NAUGHT_WON = 1
    CONTINUE = 2
    TIE = 3


class PlayerType(Enum):
    NONE = -1
    CROSS = 0
    NAUGHT = 1


# TODO: Может тоже в класс вложить?
PlayerIcon: dict = {
    PlayerType.NONE: " ",
    PlayerType.CROSS: "X",
    PlayerType.NAUGHT: "O"
}
