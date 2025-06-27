# tic-tac-toe 

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

## Как запустить игру?

1. Для начала в **app/game_config.py** нужно выставить интересующие Вас настройки (#TODO: сделать это красивее).

2. Если впервые скачали проект, создайте виртуальное окружение и установите необходимые библиотеки:

### Windows
```shell
python -m venv .venv

.venv\Scripts\activate

pip install -r requirements.txt
```

### macOS/Linux
```shell
python3.12 -m venv .venv

source ./.venv/bin/activate

pip install -r requirements.txt
```

3. Чтобы запустить игру (или любой другой модуль):

**Важно:** Все команды запуска выполняйте из корня проекта! Если файл находится в подпапке, используйте запуск через `-m` и относительный путь через точку.

### Примеры:

#### Запуск основной игры

##### Windows
```shell
python -m main
```
##### macOS/Linux
```shell
python3 -m main
```

#### Запуск тренировки (пример)

##### Windows
```shell
python -m app.models.train
```
##### macOS/Linux
```shell
python3 -m app.models.train
```

В следующие разы достаточно активировать виртуальное окружение и запускать нужный модуль из корня проекта аналогично примеру выше.

## TODO

- см start_menu.py

- сделать нормальное разбиение файлов по папкам
