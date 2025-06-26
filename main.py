# main.py
import sys

if sys.version_info < (3, 10):
    print("Для работы программы требуется Python 3.10 или выше")
    sys.exit(1)


import pygame
from app.game import Game
from app.start_menu import StartMenu
# Ensure PyGameInterface is your old one, and PyGameInterfaceFeatures is the new one
from app.interface import PyGameInterface # Presumed old interface for d=1
from app.interface_features import PyGameInterfaceFeatures # Your new interface class
from app.game_config import MCTS_ITERATIONS, MCTS_AZ_ITERATIONS
from app.field import Field
from app.player import Player # Added for Player.Type if needed by menu/interface directly
from app.mcts_alphazero import MCTSPlayer as MCTS_AZ_Player 
from app.policy_value_net_torch import PolicyValueNet
from app.mcts import MCTSPlayer as Pure_MCTS_Player
# from app.game_config import MCTS_ITERATIONS # Already imported

def main():
    current_fullscreen_state = False
    current_screen_size = (1200, 800) # Adjusted default for features interface
    
    pygame.init()
    try:
        while True:
            menu = StartMenu(
                is_fullscreen_start=current_fullscreen_state,
                initial_size=current_screen_size
            )
            m, n, k, d, ai_enabled, mcts_enabled_flag, mcts_vs_dqn_enabled, mcts_vs_dqn_choice, player_type, is_fullscreen, screen_size = menu.run()

            if m <= 0 or n <= 0 or k <= 0: # d can be 1 or more
                print("Выход из игры.")
                break

            Field.set_dimensions(m, n, k, d)
            
            # These will hold the player instances
            az_model_player = None # For AlphaZero MCTS
            pure_mcts_player_instance = None # For Pure MCTS

            # Determine which AI is primary (az_model_player) and if pure_mcts_player_instance is also needed
            # is_computer_game_active will be true if any AI is involved (HvsAI or AIvsAI)
            is_computer_game_active = ai_enabled or mcts_enabled_flag or mcts_vs_dqn_enabled

            if ai_enabled or mcts_vs_dqn_enabled: # If AZ is potentially involved
                model_file = f'policy_{m}x{n}x{k}x{d}.model'
                print(f"Попытка загрузить модель AlphaZero: {model_file}")
                try:
                    policy_value_net = PolicyValueNet(m, n, d, model_file=model_file)
                    az_model_player = MCTS_AZ_Player(
                        policy_value_net.policy_value_function,
                        puct_constant=5,
                        playout_number=MCTS_AZ_ITERATIONS,
                        is_selfplay=False
                    )
                    print("AlphaZero модель загружена.")
                except FileNotFoundError:
                    print(f"ОШИБКА: Файл модели AlphaZero '{model_file}' не найден!")
                    if ai_enabled and not mcts_enabled_flag and not mcts_vs_dqn_enabled: # AZ was the only AI selected
                        print("AlphaZero была единственным ИИ. Переключение на чистый MCTS как основной ИИ.")
                        az_model_player = Pure_MCTS_Player( # Fallback to Pure MCTS in az_model_player var
                            puct_constant=5, 
                            playout_number=MCTS_ITERATIONS
                        )
                        # ai_enabled = False # No, keep it as is, az_model_player is now Pure MCTS
                        # mcts_enabled_flag = True
                    elif mcts_vs_dqn_enabled:
                         print("AlphaZero не найдена для режима AI vs AI. AZ будет заменен на Pure MCTS.")
                         az_model_player = Pure_MCTS_Player(
                            puct_constant=5, 
                            playout_number=MCTS_ITERATIONS
                        )


            if mcts_enabled_flag or mcts_vs_dqn_enabled: # If Pure MCTS is selected or needed for AIvsAI
                print("Инициализация Pure MCTS игрока.")
                pure_mcts_player_instance = Pure_MCTS_Player(
                    puct_constant=5,
                    playout_number=MCTS_ITERATIONS,
                )

            # Determine the single AI player for Game class (for its text mode, etc.)
            # This is less critical for PyGameInterface now.
            game_constructor_ai = None
            if az_model_player:
                game_constructor_ai = az_model_player
            elif pure_mcts_player_instance:
                game_constructor_ai = pure_mcts_player_instance
            
            game = Game(game_constructor_ai) # Game needs one AI for its internal logic if any

            # Determine the primary dqn_player for the interface (AZ or its fallback)
            # and the pure_mcts_ref (always pure mcts if it exists)
            interface_dqn_player_arg = az_model_player
            if not interface_dqn_player_arg and mcts_enabled_flag and not ai_enabled and not mcts_vs_dqn_enabled:
                # If only pure MCTS was selected for Human vs AI
                interface_dqn_player_arg = pure_mcts_player_instance
            
            interface_pure_mcts_ref_arg = pure_mcts_player_instance


            if d == 1: # Assuming d=1 is for the original interface
                # The old interface might need different player setup.
                # For simplicity, let's assume it also takes dqn_player and mcts_enabled flags
                # and internally picks one if needed.
                active_ai_for_d1 = interface_dqn_player_arg if interface_dqn_player_arg else interface_pure_mcts_ref_arg

                interface = PyGameInterface( # Old interface
                    dqn_player=active_ai_for_d1,
                    mcts_enabled=is_computer_game_active, 
                    player_type=player_type, 
                    game=game, 
                    fullscreen_start=is_fullscreen, 
                    initial_size=screen_size,
                    mcts_vs_dqn=mcts_vs_dqn_enabled, # Pass these along
                    mcts_vs_dqn_choice=mcts_vs_dqn_choice
                )
            else: # d > 1, use the new features interface
                interface = PyGameInterfaceFeatures(
                    game=game,
                    dqn_player=interface_dqn_player_arg, # Main AI (AZ or its fallback, or Pure MCTS if only that was chosen for HvsAI)
                    pure_mcts_ref=interface_pure_mcts_ref_arg, # Pure MCTS instance (can be None)
                    mcts_enabled=is_computer_game_active, # True if any AI involved
                    player_type=player_type, 
                    fullscreen_start=is_fullscreen, 
                    initial_size=screen_size,
                    mcts_vs_dqn=mcts_vs_dqn_enabled,
                    mcts_vs_dqn_choice=mcts_vs_dqn_choice
                )

            current_fullscreen_state = interface.run()
            # Ensure screen_size is updated for the next loop of the menu
            if hasattr(interface, 'screen_size'):
                 current_screen_size = interface.screen_size
            else: # Fallback if screen_size attribute isn't on the interface
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