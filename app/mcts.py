import math
from app.field import Field
from collections import defaultdict


class MCTS:
    def __init__(self):
        self.wins_number = defaultdict(int) 
        self.games_number = defaultdict(int) 
        self.children_of_expanded_nodes = dict()
        self.exploration_weight = 1 / math.sqrt(2)


    def choose_best(self, node) -> Field.Cell :
        if node.is_terminal():
            print("Ты че дурной?!")
            return Field.Cell(-1, -1)

        if node not in self.children_of_expanded_nodes.keys():
            random_state = node.get_random_child()   # there is no expanded children
            print("дал рандом")
            return random_state.last_move 

        def score(n):
            if self.games_number[n] == 0:
                return float("-inf")  # avoid unseen moves
            return self.wins_number[n] / self.games_number[n]  # average reward

        best_state = max(self.children_of_expanded_nodes[node], key=score)

        return best_state.last_move
        

    def do_rollout(self, node):
        """
        make one iteration of train -- one game from start to terminal state
        """
        path = self._select_path(node)
        leaf = path[-1]
        self._expand(leaf)
        reward = self._simulate(leaf)
        self._backpropagate(path, reward)

    def _select_path(self, node):
        path = []
        while True:
            path.append(node)
            if node not in self.children_of_expanded_nodes or not self.children_of_expanded_nodes[node]:
                # node is not expanded yet or node is terminal
                return path

            not_expanded_children = self.children_of_expanded_nodes[node] - self.children_of_expanded_nodes.keys()
            if not_expanded_children:
                child = not_expanded_children.pop()
                path.append(child)
                return path
            node = self._uct_select(node)
            

    def _expand(self, node):
        "Update the `children` dict with the children of `node`"
        if node in self.children_of_expanded_nodes:
            return #already expanded 
        self.children_of_expanded_nodes[node] = node.get_children()

    def _simulate(self, node):
        "Returns the reward for a random simulation (to completion) of `node`"
        invert_reward = True
        while True:
            if node.is_terminal():
                reward = node.get_reward()
                return 1 - reward if invert_reward else reward
            node = node.get_random_child()
            invert_reward = not invert_reward

    def _backpropagate(self, path, reward):
        "Send the reward back up to the ancestors of the leaf"
        for node in reversed(path):
            self.games_number[node] += 1
            self.wins_number[node] += reward
            reward = 1 - reward  # 1 for me is 0 for my enemy, and vice versa



    
    def _uct_select(self, node):
        """
        "Select a child of node, balancing exploration & exploitation"
        """
        log_N_vertex = math.log(self.games_number[node])

        def uct(n):
            "Upper confidence bound for trees"
            return self.wins_number[n] / self.games_number[n] + self.exploration_weight * math.sqrt(
                log_N_vertex / self.games_number[n]
            )

        return max(self.children_of_expanded_nodes[node], key=uct)