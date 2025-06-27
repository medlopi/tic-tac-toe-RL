# tic-tac-toe RL

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey)
![Status](https://img.shields.io/badge/status-active-brightgreen)

## Содержание

- [О проекте](#о-проекте)
- [Требования](#требования)
- [Установка Python](#установка-python)
- [Быстрый старт](#быстрый-старт)
- [Краткое описание ключевых файлов](#краткое-описание-ключевых-файлов)
- [Как запускать?](#как-запускать)
- [Дополнительная информация](#дополнительная-информация)
- [Created by](#created-by)

## О проекте

Этот проект — исследовательская платформа для изучения и сравнения различных стратегий и алгоритмов обучения в обобщённой игре крестики-нолики (MxNxK, с произвольным числом свойств/фич).

**Возможности:**
- Анализ и поиск стратегий на полях любого размера и сложности.
- Изучение современных методов обучения с подкреплением (RL) и классических алгоритмов поиска (MCTS).
- Сравнение эффективности различных подходов (MCTS, AlphaZero, DQN) между собой и против человека.
- Подробная статистика, логи и визуализации для глубокого анализа партий и обучения.
- Гибкая настройка параметров игры и обучения через конфиги.

## Требования

- Python 3.10 или выше (рекомендуется Python 3.12)

## Установка Python

### macOS
```shell
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python@3.12
```

### Linux (Ubuntu/Debian)
```shell
sudo apt update
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

---

## Краткое описание ключевых файлов

- **main.py** — запуск графической игры (pygame).
  - **Режимы:**  
    • человек против ИИ  
    • ИИ против ИИ  
    • человек против человека  
    • автоматическая серия игр  
    • визуализация партий  
  - **Особенности:**  
    • Поддержка любых размеров поля (MxN), графический интерфейс поддерживает до 6 свойств (фич).  
    • Можно играть с классическим MCTS, AlphaZero, DQN ( для них уже есть готовые обученные модели в `app/models_training/models_files/`, имеется возможность обучить таковые для любого поля).  
    • Количество playout'ов для MCTS и DQN настраивается только в `app/basic_game_core/config/game_config.py`.  
    • Для визуализации партий используйте только этот файл.

- **bot_play.py** — запуск серии игр между ботами, анализ их силы. Не поддерживает визуализацию. Для визуализации используйте `main.py`.

- **count_states.py** — анализ дерева игры, подсчёт уникальных состояний.

- **app/models_training/train.py** — pipeline для обучения нейросети методом AlphaZero.

- **app/models_training/policy_value_net_torch.py** — архитектура нейросети (PyTorch).

- **app/models_training/models_files/** — готовые обученные модели для разных размеров поля.

- **app/basic_game_core/game.py, field.py, node.py, player.py** — базовая логика игры.

- **app/basic_game_core/config/game_config.py** — основные параметры игры (размеры поля, количество фич, настройки MCTS/DQN и др.).

- **app/basic_game_core/config/requirements.txt** — зависимости проекта.

---

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
  Запускает игру с графическим интерфейсом (pygame). Можно выбрать режимы: человек против ИИ, человек против MCTS, человек против человека и другие; визуализация партий. Поддерживается до 6 свойств!

### Запуск обучения AlphaZero

- **Windows:**
  ```shell
  python -m app.models_training.train
  ```
- **macOS/Linux:**
  ```shell
  python3 -m app.models_training.train
  ```
  Запускает pipeline для обучения нейросети методом AlphaZero. Все параметры обучения задаются внутри `train.py` и `game_config.py`. Модели и логи сохраняются в `app/models_training/models_files/` и `app/models_training/logs/`.

### Запуск игры ботов (AI vs AI)

- **Windows:**
  ```shell
  python -m bot_play
  ```
- **macOS/Linux:**
  ```shell
  python3 -m bot_play
  ```
  Запускает серию игр между двумя ботами (например, AlphaZero против чистого MCTS) и выводит статистику побед.  
  **Внимание:** визуализация не предусмотрена, только текстовая статистика. Для просмотра визуализации можно запустить `main.py`, предварительно указав нужные модели в коде.

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

---

## Дополнительная информация

- Все параметры игры (размер поля, количество фич, число итераций для MCTS/DQN и др.) настраиваются в `app/basic_game_core/config/game_config.py`.
- Готовые модели для DQN и AlphaZero лежат в `app/models_training/models_files/`.
- Для запуска на нестандартных полях или с большим количеством фич потребуется обучить новую модель.
- Для визуализации партий и ручной игры используйте только `main.py`.

---

## Created by:

### Ilya Peganov: [github](https://github.com/l3eg1nner), [telegram](https://t.me/ispeganov)

### Arseniy Pozdeyev: [github](https://github.com/medlopi), [telegram](https://t.me/medl0pi)

### Dmitry Sorochan: [github](https://github.com/DmitryS-01), [telegram](https://t.me/legenda0008)

### Ivan Fomin: [github](https://github.com/Shmel131), [telegram](https://t.me/gospodin_131)

---
