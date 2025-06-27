# TODO d свойств -- ?


from app.basic_game_core.field import Field
from app.basic_game_core.node import Node
from app.basic_game_core.player import Player
from app.basic_game_core.config.game_config import MAX_FIELD_SIZE_FOR_SOLVER
from tqdm import tqdm
from typing import Set
import random
import math


def parse_fraction(s: str) -> float:
    try:
        return float(s)
    except ValueError:
        if "/" in s:
            num, denom = s.split("/")

            return float(num) / float(denom)

        raise ValueError("error, try to input another float")


def count_states_dfs() -> int:
    """
    Считает число уникальных состояний в дереве игры с помощью dfs
    """

    visited: Set[int] = set()  # хеши уже посещенных состояний

    pbar = tqdm(desc="DFS progress", unit="states")  # прогресс бар

    def dfs(current_state: Node) -> int:
        """
        Рекурсивная функция для обхода дерева игры.
        Возвращает количество уникальных состояний в поддереве.
        """

        state_hash = hash(current_state)

        if state_hash in visited:
            return 0

        visited.add(state_hash)
        pbar.update(1)

        if (
            current_state.check_win() or not current_state.free_cells_count
        ):  # если игра закончилась, возвращаем текущее состояние
            return 1

        total_states = 1  # текущее состояние

        # сохраняем то, что было тут
        current_player = current_state.who_moves
        current_last_move = current_state.last_move
        current_free_cells = current_state.free_cells_count

        # меняем игрока
        current_state.who_moves = Player.Type(abs(current_state.who_moves.value - 1))
        current_state.free_cells_count -= 1

        for row in range(Field.HEIGHT):
            for col in range(Field.WIDTH):
                if current_state.field[row][col] != Player.Type.NONE:
                    continue

                # новый ход
                current_state.field[row][col] = current_player
                current_state.last_move = Field.Cell(row, col)

                # рекурсивно идем дальше
                total_states += dfs(current_state)

                # откат
                current_state.field[row][col] = Player.Type.NONE

        # еще откат
        current_state.who_moves = current_player
        current_state.last_move = current_last_move
        current_state.free_cells_count = current_free_cells

        return total_states

    try:
        initial_state = Node()

        return dfs(initial_state)

    finally:
        pbar.close()


def check_winning_line_through_move(
    field: Field, last_move: Field.Cell, streak_to_win: int
) -> bool:
    """
    Проверка: завершилась ли победой игра после крайнего хода
    """
    row, col = last_move.row, last_move.col
    player = field[row][col]

    height, width = len(field), len(field[0])

    """
    горизонт
    """
    count = 1
    # влево
    for c in range(col - 1, -1, -1):
        if field[row][c] == player:
            count += 1
        else:
            break
    # вправо
    for c in range(col + 1, width):
        if field[row][c] == player:
            count += 1
        else:
            break
    if count >= streak_to_win:
        return True

    """
    вертикаль
    """
    count = 1
    # вверх
    for r in range(row - 1, -1, -1):
        if field[r][col] == player:
            count += 1
        else:
            break
    # вниз
    for r in range(row + 1, height):
        if field[r][col] == player:
            count += 1
        else:
            break
    if count >= streak_to_win:
        return True

    """
    диагональ \\
    """
    count = 1
    # влево вверх
    r, c = row - 1, col - 1
    while r >= 0 and c >= 0:
        if field[r][c] == player:
            count += 1
            r -= 1
            c -= 1
        else:
            break
    # вправо вниз
    r, c = row + 1, col + 1
    while r < height and c < width:
        if field[r][c] == player:
            count += 1
            r += 1
            c += 1
        else:
            break
    if count >= streak_to_win:
        return True

    """
    диагональ /
    """
    count = 1
    # вправо вверх
    r, c = row - 1, col + 1
    while r >= 0 and c < width:
        if field[r][c] == player:
            count += 1
            r -= 1
            c += 1
        else:
            break
    # влево вниз
    r, c = row + 1, col - 1
    while r < height and c >= 0:
        if field[r][c] == player:
            count += 1
            r += 1
            c -= 1
        else:
            break
    if count >= streak_to_win:
        return True

    """
    жизнь боль, везде облом
    """
    return False


def main():
    width = int(input("m >  "))
    height = int(input("n >  "))
    streak = int(input("k >  "))
    SIMULATIONS_POWER_FACTOR = parse_fraction(
        input("simulations power factor (0 < float <= 1) >  ")
    )  # степень для расчета количества симуляций

    Field.set_dimensions(width, height, streak)

    total_cells = width * height

    rough_estimate = int(math.pow(3, width * height))
    print(f"\nrough estimate [3^(m * n)] is {rough_estimate:,}\n")

    result = 0

    for move in range(1, total_cells + 1):  # число сделанных ходов
        simulations_count = max(
            1, int(math.comb(total_cells, move) ** SIMULATIONS_POWER_FACTOR)
        )  # количество рандомно просмотренных полей с move ходами. #TODO поиграться

        visited_nodes_hashes = set()
        is_good = 0

        # случайно делаем simulations_count раз move ходов
        for _ in range(simulations_count):
            cur_node = Node()
            cur_player = Player.Type.CROSS
            game_ended = False
            is_terminal_on_last_move = False

            for move_num in range(move):
                next_move = random.choice(cur_node.get_available_moves())
                cur_node.field[next_move.row][next_move.col] = cur_player

                # проверяем окончание игры только на последнем ходу, чтобы считать is_good и терминальные состояния на нем
                if move_num == move - 1:
                    # если победа на последнем ходу или ничья (все клетки заполнены) - считаем состояние хорошим
                    if (
                        check_winning_line_through_move(
                            cur_node.field, next_move, streak
                        )
                        or move == total_cells
                    ):
                        is_terminal_on_last_move = True
                else:  # если не последний ход
                    # если игра закончилась раньше - считаем состояние плохим
                    if check_winning_line_through_move(
                        cur_node.field, next_move, streak
                    ):
                        game_ended = True

                        break

                cur_player = (
                    Player.Type.NAUGHT
                    if cur_player == Player.Type.CROSS
                    else Player.Type.CROSS
                )

            # состояние хорошее если игра не закончилась раньше времени ИЛИ закончилась на последнем ходу
            if hash(cur_node) not in visited_nodes_hashes and (
                not game_ended or is_terminal_on_last_move
            ):
                is_good += 1

            visited_nodes_hashes.add(hash(cur_node))

        possible_states = math.comb(total_cells, move) * (2 ** (move - 1))

        reachable_probability = is_good / len(visited_nodes_hashes)
        total_nodes = int(possible_states * reachable_probability)

        print(
            f"move {move}: {total_nodes:,} states (is_good: {reachable_probability:.2%})"
        )
        result += total_nodes

    print(f"\nRandomized algorithm says that game tree have ~{result:,} states\n")

    if max(width, height) <= MAX_FIELD_SIZE_FOR_SOLVER:
        print("dfs is calculating exact number of states...")
        exact_states = count_states_dfs()
        print(f"exact number of states: {exact_states:,}")

        if exact_states > 0:
            ratio = abs(result / exact_states) * 100
            print(f"\nratio: {ratio:.1f}%")
    else:
        print(
            "field is too large for exact calculation! check app/game_config.py please"
        )


if __name__ == "__main__":
    main()
