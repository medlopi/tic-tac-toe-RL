from app.game_config import Field, PlayerType, Cell
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


analyzed_positions: dict[str, tuple[PositionStatus, Cell]] = {}


def check_win(position: str, last_move: Cell) -> bool:
        """
        Проверяет, закончилась ли игра победой
        """
        if last_move.row == -1 and last_move.col == -1:
            return False
        
        last_move_index = last_move.row * Field.WIDTH + last_move.col
        for direction in range(4):
            count = 1
            for _ in range(2):
                row = last_move.row + DIRECTIONS[direction][0]
                col = last_move.col + DIRECTIONS[direction][1]
                index = row * Field.WIDTH + col
                while (
                    0 <= row < Field.HEIGHT and
                    0 <= col < Field.WIDTH and
                    position[index] == position[last_move_index]
                ):
                    count += 1
                    row += DIRECTIONS[direction][0]
                    col += DIRECTIONS[direction][1]
                    index = row * Field.WIDTH + col
                direction = (direction + 4) % 8
            if count >= Field.STREAK_TO_WIN:
                return True
            
        return False


def get_position_status_and_best_move(position: str, current_player: PlayerType, last_move: Cell) -> tuple[PositionStatus, Cell]:
        """
        Возращает оценку позиции и оптимальный ход
        """
        if position in analyzed_positions:
            return analyzed_positions[position]
        
        if check_win(position, last_move):
            analyzed_positions[position] = (PositionStatus.LOSING_POSITION, Cell())
            return analyzed_positions[position]
        
        if not position.count('0'):
            analyzed_positions[position] = (PositionStatus.DRAW_POSITION, Cell())
            return analyzed_positions[position]
        
        analyzed_positions[position] = (PositionStatus.LOSING_POSITION, Cell())

        for row in range(Field.HEIGHT):
            for col in range(Field.WIDTH):
                index = row * Field.WIDTH + col

                if position[index] != '0':
                    continue

                next_position: str = position[:index] + str(current_player.value + 1) + position[index + 1:]
                next_position_status: PositionStatus = get_position_status_and_best_move(
                    next_position, 
                    PlayerType(abs(current_player.value - 1)), 
                    Cell(row, col)
                )[0]

                if next_position_status == PositionStatus.LOSING_POSITION:
                    analyzed_positions[position] = (PositionStatus.WINNING_POSITION, Cell(row, col))
                    return analyzed_positions[position]
                elif next_position_status == PositionStatus.DRAW_POSITION:
                    analyzed_positions[position] = (PositionStatus.DRAW_POSITION, Cell(row, col))
                else:
                    if analyzed_positions[position][0] == PositionStatus.LOSING_POSITION:
                        analyzed_positions[position] = (PositionStatus.LOSING_POSITION, Cell(row, col))

        return analyzed_positions[position]
