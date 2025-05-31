from app.game import Game
from app.mcts import MCTSPlayer
from app.start_menu import StartMenu
from app.interface import PyGameInterface
from app.game_config import MCTS_ITERATIONS
import pygame

def main():
    try:
        mcts_player = MCTSPlayer(
            puct_constant=5,
            playout_number=MCTS_ITERATIONS,
        )
        pygame.init()
        menu = StartMenu()
        m, n, k, ai_enabled = menu.run()
        if m > 0 and n > 0 and k > 0:
            game: Game = Game(mcts_player)
            # game.start_processing_input()
            interface = PyGameInterface(game)
            interface.run()
        
    except KeyboardInterrupt:
        print("\n\nProgram stopped!")
        print("Have a nice day!\n")
    except Exception as e:
        print("Exception!")
        print(e)


if __name__ == "__main__":
    main()
