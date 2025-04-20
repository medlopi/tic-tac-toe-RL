from app.game import Game
from app.interface import PyGameInterface

def main():
    game = Game()
    interface = PyGameInterface()
    interface.game = game
    
    # Здесь выбираем, что запускать
    # Либо интерфейс (тогда консольная версия будет выводить только финальную доску):
    interface.run()
    # Либо консольную версию (тогда интерфейс будет тёмным окном):
    # game.start_processing_input()

    # И то, и другое запускать не надо (можно, но нет смысла)

if __name__ == "__main__":
    main()