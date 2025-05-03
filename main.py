from app.starting_menu import StartMenu
from app.interface import PyGameInterface
from app.field import Field
from app.game import Game
import pygame

def main():
    pygame.init()
    menu = StartMenu()
    m, n, k, ai_enabled = menu.run()
    if m > 0 and n > 0 and k > 0:
        Field.set_dimensions(m, n, k)
        game = Game()
        game.ai_enabled = ai_enabled
        
        interface = PyGameInterface(game)
        interface.run()

if __name__ == "__main__":
    main()