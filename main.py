from app.game import Game
from app.mcts import MCTSPlayer
# from app.node import Node
from app.game_config import MCTS_ITERATIONS


def main():
    try:
        mcts_player = MCTSPlayer(
            puct_constant=5,
            playout_number=MCTS_ITERATIONS,
            selfplay=False, 
            policy_value_fn=None
        )

        game: Game = Game(mcts_player)
        game.start_processing_input()
        
    except KeyboardInterrupt:
        print("\n\nProgram stopped!")
        print("Have a nice day!\n")
    except Exception as e:
        print("Exception!")
        print(e)


if __name__ == "__main__":
    main()
