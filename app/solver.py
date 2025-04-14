from app.field import Field
from app.player import Player
from app.node import Node
from enum import Enum
import sys


sys.setrecursionlimit(10**5)


class PositionStatus(Enum):
    LOSING_POSITION = 0
    WINNING_POSITION = 1
    DRAW_POSITION = 2


DIRECTIONS = [
    (-1, 0), (-1, 1), (0, 1), (1, 1),
    (1, 0), (1, -1), (0, -1), (-1, -1)
]


analyzed_positions: dict[int, tuple[PositionStatus, Field.Cell]] = {}


def check_win(current_state: Node) -> bool:
    """
    Проверяет, закончилась ли игра победой
    """

    if current_state.last_move.row == -1:
        return False
    
    for direction in range(4):
        count = 1

        for _ in range(2):
            row = current_state.last_move.row + DIRECTIONS[direction][0]
            col = current_state.last_move.col + DIRECTIONS[direction][1]

            while (
                0 <= row < Field.HEIGHT and
                0 <= col < Field.WIDTH and
                current_state.field[row][col] == current_state.field[current_state.last_move.row][current_state.last_move.col]
            ):
                count += 1
                row += DIRECTIONS[direction][0]
                col += DIRECTIONS[direction][1]

            direction = (direction + 4) % 8

        if count >= Field.STREAK_TO_WIN:
            return True
        
    return False


def get_position_status_and_best_move(current_state: Node) -> tuple[PositionStatus, Field.Cell]:
    """
    Возращает оценку позиции и оптимальный ход
    """

    current_position_hash: int = hash(current_state)
    if current_position_hash in analyzed_positions:
        return analyzed_positions[current_position_hash]
    
    if check_win(current_state):
        analyzed_positions[current_position_hash] = (PositionStatus.LOSING_POSITION, Field.Cell())
        return analyzed_positions[current_position_hash]
    
    if not current_state.free_cells_count:
        analyzed_positions[current_position_hash] = (PositionStatus.DRAW_POSITION, Field.Cell())
        return analyzed_positions[current_position_hash]
    
    analyzed_positions[current_position_hash] = (PositionStatus.LOSING_POSITION, Field.Cell())
    changed: bool = False
    current_player: Player.Type = current_state.who_moves
    current_last_move: Field.Cell = current_state.last_move

    current_state.who_moves = Player.Type(abs(current_state.who_moves.value - 1))
    current_state.free_cells_count -= 1
    
    for row in range(Field.HEIGHT):
        for col in range(Field.WIDTH):
            if current_state.field[row][col] != Player.Type.NONE:
                continue

            current_state.field[row][col] = current_player
            current_state.last_move = Field.Cell(row, col)

            next_position_status: PositionStatus = get_position_status_and_best_move(current_state)[0]

            current_state.field[row][col] = Player.Type.NONE

            if next_position_status == PositionStatus.LOSING_POSITION:
                analyzed_positions[current_position_hash] = (PositionStatus.WINNING_POSITION, Field.Cell(row, col))

                current_state.who_moves = current_player
                current_state.free_cells_count += 1
                current_state.last_move = current_last_move

                return analyzed_positions[current_position_hash]
            elif next_position_status == PositionStatus.DRAW_POSITION:
                if analyzed_positions[current_position_hash][0] == PositionStatus.LOSING_POSITION:
                    analyzed_positions[current_position_hash] = (PositionStatus.DRAW_POSITION, Field.Cell(row, col))
                    changed = True
            else:
                if analyzed_positions[current_position_hash][0] == PositionStatus.LOSING_POSITION and not changed:
                    analyzed_positions[current_position_hash] = (PositionStatus.LOSING_POSITION, Field.Cell(row, col))
                    changed = True

    current_state.who_moves = current_player
    current_state.free_cells_count += 1
    current_state.last_move = current_last_move

    return analyzed_positions[current_position_hash]
