from app.mcts.mcts_alphazero import MCTSPlayer as MCTS_AZ_player
from app.mcts.mcts import MCTSPlayer as MCTS_player
from app.models_training.policy_value_net_torch import PolicyValueNet
from app.basic_game_core.field import Field
from collections import defaultdict
from app.basic_game_core.game import Game

policy_value_net = PolicyValueNet(
    Field.WIDTH, Field.HEIGHT, model_file="best_policy_8x8x5.model"
)


az_mcts_player1 = MCTS_AZ_player(
    policy_value_net.policy_value_function, 5, 3000, is_selfplay=False
)
pure_mcts_player1 = MCTS_player(5, 10000)
az_mcts_player2 = MCTS_AZ_player(
    policy_value_net.policy_value_function, 5, 2000, is_selfplay=False
)
pure_mcts_player2 = MCTS_player(5, 5000)


game = Game(pure_mcts_player1)


win_cnt = defaultdict(int)
play_num = 50
for i in range(play_num):
    winner = game.start_bot_play(
        az_mcts_player1, pure_mcts_player1, 0  # 0 - az mcts, 1 - pure mcts
    )
    win_cnt[winner] += 1
    win_ratio = 1.0 * (win_cnt[1] + 0.5 * win_cnt[-1]) / play_num
    print(
        "num_playouts:{}, win: {}, lose: {}, tie:{}".format(
            play_num, win_cnt[1], win_cnt[0], win_cnt[-1]
        )
    )

print(
    "num_playouts:{}, win: {}, lose: {}, tie:{}".format(
        play_num, win_cnt[1], win_cnt[0], win_cnt[-1]
    )
)
print(win_cnt, win_ratio)


for i in range(play_num):
    winner = game.start_bot_play(
        az_mcts_player1, pure_mcts_player1, 1  # 0 - az mcts, 1 - pure mcts
    )
    win_cnt[winner] += 1
    win_ratio = 1.0 * (win_cnt[1] + 0.5 * win_cnt[-1]) / play_num
    print(
        "num_playouts:{}, win: {}, lose: {}, tie:{}".format(
            play_num, win_cnt[1], win_cnt[0], win_cnt[-1]
        )
    )

print(
    "num_playouts:{}, win: {}, lose: {}, tie:{}".format(
        play_num, win_cnt[1], win_cnt[0], win_cnt[-1]
    )
)
print(win_cnt, win_ratio)
