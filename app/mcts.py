from app.field import Field, GameStates
from app.node import Node
from app.player import Player
import numpy as np


def rollout_policy_function(node: Node) -> list[tuple[Field.Cell, float]]:
    available_moves = node.get_available_moves()
    move_probabilities = np.random.rand(len(available_moves))  # random rollout
    return zip(available_moves, move_probabilities)


def policy_value_function(node: Node) -> list[tuple[Field.Cell, float]]:
    available_moves = node.get_available_moves()
    action_probs = np.ones(len(available_moves)) / len(available_moves)
    return zip(available_moves, action_probs)


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

        game_state = node.check_game_state()
        if game_state == GameStates.CONTINUE:
            node.expand_node(self._policy_value_function(node))
        leaf_value = self._run_rollout(node)
        node.update_all_ancestors_recursively(-leaf_value)

    def _run_rollout(self, node: Node) -> int:
        player = node.who_moves
        winner = Player.Type.NONE
        while True:
            game_state = node.check_game_state()
            if game_state != GameStates.CONTINUE:
                if game_state == GameStates.CROSS_WON:
                    winner = Player.Type.CROSS
                elif game_state == GameStates.NAUGHT_WON:
                    winner = Player.Type.NAUGHT
                break
             
            action = max(
                rollout_policy_function(node),
                key=lambda action: action[1]
            )[0]
            node = Node(node, action)
            
        if winner == Player.Type.NONE:  # tie
            return 0
        else:
            return 1 if winner == player else -1

    def get_move(self) -> Field.Cell:
        for _ in range(self._playout_number):
            self._run_playout()
        return max(self._root._children.items(),
                   key=lambda child: child[1]._visits_number)[0]

    def move_and_update(self, move: Field.Cell) -> None:
        if move in self._root._children:
            self._root = self._root._children[move]
        else:
            self._root = Node(self._root, move)
        self._root._parent = None


class MCTSPlayer:

    def __init__(self, puct_constant: float, playout_number: int):
        self.mcts = MCTS(policy_value_function, puct_constant, playout_number)

    def reset_player(self) -> None:
        self.mcts._root = Node()

    def get_move(self) -> Field.Cell:
        return self.mcts.get_move()
    
    def move_and_update(self, move: Field.Cell) -> None:
        self.mcts.move_and_update(move)