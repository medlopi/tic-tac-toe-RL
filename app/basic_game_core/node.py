from app.basic_game_core.field import Field, GameStates
from app.basic_game_core.player import Player
from typing import ForwardRef, Union
import copy
import numpy as np

DIRECTIONS = tuple(
    [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]
)


class Node:
    def __init__(self, parent=None, move=None, prior_probability=1.0):
        self._parent: ForwardRef("Node") = parent
        self._children: dict[Field.Cell, Node] = {}
        self._visits_number: int = 0
        self._estimate_value: float = 0
        self._exploration_bonus: float = 0
        self._prior_probability: float = prior_probability

        if parent is None:
            self.who_moves: Player.Type = Player.Type.CROSS
            self.field: list[list[int]] = [
                [-1 for _ in range(Field.WIDTH)] for _ in range(Field.HEIGHT)
            ]
            self.free_cells_count: int = Field.WIDTH * Field.HEIGHT
            self.last_move: Field.Cell = Field.Cell()
            self.available_figures = set(range(1 << Field.COUNT_FEATURES))
        else:
            self.field = copy.deepcopy(parent.field)
            self.field[move.row][move.col] = move.figure
            self.who_moves = Player.Type(abs(parent.who_moves.value - 1))
            self.free_cells_count = parent.free_cells_count - 1
            self.last_move = move
            self.available_figures = parent.available_figures.copy()
            if Field.COUNT_FEATURES > 1:
                self.available_figures.remove(move.figure)

    def get_depth(self) -> int:
        """
        Возвращает глубину узла в дереве (расстояние от корня)
        """
        depth = 0
        current = self
        while current._parent is not None:
            depth += 1

            current = current._parent

        return depth

    def get_node_value(self, puct_constant: float) -> float:
        self._exploration_bonus = (
            puct_constant
            * self._prior_probability
            * np.sqrt(self._parent._visits_number)
            / (1 + self._visits_number)
        )
        return self._estimate_value + self._exploration_bonus

    def select_action(self, puct_constant) -> tuple[Field.Cell, ForwardRef("Node")]:
        return max(
            self._children.items(),
            key=lambda child: child[1].get_node_value(puct_constant),
        )

    def update_node(self, leaf_value: float) -> None:
        self._visits_number += 1
        self._estimate_value += (
            leaf_value - self._estimate_value
        ) / self._visits_number

    def update_all_ancestors_recursively(self, leaf_value: float) -> None:
        if self._parent:
            self._parent.update_all_ancestors_recursively(-leaf_value)
        self.update_node(leaf_value)

    def expand_node(
        self, actions_with_prior_probabilities: list[tuple[Field.Cell, float]]
    ) -> None:
        for action, probability in actions_with_prior_probabilities:
            if action not in self._children:
                self._children[action] = Node(self, action, probability)

    def is_leaf(self) -> bool:
        return self._children == {}

    def is_root(self) -> bool:
        return self._parent is None

    def get_available_moves(self) -> list[Field.Cell]:
        count_different_figures = 1 << (Field.COUNT_FEATURES - 1)
        shift = count_different_figures * self.who_moves.value
        result = []
        for figure in range(count_different_figures):
            if (figure + shift) not in self.available_figures:
                continue
            for i in range(Field.HEIGHT):
                for j in range(Field.WIDTH):
                    if self.field[i][j] == -1:
                        result.append(Field.Cell(i, j, figure + shift))
        return result

    def check_win(self) -> bool:
        """
        Проверяет, закончилась ли игра победой
        """

        if self.last_move.row == -1:
            return False

        last_move_cell = f"{self.field[self.last_move.row][self.last_move.col]:0{Field.COUNT_FEATURES}b}"

        for i in range(Field.COUNT_FEATURES):

            for direction in range(4):
                count = 1

                for _ in range(2):
                    row = self.last_move.row + DIRECTIONS[direction][0]
                    col = self.last_move.col + DIRECTIONS[direction][1]

                    while (
                        0 <= row < Field.HEIGHT
                        and 0 <= col < Field.WIDTH
                        and self.field[row][col] != -1
                        and f"{self.field[row][col]:0{Field.COUNT_FEATURES}b}"[i]
                        == last_move_cell[i]
                    ):
                        count += 1
                        row += DIRECTIONS[direction][0]
                        col += DIRECTIONS[direction][1]

                    direction = (direction + 4) % 8

                if count >= Field.STREAK_TO_WIN:
                    return True

        return False

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

    def current_state(self):
        """
        Возвращает текущее состояние доски в виде np.array формы (2*FEATURES+2, HEIGHT, WIDTH):
        каналы 0-1: клетки текущего игрока и клетки соперника
        каналы 2-2D-1: по 2 канала на каждое из D-1 свойств
        канал 2D: последняя сыгранная клетка
        канал 2D+1: чей ход
        """
        h, w, d = Field.HEIGHT, Field.WIDTH, Field.COUNT_FEATURES
        state = np.zeros((2 * d + 2, h, w), dtype=np.float32)

        current = self.who_moves.value

        # Каналы 0, ..., 2D - 1
        for i in range(h):
            for j in range(w):
                figure = self.field[i][j]
                if figure == -1:
                    continue

                binary = f"{figure:0{d}b}"
                shift = int(int(binary[0]) != current)
                state[shift, i, j] = 1.0

                for k in range(1, d):
                    if int(binary[k]):
                        state[2 * k + shift, i, j] = 1.0

        # Последний ход
        if self.last_move != Field.Cell():
            state[2 * d, self.last_move.row, self.last_move.col] = 1.0

        # Чей ход
        if self.who_moves == Player.Type.CROSS:
            state[2 * d + 1, :, :] = 1.0

        if d == 1:
            return state[:, ::-1, :]
        else:
            return state

    def define_winner(self, game_state: GameStates) -> Union[Player.Type, None]:
        if game_state != GameStates.CONTINUE:
            if game_state == GameStates.CROSS_WON:
                winner = Player.Type.CROSS
            elif game_state == GameStates.NAUGHT_WON:
                winner = Player.Type.NAUGHT
            else:
                winner = Player.Type.NONE
            return winner
        else:
            print("This is not the end of game")

    def is_terminal(self):
        return self.check_game_state() != GameStates.CONTINUE

    def __hash__(self):
        """
        вычисление хеш-функции состояния игры
        """
        return hash(tuple(tuple(row) for row in self.field))

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return self.field == other.field
