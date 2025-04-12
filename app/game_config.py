from enum import Enum


PROGRAM_VERSION = 0.2
PROGRAM_VERSION_DESCRIPTION = "console version. m, n, k -- arbitrary"
# TODO NEXT VERSION: перевести вывод в консоль на какой-то ОДИН язык) ПРОСМОТРЕТЬ ВСЕ #TODO!!!!!


class Field:
    HEIGHT = 7
    WIDTH = 7
    STREAK_TO_WIN = 4


class GameStates(Enum):
    CROSS_WON = 0
    NAUGHT_WON = 1
    CONTINUE = 2
    TIE = 3


class PlayerType(Enum):
    NONE = -1
    CROSS = 0
    NAUGHT = 1


# TODO в будущем как в лабе по плюсам имеет смысл это в отдельный класс выделить
PlayerIcon: dict = {
    PlayerType.NONE: " ",
    PlayerType.CROSS: "X",
    PlayerType.NAUGHT: "O"
}
