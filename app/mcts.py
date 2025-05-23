from app.field import Field, GameStates
from app.node import Node
from app.player import Player
import numpy as np

def softmax(x):
    probs = np.exp(x - np.max(x))
    probs /= np.sum(probs)
    return probs


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

# MCTS AI part

    def _playout(self, board):
        """Run a single playout from the root to the leaf, getting a value at
        the leaf and propagating it back through its parents.
        State is modified in-place, so a copy must be provided.
        """
        k = 0
        node = self._root
        print(node._children)
        while True:
            if node.is_leaf():
                break
            act, new_node = node.select_action(self.puct_constant)
            node = new_node
            board.make_silent_move(act)
            k += 1
        print('kkkkkkkkkkk', k)
        action_probs, leaf_value = self._policy_value_function(board.current_state)

        game_res = board.current_state.check_game_state()

        
        if game_res == GameStates.CONTINUE:
            node.expand_node(action_probs)
            k += 1
        else:
            leaf_value = 1 if game_res == GameStates.CROSS_WON else (-1 if game_res == GameStates.NAUGHT_WON else 0)

        node.update_all_ancestors_recursively(-leaf_value)


    def get_move_probs(self, board, temp) -> Field.Cell:
        for _ in range(self._playout_number):
            self._playout(board)

        act_visits = [(act, node._n_visits)
                      for act, node in self._root._children.items()]
        acts, visits = zip(*act_visits)
        act_probs = softmax(1.0/temp * np.log(np.array(visits) + 1e-10))

        return acts, act_probs


class MCTSPlayer:

    def __init__(self, puct_constant: float, playout_number: int, selfplay, policy_value_fn):
        if policy_value_fn:
            self.mcts = MCTS(policy_value_fn, puct_constant, playout_number)
        else:
            self.mcts = MCTS(policy_value_function, puct_constant, playout_number)
        self._is_selfplay = selfplay

    def reset_player(self) -> None:
        self.mcts = MCTS(policy_value_function, self.mcts._puct_constant, self.mcts._playout_number)

    def get_move(self) -> Field.Cell:
        return self.mcts.get_move()
    
    def set_player_ind(self, p):
        self.player = p
    
    def get_action_AI(self, board, *args, temp=1e-3, return_prob=0):
        sensible_moves = board.current_state.get_available_moves()

        # the pi vector returned by MCTS as in the alphaGo Zero paper
        move_probs = np.zeros(Field.HEIGHT*Field.WIDTH)
        if len(sensible_moves) > 0:
            acts, probs = self.mcts.get_move_probs(board, temp)
            move_probs[list(acts)] = probs
            if self._is_selfplay:
                # add Dirichlet Noise for exploration (needed for
                # self-play training)
                move = np.random.choice(
                    acts,
                    p=0.75*probs + 0.25*np.random.dirichlet(0.3*np.ones(len(probs)))
                )
                # update the root node and reuse the search tree
                self.mcts.update_with_move(move)
            else:
                # with the default temp=1e-3, it is almost equivalent
                # to choosing the move with the highest prob
                move = np.random.choice(acts, p=probs)
                # reset the root node
                self.mcts.update_with_move(-1)
#                location = board.move_to_location(move)
#                print("AI move: %d,%d\n" % (location[0], location[1]))

            if return_prob:
                return move, move_probs
            else:
                return move
        else:
            print("WARNING: the board is full")
    
    def move_and_update(self, move: Field.Cell) -> None:
        self.mcts.move_and_update(move)