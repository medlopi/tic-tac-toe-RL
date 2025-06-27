from enum import Enum


class Player:
    class Type(Enum):
        NONE = -1
        CROSS = 0
        NAUGHT = 1

    Icon: dict = {Type.NONE: " ", Type.CROSS: "X", Type.NAUGHT: "O"}
