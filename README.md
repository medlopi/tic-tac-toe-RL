# tic-tac-toe RL

## Требования
- Python 3.10 или выше (рекомендуется Python 3.12)

## Установка Python

### macOS
1. Установите Homebrew, если еще не установлен:
```shell
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
2. Установите Python 3.12:
```shell
brew install python@3.12
```

### Linux (Ubuntu/Debian)
1. Обновите список пакетов:
```shell
sudo apt update
```
2. Установите Python 3.12:
```shell
sudo apt install python3.12 python3.12-venv
```

## Быстрый старт

1. Создайте виртуальное окружение и установите зависимости:

### Windows
```shell
python -m venv .venv
.venv\Scripts\activate
pip install -r app/basic_game_core/config/requirements.txt
```

### macOS/Linux
```shell
python3.12 -m venv .venv
source ./.venv/bin/activate
pip install -r app/basic_game_core/config/requirements.txt
```

2. При необходимости настройте параметры игры в `app/basic_game_core/config/game_config.py`.

## Краткое описание ключевых файлов

- **main.py** — запуск графической игры (pygame), поддержка разных режимов.
- **bot_play.py** — запуск серии игр между ботами, анализ их силы.
- **count_states.py** — анализ дерева игры, подсчёт уникальных состояний.
- **app/models_training/train.py** — обучение нейросети методом AlphaZero.
- **app/models_training/policy_value_net_torch.py** — архитектура нейросети (PyTorch).
- **app/basic_game_core/game.py, field.py, node.py, player.py** — базовая логика игры.
- **app/basic_game_core/config/game_config.py** — основные параметры игры (размеры поля, количество фич и т.д.).
- **app/basic_game_core/config/requirements.txt** — зависимости проекта.

## Как запускать?

**Все команды выполняйте из корня проекта!**

### Запуск графической игры

- **Windows:**
  ```shell
  python -m main
  ```
- **macOS/Linux:**
  ```shell
  python3 -m main
  ```
  
  Запускает игру с графическим интерфейсом (pygame). Можно выбрать режимы: человек против ИИ, ИИ против ИИ и т.д.

### Запуск обучения AlphaZero

- **Windows:**
  ```shell
  python -m app.models_training.train
  ```
- **macOS/Linux:**
  ```shell
  python3 -m app.models_training.train
  ```
  
  Запускает процесс обучения нейросети методом AlphaZero. Все параметры обучения задаются внутри train.py и game_config.py. Модели и логи сохраняются в app/models_training/models_files/ и app/models_training/logs/.

### Запуск боёв ботов (AI vs AI)

- **Windows:**
  ```shell
  python -m bot_play
  ```
- **macOS/Linux:**
  ```shell
  python3 -m bot_play
  ```
  
  Запускает серию игр между двумя ботами (например, AlphaZero против чистого MCTS) и выводит статистику побед.

### Подсчёт уникальных состояний игры

- **Windows:**
  ```shell
  python -m count_states
  ```
- **macOS/Linux:**
  ```shell
  python3 -m count_states
  ```
  
  Считает количество уникальных состояний в дереве игры для заданных параметров поля.
