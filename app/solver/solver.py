from app.basic_game_core.field import Field
from app.basic_game_core.player import Player
from app.basic_game_core.node import Node
from enum import Enum
import sys


sys.setrecursionlimit(10**5)


class PositionStatus(Enum):
    LOSING_POSITION = 0
    WINNING_POSITION = 1
    DRAW_POSITION = 2


analyzed_positions: dict[int, tuple[PositionStatus, Field.Cell]] = {}


# @measure_performance
def get_position_status_and_best_move(current_state: Node) -> tuple[PositionStatus, Field.Cell]:
    """
    Возращает оценку позиции и оптимальный ход
    """

    current_position_hash: int = hash(current_state)
    if current_position_hash in analyzed_positions:
        return analyzed_positions[current_position_hash]
    
    if current_state.check_win():
        analyzed_positions[current_position_hash] = (PositionStatus.LOSING_POSITION, Field.Cell())
        return analyzed_positions[current_position_hash]
    
    if not current_state.free_cells_count:
        analyzed_positions[current_position_hash] = (PositionStatus.DRAW_POSITION, Field.Cell())
        return analyzed_positions[current_position_hash]
    
    analyzed_positions[current_position_hash] = (PositionStatus.LOSING_POSITION, Field.Cell())
    changed: bool = False
    current_player: Player.Type = current_state.who_moves
    current_last_move: Field.Cell = current_state.last_move
    count_different_figures: int = 1 << (Field.COUNT_FEATURES - 1)
    shift: int = count_different_figures * current_player.value

    current_state.who_moves = Player.Type(abs(current_state.who_moves.value - 1))
    current_state.free_cells_count -= 1
    
    for row in range(Field.HEIGHT):
        for col in range(Field.WIDTH):
            if current_state.field[row][col] != -1:
                continue
            
            for i in range(count_different_figures): 
                figure = i + shift
                if figure not in current_state.available_figures:
                    continue
                
                current_state.field[row][col] = figure
                if Field.COUNT_FEATURES > 1:
                    current_state.available_figures.remove(figure)
                current_state.last_move = Field.Cell(row, col, figure)

                next_position_status: PositionStatus = get_position_status_and_best_move(current_state)[0]

                current_state.field[row][col] = -1
                current_state.available_figures.add(figure)

                if next_position_status == PositionStatus.LOSING_POSITION:
                    analyzed_positions[current_position_hash] = (PositionStatus.WINNING_POSITION, current_state.last_move)

                    current_state.who_moves = current_player
                    current_state.free_cells_count += 1
                    current_state.last_move = current_last_move

                    return analyzed_positions[current_position_hash]
                elif next_position_status == PositionStatus.DRAW_POSITION:
                    if analyzed_positions[current_position_hash][0] == PositionStatus.LOSING_POSITION:
                        analyzed_positions[current_position_hash] = (PositionStatus.DRAW_POSITION, current_state.last_move)
                        changed = True
                else:
                    if analyzed_positions[current_position_hash][0] == PositionStatus.LOSING_POSITION and not changed:
                        analyzed_positions[current_position_hash] = (PositionStatus.LOSING_POSITION, current_state.last_move)
                        changed = True

    current_state.who_moves = current_player
    current_state.free_cells_count += 1
    current_state.last_move = current_last_move

    return analyzed_positions[current_position_hash]
