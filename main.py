import sys

if sys.version_info < (3, 10):
    print("Для работы программы требуется Python 3.10 или выше")
    sys.exit(1)


import pygame
from app.basic_game_core.game import Game
from app.pygame_interface.start_menu import StartMenu
from app.pygame_interface.interface import PyGameInterface
from app.pygame_interface.interface_features import PyGameInterfaceFeatures
from app.basic_game_core.config.game_config import MCTS_ITERATIONS, MCTS_AZ_ITERATIONS
from app.basic_game_core.field import Field
from app.basic_game_core.player import Player
from app.mcts.mcts_alphazero import MCTSPlayer as MCTS_AZ_Player
from app.models_training.policy_value_net_torch import PolicyValueNet
from app.mcts.mcts import MCTSPlayer as Pure_MCTS_Player


def main():
    current_fullscreen_state = False
    current_screen_size = (1200, 800)

    pygame.init()
    try:
        while True:
            menu = StartMenu(
                is_fullscreen_start=current_fullscreen_state,
                initial_size=current_screen_size,
            )
            (
                m,
                n,
                k,
                d,
                ai_enabled,
                mcts_enabled_flag,
                mcts_vs_dqn_enabled,
                mcts_vs_dqn_choice,
                player_type,
                is_fullscreen,
                screen_size,
            ) = menu.run()

            if m <= 0 or n <= 0 or k <= 0:
                print("Выход из игры.")
                break

            Field.set_dimensions(m, n, k, d)

            az_model_player = None
            pure_mcts_player_instance = None

            is_computer_game_active = (
                ai_enabled or mcts_enabled_flag or mcts_vs_dqn_enabled
            )

            if ai_enabled or mcts_vs_dqn_enabled:
                model_file_name = f"policy_{m}x{n}x{k}x{d}.model"
                path_to_model_file = f"app/models_training/models_files/{model_file_name}"
                print(f"Попытка загрузить модель AlphaZero: {model_file_name}")
                try:
                    policy_value_net = PolicyValueNet(m, n, d, model_file=path_to_model_file)
                    az_model_player = MCTS_AZ_Player(
                        policy_value_net.policy_value_function,
                        puct_constant=5,
                        playout_number=MCTS_AZ_ITERATIONS,
                        is_selfplay=False,
                    )
                    print("AlphaZero модель загружена.")
                except FileNotFoundError:
                    print(f"ОШИБКА: Файл модели AlphaZero '{model_file_name}' по адресу '{path_to_model_file}' не найден!")
                    if ai_enabled and not mcts_enabled_flag and not mcts_vs_dqn_enabled:
                        print(
                            "AlphaZero была единственным ИИ. Переключение на чистый MCTS как основной ИИ."
                        )
                        az_model_player = Pure_MCTS_Player(
                            puct_constant=5, playout_number=MCTS_ITERATIONS
                        )
                    elif mcts_vs_dqn_enabled:
                        print(
                            "AlphaZero не найдена для режима AI vs AI. AZ будет заменен на Pure MCTS."
                        )
                        az_model_player = Pure_MCTS_Player(
                            puct_constant=5, playout_number=MCTS_ITERATIONS
                        )

            if mcts_enabled_flag or mcts_vs_dqn_enabled:
                print("Инициализация Pure MCTS игрока.")
                pure_mcts_player_instance = Pure_MCTS_Player(
                    puct_constant=5,
                    playout_number=MCTS_ITERATIONS,
                )

            game_constructor_ai = None
            if az_model_player:
                game_constructor_ai = az_model_player
            elif pure_mcts_player_instance:
                game_constructor_ai = pure_mcts_player_instance

            game = Game(game_constructor_ai)

            interface_dqn_player_arg = az_model_player
            if (
                not interface_dqn_player_arg
                and mcts_enabled_flag
                and not ai_enabled
                and not mcts_vs_dqn_enabled
            ):
                interface_dqn_player_arg = pure_mcts_player_instance

            interface_pure_mcts_ref_arg = pure_mcts_player_instance

            if d == 1:
                active_ai_for_d1 = (
                    interface_dqn_player_arg
                    if interface_dqn_player_arg
                    else interface_pure_mcts_ref_arg
                )

                interface = PyGameInterface(
                    dqn_player=active_ai_for_d1,
                    mcts_enabled=is_computer_game_active,
                    player_type=player_type,
                    game=game,
                    fullscreen_start=is_fullscreen,
                    initial_size=screen_size,
                    mcts_vs_dqn=mcts_vs_dqn_enabled,
                    mcts_vs_dqn_choice=mcts_vs_dqn_choice,
                )
            else:
                interface = PyGameInterfaceFeatures(
                    game=game,
                    dqn_player=interface_dqn_player_arg,
                    pure_mcts_ref=interface_pure_mcts_ref_arg,
                    mcts_enabled=is_computer_game_active,
                    player_type=player_type,
                    fullscreen_start=is_fullscreen,
                    initial_size=screen_size,
                    mcts_vs_dqn=mcts_vs_dqn_enabled,
                    mcts_vs_dqn_choice=mcts_vs_dqn_choice,
                )

            current_fullscreen_state = interface.run()
            if hasattr(interface, "screen_size"):
                current_screen_size = interface.screen_size
            else:
                current_screen_size = screen_size

    except KeyboardInterrupt:
        print("\n\nПрограмма остановлена!")
        print("Хорошего дня!\n")
    except Exception as e:
        print("Произошло исключение!")
        print(e)
        import traceback

        traceback.print_exc()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
