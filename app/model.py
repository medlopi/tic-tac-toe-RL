import torch
import torch.nn as nn
import torch.nn.functional as F
# import numpy as np

class TicTacToeNet(nn.Module):
    def __init__(self):
        super(TicTacToeNet, self).__init__()
        # Входной слой: 9 клеток поля (3x3)
        self.fc1 = nn.Linear(9, 64)
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, 1)  # Выход: оценка позиции
        
    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = torch.sigmoid(self.fc3(x))  # Нормализуем выход в диапазон [0,1]
        return x

class ModelWrapper:
    def __init__(self, model_path=None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = TicTacToeNet().to(self.device)
        if model_path:
            self.load_model(model_path)
        
    def board_to_tensor(self, board):
        # Преобразуем состояние доски в тензор
        board_tensor = torch.zeros(9, dtype=torch.float32)
        for i in range(3):
            for j in range(3):
                cell = board[i][j]
                if cell == 'X':
                    board_tensor[i*3 + j] = 1
                elif cell == 'O':
                    board_tensor[i*3 + j] = -1
        return board_tensor.to(self.device)
    
    def evaluate_position(self, board):
        with torch.no_grad():
            board_tensor = self.board_to_tensor(board)
            return self.model(board_tensor.unsqueeze(0)).item()
    
    def save_model(self, path):
        torch.save(self.model.state_dict(), path)
    
    def load_model(self, path):
        self.model.load_state_dict(torch.load(path, map_location=self.device))
        self.model.eval() 
        