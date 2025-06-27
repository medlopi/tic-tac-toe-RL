import time
import psutil
import os
import threading
import numpy as np
from app.basic_game_core.node import Node


class WrongMethodError(Exception):
    """Исключение, возникающее при попытке использовать декоратор measure_mcts_performance не на методе MCTS"""

    pass


def measure_mcts_performance(func):
    """
    Декоратор для измерения времени выполнения, потребления памяти и статистики MCTS (!!!!!)

    :param func: Функция, которую нужно измерить.
    :raises WrongMethodError: Если декоратор используется не на методе MCTS
    """

    # тут я патчу Node.select_action. Критика приветствуется.
    def wrapper(*args, **kwargs):
        if not hasattr(args[0], "_run_playout"):
            raise WrongMethodError(
                "Декоратор measure_mcts_performance может использоваться только на методах класса MCTS"
            )

        process = psutil.Process(os.getpid())

        # статистика для MCTS из конкретного узла
        mcts_stats = {
            "total_nodes": 0,
            "depths": [],
            "ucb_values": [],
            "winning_simulations": 0,
            "total_simulations": 0,
            "simulation_times": [],
            "node_values": {},  # словарь для хранения значений узлов
            "branching_factors": [],  # фактор ветвления на каждом уровне
        }

        original_run_playout = None
        original_run_rollout = None

        original_run_playout = args[0]._run_playout

        def new_run_playout():
            start_time = time.time()

            result = original_run_playout()

            mcts_stats["simulation_times"].append(time.time() - start_time)
            mcts_stats["total_simulations"] += 1

            return result

        args[0]._run_playout = new_run_playout

        original_node_select_action = Node.select_action

        def new_node_select_action(self, puct_constant):
            action, node = original_node_select_action(self, puct_constant)
            if node is not None:
                depth = node.get_depth()
                mcts_stats["depths"].append(depth)
                mcts_stats["total_nodes"] += 1

                # соберем статистику по узлам
                node_id = id(node)
                if node_id not in mcts_stats["node_values"]:
                    mcts_stats["node_values"][node_id] = {"visits": 0, "value": 0}

                mcts_stats["node_values"][node_id]["visits"] = node._visits_number
                mcts_stats["node_values"][node_id]["value"] = node._estimate_value

                if hasattr(node, "_children"):
                    mcts_stats["branching_factors"].append(len(node._children))

                if hasattr(node, "get_node_value"):
                    mcts_stats["ucb_values"].append(node.get_node_value(puct_constant))

            return action, node

        Node.select_action = new_node_select_action

        if hasattr(args[0], "_run_rollout"):
            original_run_rollout = args[0]._run_rollout

            def new_run_rollout(node):
                if node is not None:
                    result = original_run_rollout(node)
                    if result > 0:  # победа
                        mcts_stats["winning_simulations"] += 1

                    return result

                return original_run_rollout(node)

            args[0]._run_rollout = new_run_rollout

        start_memory = process.memory_info().rss
        peak_memory = start_memory

        stop_monitoring = threading.Event()

        def monitor_memory():
            nonlocal peak_memory

            while not stop_monitoring.is_set():
                current_memory = process.memory_info().rss
                peak_memory = max(peak_memory, current_memory)

                time.sleep(0.1)

        memory_monitor_thread = threading.Thread(target=monitor_memory, daemon=True)
        memory_monitor_thread.start()

        start_time = time.time()

        try:
            result = func(*args, **kwargs)
        finally:
            stop_monitoring.set()
            memory_monitor_thread.join()

            # возвращаем методы, как было
            if original_run_playout:
                args[0]._run_playout = original_run_playout
            if original_node_select_action:
                Node.select_action = original_node_select_action
            if original_run_rollout:
                args[0]._run_rollout = original_run_rollout

        end_time = time.time()

        elapsed_time = end_time - start_time  # в секундах
        peak_memory_used = (peak_memory - start_memory) / (1024**2)  # в мб

        print()
        print(f"[{func.__name__}] Time: {elapsed_time:.2f} seconds")
        print(f"[{func.__name__}] Peak memory used: {peak_memory_used:.3f} MB")

        if mcts_stats["total_nodes"] > 0:
            avg_depth = np.mean(mcts_stats["depths"]) if mcts_stats["depths"] else 0
            max_depth = max(mcts_stats["depths"]) if mcts_stats["depths"] else 0
            avg_ucb = (
                np.mean(mcts_stats["ucb_values"]) if mcts_stats["ucb_values"] else 0
            )
            avg_sim_time = (
                np.mean(mcts_stats["simulation_times"])
                if mcts_stats["simulation_times"]
                else 0
            )
            win_rate = (
                (
                    mcts_stats["winning_simulations"]
                    / mcts_stats["total_simulations"]
                    * 100
                )
                if mcts_stats["total_simulations"] > 0
                else 0
            )
            avg_branching = (
                np.mean(mcts_stats["branching_factors"])
                if mcts_stats["branching_factors"]
                else 0
            )

            print(f"[{func.__name__}] MCTS Statistics:")
            print(f"  Total nodes visited: {mcts_stats['total_nodes']}")
            print(f"  Average search depth: {avg_depth:.2f}")
            print(f"  Maximum search depth: {max_depth}")
            print(f"  Average UCB value: {avg_ucb:.4f}")
            print(f"  Average simulation time: {avg_sim_time*1000:.2f} ms")
            print(f"  Overall win rate: {win_rate:.1f}%")
            print(f"  Average branching factor: {avg_branching:.1f}")

        print()

        return result

    return wrapper
