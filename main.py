import sys

if sys.version_info < (3, 10):
    print("Для работы программы требуется Python 3.10 или выше")
    sys.exit(1)


import pygame
from app.game import Game
from app.start_menu import StartMenu
from app.interface import PyGameInterface
from app.interface_features import PyGameInterface as PyGameInterfaceFeatures
from app.game_config import MCTS_ITERATIONS, MCTS_AZ_ITERATIONS
from app.field import Field
from app.mcts_alphazero import MCTSPlayer as MCTS_AZ_Player 
from app.policy_value_net_torch import PolicyValueNet
from app.mcts import MCTSPlayer as Pure_MCTS_Player
from app.game_config import MCTS_ITERATIONS

def main():
    current_fullscreen_state = False
    current_screen_size = (800, 600)
    
    pygame.init()
    try:
        while True:
            menu = StartMenu(
                is_fullscreen_start=current_fullscreen_state,
                initial_size=current_screen_size
            )
            m, n, k, d, ai_enabled, mcts_enabled, mcts_vs_dqn_enabled, mcts_vs_dqn_choice, player_type, is_fullscreen, screen_size = menu.run()

            if m <= 0 or n <= 0 or k <= 0 or d <= 0:
                print("Выход из игры.")
                break

            Field.set_dimensions(m, n, k, d)
            dqn_player = None
            mcts_player = None
            
            if mcts_enabled:
                print("Режим игры: Чистый MCTS")
                mcts_player = Pure_MCTS_Player(
                    puct_constant=5,
                    playout_number=MCTS_ITERATIONS,
                )
            elif ai_enabled:
                print("Режим игры: AlphaZero ИИ (с нейросетью)")
                model_file = f'policy_{m}x{n}x{k}x{d}.model'
                print(f"Попытка загрузить модель: {model_file}")
                
                try:
                    policy_value_net = PolicyValueNet(m, n, d, model_file=model_file)
                    dqn_player = MCTS_AZ_Player(
                        policy_value_net.policy_value_function,
                        puct_constant=5,
                        playout_number=MCTS_AZ_ITERATIONS,
                        is_selfplay=False
                    )
                except FileNotFoundError:
                    print(f"ОШИБКА: Файл модели '{model_file}' не найден!")
                    print("Переключение на чистый MCTS.")
                    mcts_player = Pure_MCTS_Player(
                        puct_constant=5, 
                        playout_number=MCTS_ITERATIONS
                    )
                    mcts_enabled = True
                    ai_enabled = False

            elif mcts_vs_dqn_enabled:
                print("Режим игры: MCTS vs DQN")
                mcts_player = Pure_MCTS_Player(
                    puct_constant=5,
                    playout_number=MCTS_ITERATIONS,
                )
        
                model_file = f'policy_{m}x{n}x{k}x{d}.model'
                print(f"Попытка загрузить модель: {model_file}")
                
                try:
                    policy_value_net = PolicyValueNet(m, n, d, model_file=model_file)
                    dqn_player = MCTS_AZ_Player(
                        policy_value_net.policy_value_function,
                        puct_constant=5,
                        playout_number=MCTS_AZ_ITERATIONS,
                        is_selfplay=False
                    )
                except FileNotFoundError:
                    print(f"ОШИБКА: Файл модели '{model_file}' не найден!")
                    print("Переключение на чистый MCTS.")
                    mcts_player = Pure_MCTS_Player(
                        puct_constant=5, 
                        playout_number=MCTS_ITERATIONS
                    )
                    mcts_enabled = False
                    ai_enabled = False


            game = Game(mcts_player if mcts_player is not None else dqn_player)
            is_computer_game = mcts_enabled or ai_enabled

            if d == 1:
                interface = PyGameInterface(
                    dqn_player=dqn_player if dqn_player is not None else mcts_player,
                    mcts_enabled=is_computer_game, 
                    player_type=player_type, 
                    game=game, 
                    fullscreen_start=is_fullscreen, 
                    initial_size=screen_size,
                    mcts_vs_dqn=mcts_vs_dqn_enabled,
                    mcts_vs_dqn_choice=mcts_vs_dqn_choice
                )
            else:
                interface = PyGameInterfaceFeatures(
                    dqn_player=dqn_player if dqn_player is not None else mcts_player,
                    mcts_enabled=is_computer_game, 
                    player_type=player_type, 
                    game=game, 
                    fullscreen_start=is_fullscreen, 
                    initial_size=screen_size,
                    mcts_vs_dqn=mcts_vs_dqn_enabled,
                    mcts_vs_dqn_choice=mcts_vs_dqn_choice
                )

            current_fullscreen_state = interface.run()
            current_screen_size = interface.screen_size if hasattr(interface, 'screen_size') else screen_size
        
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