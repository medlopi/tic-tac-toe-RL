import torch
import torch.nn as nn
import torch.optim as optim
from app.mcts import MCTS
from app.node import Node
from app.model import ModelWrapper
import os

def train_model(num_episodes=1000, save_path='models/tictactoe_model.pth'):
    # Создаем директорию для сохранения моделей, если её нет
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    # Инициализируем модель и оптимизатор
    model_wrapper = ModelWrapper()
    optimizer = optim.Adam(model_wrapper.model.parameters())
    criterion = nn.MSELoss()
    
    # Инициализируем MCTS для генерации данных
    mcts = MCTS()
    
    for episode in range(num_episodes):
        # Начинаем новую игру
        node = Node()
        states = []
        rewards = []
        
        # Играем игру до конца
        while not node.is_terminal():
            # Сохраняем текущее состояние
            states.append(node.board)
            
            # Делаем ход с помощью MCTS
            mcts.do_rollout(node)
            best_move = mcts.choose_best(node)
            node = node.make_move(best_move)
            
            # Получаем награду для текущего состояния
            reward = node.get_reward() if node.is_terminal() else 0
            rewards.append(reward)
        
        # Обучаем модель на собранных данных
        for state, reward in zip(states, rewards):
            # Преобразуем состояние в тензор
            state_tensor = model_wrapper.board_to_tensor(state)
            
            # Получаем предсказание модели
            prediction = model_wrapper.model(state_tensor.unsqueeze(0))
            
            # Вычисляем loss и обновляем веса
            target = torch.tensor([reward], dtype=torch.float32).to(model_wrapper.device)
            loss = criterion(prediction, target)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        
        if (episode + 1) % 100 == 0:
            print(f"Episode {episode + 1}/{num_episodes}, Loss: {loss.item():.4f}")
    
    # Сохраняем обученную модель
    model_wrapper.save_model(save_path)
    print(f"Model saved to {save_path}")

if __name__ == "__main__":
    train_model() 