from app.game import Game
from app.mcts import MCTS
from app.node import Node



def main():

    mcts = MCTS()

    board = Node()

    def train_MCTS(iterations : int):
        for i in range(iterations):
            mcts.do_rollout(board)

    train_MCTS(2000)

    game: Game = Game(mcts)

    game.start_processing_input()





if __name__ == "__main__":
    main()
