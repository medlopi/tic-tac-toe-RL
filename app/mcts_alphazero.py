from app.field import Field, GameStates
from app.node import Node
from app.player import Player
import numpy as np


def softmax(x):
    probs = np.exp(x - np.max(x))
    probs /= np.sum(probs)
    return probs


class MCTS:

    def __init__(self, policy_value_function, puct_constant, playout_number):
        self._root: Node = Node()
        self._policy_value_function = policy_value_function
        self._puct_constant: float = puct_constant
        self._playout_number: int = playout_number

    def _run_playout(self) -> None:
        node = self._root
        while True:
            if node.is_leaf():
                break
            action, node = node.select_action(self._puct_constant)

        actions_with_probs, leaf_value = self._policy_value_function(node)

        game_state = node.check_game_state()
        if game_state == GameStates.CONTINUE:
            node.expand_node(actions_with_probs)
        else:
            winner = node.define_winner(game_state)
            
            if winner == node.who_moves:
                leaf_value = 1
            elif winner == Player.Type.NONE:
                leaf_value = 0
            else:
                leaf_value = -1

        node.update_all_ancestors_recursively(-leaf_value)

    def get_move_probs(self, temperature_contant: float):
        for _ in range(self._playout_number):
            self._run_playout()

        actions_with_visits = [
            (action, node._visits_number) for action, node in self._root._children.items()
        ]
        actions, visits = zip(*actions_with_visits)
        action_probs = softmax(
            1.0 / temperature_contant * np.log(np.array(visits) + 1e-10)
        )

        return actions, action_probs

    def move_and_update(self, move: Field.Cell) -> None:
        if move in self._root._children:
            self._root = self._root._children[move]
        else:
            self._root = Node(self._root, move)
        self._root._parent = None


class MCTSPlayer:

    def __init__(self, policy_value_function, puct_constant: float,
                 playout_number: int, is_selfplay: bool):
        self.mcts = MCTS(policy_value_function, puct_constant, playout_number)
        self._is_selfplay = is_selfplay

    def reset_player(self) -> None:
        self.mcts._root = Node()

    def move_and_update(self, move: Field.Cell) -> None:
        self.mcts.move_and_update(move)
    
    def get_move(self, temperature_contant: float = 1e-3, return_prob: bool = False):
        count_different_figures = 1 << Field.COUNT_FEATURES
        move_probs = np.zeros(count_different_figures*Field.HEIGHT*Field.WIDTH)
        moves, probs = self.mcts.get_move_probs(temperature_contant)
        moves = [
            cell.figure * Field.WIDTH * Field.HEIGHT + cell.row * Field.WIDTH + cell.col 
            for cell in moves
        ]
        move_probs[list(moves)] = probs

        if self._is_selfplay:
            # add Dirichlet Noise for exploration
            move = np.random.choice(
                moves,
                p=0.75*probs + 0.25*np.random.dirichlet(0.3*np.ones(len(probs)))
            )
            move_cell = Field.Cell(
                move % (Field.WIDTH * Field.HEIGHT) // Field.WIDTH, 
                move % Field.WIDTH,
                move // (Field.WIDTH * Field.HEIGHT)
            )
            self.mcts.move_and_update(move_cell)
        else:
            # with the default temperature_contant=1e-3, it is almost
            # equivalent to choosing the move with the highest prob
            move = np.random.choice(moves, p=probs)
            move_cell = Field.Cell(
                move % (Field.WIDTH * Field.HEIGHT) // Field.WIDTH, 
                move % Field.WIDTH,
                move // (Field.WIDTH * Field.HEIGHT)
            )
            # print(f'Best move: {move_cell.row} {move_cell.col} {move_cell.figure}')

        if return_prob:
            return move_cell, move_probs
        else:
            return move_cell
