from app.game import Game
from app.mcts import MCTS
from app.node import Node
from app.game_config import MCTS_ITERATIONS

from app.system import measure_performance


def main():

    mcts = MCTS()

    board = Node()

    @measure_performance
    def train_MCTS(iterations : int):
        print("training started . . .")
        
        for _ in range(iterations):
            mcts.do_rollout(board)

    train_MCTS(MCTS_ITERATIONS)

    game: Game = Game(mcts)

    game.start_processing_input()


if __name__ == "__main__":
    main()
