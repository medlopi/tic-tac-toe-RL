import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from app.basic_game_core.field import Field
from app.basic_game_core.node import Node
import numpy as np


def set_learning_rate(optimizer, lr):
    """Sets the learning rate to the given value"""
    for param_group in optimizer.param_groups:
        param_group["lr"] = lr


class Net(nn.Module):
    """policy-value network module"""

    def __init__(
        self,
        board_width,
        board_height,
        count_features,
        conv1_out=64,
        conv2_out=128,
        conv3_out=256,
        act_conv1_out=8,
        act_fc1_out=None,
        val_conv1_out=4,
        val_fc1_out=64,
    ):
        super(Net, self).__init__()

        self.board_width = board_width
        self.board_height = board_height
        self.count_features = count_features
        in_channels = 2 * count_features + 2

        # common layers
        self.conv1 = nn.Conv2d(in_channels, conv1_out, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(conv1_out, conv2_out, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(conv2_out, conv3_out, kernel_size=3, padding=1)

        # action policy layers
        self.act_conv1 = nn.Conv2d(conv3_out, act_conv1_out, kernel_size=1)
        if act_fc1_out is None:
            count_different_figures = 1 << (count_features - 1)
            act_fc1_out = board_width * board_height * count_different_figures
        self.act_fc1 = nn.Linear(
            act_conv1_out * board_width * board_height, act_fc1_out
        )

        # state value layers
        self.val_conv1 = nn.Conv2d(conv3_out, val_conv1_out, kernel_size=1)
        self.val_fc1 = nn.Linear(val_conv1_out * board_width * board_height, val_fc1_out)
        self.val_fc2 = nn.Linear(val_fc1_out, 1)

    def forward(self, state_input):
        # common layers
        x = F.relu(self.conv1(state_input))
        x = F.relu(self.conv2(x))
        x = F.relu(self.conv3(x))
        # action policy layers
        x_act = F.relu(self.act_conv1(x))
        if self.count_features == 1:
            x_act = x_act.view(-1, 4 * self.board_width * self.board_height)
        else:
            x_act = x_act.view(-1, self.act_conv1.out_channels * self.board_width * self.board_height)
        x_act = F.log_softmax(self.act_fc1(x_act), dim=1)
        # state value layers
        x_val = F.relu(self.val_conv1(x))
        if self.count_features == 1:
            x_val = x_val.view(-1, 2 * self.board_width * self.board_height)
        else:
            x_val = x_val.view(-1, self.val_conv1.out_channels * self.board_width * self.board_height)
        x_val = F.relu(self.val_fc1(x_val))
        x_val = F.tanh(self.val_fc2(x_val))
        return x_act, x_val


class PolicyValueNet:
    """policy-value network"""

    def __init__(
        self, board_width, board_height, count_features, model_file=None, use_gpu=False
    ):
        self.use_gpu = use_gpu
        self.board_width = board_width
        self.board_height = board_height
        self.count_features = count_features
        self.l2_const = 1e-4  # coef of l2 penalty

        net_kwargs = {}
        if model_file:
            net_params = torch.load(model_file, map_location="cpu")
            # Автоматически определяем размеры слоёв
            net_kwargs = {
                "conv1_out": net_params["conv1.weight"].shape[0],
                "conv2_out": net_params["conv2.weight"].shape[0],
                "conv3_out": net_params["conv3.weight"].shape[0],
                "act_conv1_out": net_params["act_conv1.weight"].shape[0],
                "act_fc1_out": net_params["act_fc1.weight"].shape[0],
                "val_conv1_out": net_params["val_conv1.weight"].shape[0],
                "val_fc1_out": net_params["val_fc1.weight"].shape[0],
            }

        if self.use_gpu:
            self.policy_value_net = Net(
                board_width, board_height, count_features, **net_kwargs
            ).cuda()
        else:
            self.policy_value_net = Net(
                board_width, board_height, count_features, **net_kwargs
            )
        self.optimizer = optim.Adam(
            self.policy_value_net.parameters(), weight_decay=self.l2_const
        )

        if model_file:
            self.policy_value_net.load_state_dict(net_params)

    def policy_value(self, state_batch):
        """
        input: a batch of states
        output: a batch of action probabilities and state values
        """
        if self.use_gpu:
            state_batch = torch.tensor(state_batch, dtype=torch.float32, device="cuda")
            log_act_probs, value = self.policy_value_net(state_batch)
            act_probs = np.exp(log_act_probs.data.cpu().numpy())
            return act_probs, value.data.cpu().numpy()
        else:
            state_batch = torch.as_tensor(np.array(state_batch), dtype=torch.float32)
            log_act_probs, value = self.policy_value_net(state_batch)
            act_probs = np.exp(log_act_probs.data.numpy())
            return act_probs, value.data.numpy()

    def policy_value_function(self, node: Node):
        available_moves = node.get_available_moves()
        count_different_figures = 1 << (Field.COUNT_FEATURES - 1)
        legal_positions = [
            (move.figure % count_different_figures) * Field.WIDTH * Field.HEIGHT
            + move.row * Field.WIDTH
            + move.col
            for move in available_moves
        ]
        current_state = np.ascontiguousarray(
            node.current_state().reshape(
                -1, 2 * self.count_features + 2, self.board_width, self.board_height
            )
        )
        if self.use_gpu:
            log_action_probs, score = self.policy_value_net(
                torch.tensor(current_state, dtype=torch.float32, device="cuda")
            )
            action_probs = np.exp(log_action_probs.data.cpu().numpy().flatten())
        else:
            log_action_probs, score = self.policy_value_net(
                torch.tensor(current_state, dtype=torch.float32)
            )
            action_probs = np.exp(log_action_probs.data.numpy().flatten())
        actions_with_probs = list(zip(available_moves, action_probs[legal_positions]))
        score = score.data[0][0]

        return actions_with_probs, score

    def train_step(self, state_batch, mcts_probs, winner_batch, lr):
        """perform a training step"""
        if self.use_gpu:
            state_batch = torch.tensor(state_batch, dtype=torch.float32, device="cuda")
            mcts_probs = torch.tensor(mcts_probs, dtype=torch.float32, device="cuda")
            winner_batch = torch.tensor(
                winner_batch, dtype=torch.float32, device="cuda"
            )
        else:
            state_batch = torch.as_tensor(np.array(state_batch), dtype=torch.float32)
            mcts_probs = torch.as_tensor(np.array(mcts_probs), dtype=torch.float32)
            winner_batch = torch.as_tensor(np.array(winner_batch), dtype=torch.float32)

        # zero the parameter gradients
        self.optimizer.zero_grad()
        # set learning rate
        set_learning_rate(self.optimizer, lr)

        # forward
        log_act_probs, value = self.policy_value_net(state_batch)
        # define the loss = (z - v)^2 - pi^T * log(p) + c||theta||^2
        # Note: the L2 penalty is incorporated in optimizer
        value_loss = F.mse_loss(value.view(-1), winner_batch)
        policy_loss = -torch.mean(torch.sum(mcts_probs * log_act_probs, 1))
        loss = value_loss + policy_loss
        # backward and optimize
        loss.backward()
        self.optimizer.step()
        # calc policy entropy, for monitoring only
        entropy = -torch.mean(torch.sum(torch.exp(log_act_probs) * log_act_probs, 1))
        return loss.item(), entropy.item()

    def get_policy_param(self):
        net_params = self.policy_value_net.state_dict()
        return net_params

    def save_model(self, model_file):
        """save model params to file"""
        net_params = self.get_policy_param()  # get model params
        torch.save(net_params, model_file)
