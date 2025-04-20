# TODO добавить стартовое меню перед началом игры (с вводом параметров MxNxK + с переключением на игру с ИИ)
# TODO добавить нормальное центрирование поля
# TODO добавить уменьшение клеток при увеличении размера поля (поле может не влезть в экран)
# TODO такое ощущение, что зачёркивание победной линии чертой не всегда выглядит красиво. Можно попробовать сделать овал вокруг победной линии

import pygame
from pygame.locals import *
from app.game import Game
from app.field import Field
from app.player import Player

pygame.init()

# Цветовая гамма TODO поменять, если людям такая не нравится
COLOR_BG = (140, 140, 140)
COLOR_FIELD_BG = (180, 180, 180)
COLOR_STATUS = (53, 0, 211)
COLOR_MESSAGE = (36, 0, 144)
COLOR_GRID = (25, 0, 97)
COLOR_TEXT = (220, 220, 220)
COLOR_X_MAIN = (255, 75, 75)
COLOR_X_OUTLINE = (255, 180, 180)
COLOR_O_MAIN = (75, 255, 75)
COLOR_O_OUTLINE = (180, 255, 180)
COLOR_WIN_LINE = (0, 0, 0)

CELL_SIZE = 80  # Размер ячейки (не изменяется) TODO уменьшать при увеличении поля
STATUS_HEIGHT = 50
MESSAGE_HEIGHT = 40
PADDING = 20
MIN_WIDTH = 400  # Минимальная ширина окна

class PyGameInterface:
    def __init__(self, game=None):
        self.game = game if game else Game()
        self.running = True
        self.game_over = False
        self.win_line = None
        self.fullscreen = False
        self.game_over_start_time = 0
        self.game_over_duration = 3000
        self.game_msg = "Game in progress"
        
        # Рассчитываем размеры окна по умолчанию
        self.default_width = max(Field.WIDTH * CELL_SIZE + PADDING * 2, MIN_WIDTH)
        self.default_height = Field.HEIGHT * CELL_SIZE + STATUS_HEIGHT + MESSAGE_HEIGHT + PADDING * 2
        
        self.init_window()
        self.update_game_state()

    def init_window(self):
        self.screen = pygame.display.set_mode(
            (self.default_width, self.default_height), 
            pygame.RESIZABLE
        )
        pygame.display.set_caption("MxNxK Game")
        self.handle_resize()

    def handle_resize(self):
        """
        Пересчет позиций при изменении размера окна
        """
        screen_width, screen_height = self.screen.get_size()
        
        # Расчет позиции игрового поля
        self.field_width = Field.WIDTH * CELL_SIZE
        self.field_height = Field.HEIGHT * CELL_SIZE
        self.field_x = (screen_width - self.field_width) // 2
        self.field_y = STATUS_HEIGHT + MESSAGE_HEIGHT + PADDING
        
        # Проверяем, чтобы поле не выходило за границы экрана
        if self.field_x < PADDING:
            self.field_x = PADDING
            self.field_width = screen_width - PADDING * 2
            
        # Обновляем высоту, если нужно
        required_height = self.field_y + self.field_height + PADDING
        if not self.fullscreen and screen_height < required_height:
            self.screen = pygame.display.set_mode(
                (screen_width, required_height), 
                pygame.RESIZABLE
            )

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            current_time = pygame.time.get_ticks()
            if self.game_over and (current_time - self.game_over_start_time) > self.game_over_duration:
                self.reset_game()
            for event in pygame.event.get():
                self.handle_event(event)
            
            self.draw()
            pygame.display.flip()
            clock.tick(30)

        pygame.quit()

    def handle_event(self, event):
        if event.type == QUIT:
            self.running = False
        elif event.type == MOUSEBUTTONDOWN:
            if self.game_over:
                self.reset_game()
            else:
                self.handle_click(event.pos)
        elif event.type == KEYDOWN:
            if event.key == K_f:
                self.toggle_fullscreen()
        elif event.type == VIDEORESIZE:
            if not self.fullscreen:
                self.handle_resize()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.windowed_size = self.screen.get_size()
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        self.handle_resize()

    def handle_click(self, pos):
        col = (pos[0] - self.field_x) // CELL_SIZE
        row = (pos[1] - self.field_y) // CELL_SIZE
        
        if 0 <= row < Field.HEIGHT and 0 <= col < Field.WIDTH:
            if self.game.current_state.field[row][col] == Player.Type.NONE:
                self.game._Game__make_move(row, col)
                self.update_game_state()


    def update_game_state(self):
        state = self.game._Game__check_game_state()
        
        current_player = self.game.current_state.who_moves
        self.status_msg = f"Current: {Player.Icon[current_player]}"
        
        if state == self.game.GameStates.CONTINUE:
            self.game_msg = "Game in progress"
            self.game_over = False
            self.win_line = None
        else:
            self.game_over = True
            if state == self.game.GameStates.CROSS_WON:
                self.game_msg = "Crosses Victory! Click to restart"
            elif state == self.game.GameStates.NAUGHT_WON:
                self.game_msg = "Noughts Victory! Click to restart"
            elif state == self.game.GameStates.TIE:
                self.game_msg = "Tie! Click to restart"
            
            self.win_line = self.find_win_line()
            self.game_over_start_time = pygame.time.get_ticks()

    def draw(self):
        self.screen.fill(COLOR_BG)
        self.draw_status_bar()
        self.draw_message_panel()
        self.draw_game_field()
        
        if self.game_over:
            self.draw_win_line()  # Рисуем победную черту поверх поля
            self.draw_game_over()

    def draw_status_bar(self):
        # Рисуем панель с тем, кто ходит
        screen_width = self.screen.get_width()
        pygame.draw.rect(self.screen, COLOR_STATUS, (0, 0, screen_width, STATUS_HEIGHT))
        
        # Центрируем текст в панели
        font = pygame.font.SysFont('Arial', 28, bold=True)
        text = font.render(self.status_msg, True, COLOR_TEXT)
        text_rect = text.get_rect(center=(screen_width//2, STATUS_HEIGHT//2))
        self.screen.blit(text, text_rect)

    def draw_message_panel(self): # Аналогично
        screen_width = self.screen.get_width()
        pygame.draw.rect(self.screen, COLOR_MESSAGE, 
                        (0, STATUS_HEIGHT, screen_width, MESSAGE_HEIGHT))
      
        font = pygame.font.SysFont('Arial', 24)
        text = font.render(self.game_msg, True, COLOR_TEXT)
        text_rect = text.get_rect(center=(screen_width//2, STATUS_HEIGHT + MESSAGE_HEIGHT//2))
        self.screen.blit(text, text_rect)

    def draw_game_field(self):
        pygame.draw.rect(self.screen, COLOR_FIELD_BG, (
            self.field_x - 10,
            self.field_y - 10 + PADDING,
            self.field_width + 20,
            self.field_height + 20
        ), border_radius=10)

        for row in range(Field.HEIGHT):
            for col in range(Field.WIDTH):
                x = self.field_x + col * CELL_SIZE
                y = self.field_y + row * CELL_SIZE + PADDING
                self.draw_cell(x, y, row, col)

       

    def draw_cell(self, x, y, row, col):
        # Рисуем границы между клетками
        pygame.draw.rect(self.screen, COLOR_GRID, (x, y, CELL_SIZE, CELL_SIZE), 3)
        
        # Красивые Х и О
        cell = self.game.current_state.field[row][col]
        if cell == Player.Type.CROSS:
            # Окантовка крестика
            pygame.draw.line(self.screen, COLOR_X_OUTLINE,
                            (x + 10, y + 10), (x + CELL_SIZE - 10, y + CELL_SIZE - 10), 8)
            pygame.draw.line(self.screen, COLOR_X_OUTLINE,
                            (x + CELL_SIZE - 10, y + 10), (x + 10, y + CELL_SIZE - 10), 8)
            # Собственно крестик
            pygame.draw.line(self.screen, COLOR_X_MAIN,
                            (x + 15, y + 15), (x + CELL_SIZE - 15, y + CELL_SIZE - 15), 6)
            pygame.draw.line(self.screen, COLOR_X_MAIN,
                            (x + CELL_SIZE - 15, y + 15), (x + 15, y + CELL_SIZE - 15), 6)
        
        elif cell == Player.Type.NAUGHT:
            # Окантовка нолика
            pygame.draw.circle(self.screen, COLOR_O_OUTLINE,
                            (x + CELL_SIZE//2, y + CELL_SIZE//2),
                            CELL_SIZE//2 - 10, 8)
            # Собственно нолик
            pygame.draw.circle(self.screen, COLOR_O_MAIN,
                            (x + CELL_SIZE//2, y + CELL_SIZE//2),
                            CELL_SIZE//2 - 13, 6)

    def draw_win_line(self):
        if self.win_line:
            # Анимация длится 0.8 секунды
            progress = min(1.0, (pygame.time.get_ticks() - self.game_over_start_time) / 800)
            start_row, start_col, end_row, end_col = self.win_line
            
            # Координаты 
            x1 = self.field_x + start_col * CELL_SIZE + CELL_SIZE//2
            y1 = self.field_y + start_row * CELL_SIZE + CELL_SIZE//2 + PADDING
            x2 = self.field_x + end_col * CELL_SIZE + CELL_SIZE//2
            y2 = self.field_y + end_row * CELL_SIZE + CELL_SIZE//2 + PADDING
            
            # Для диагональных линий корректируем координаты, чтобы линия проходила точно через центры
            if abs(start_row - end_row) == abs(start_col - end_col):
                if start_col < end_col:
                    x1 -= CELL_SIZE//4
                    x2 += CELL_SIZE//4
                else:
                    x1 += CELL_SIZE//4
                    x2 -= CELL_SIZE//4
                    
                if start_row < end_row:
                    y1 -= CELL_SIZE//4
                    y2 += CELL_SIZE//4
                else:
                    y1 += CELL_SIZE//4
                    y2 -= CELL_SIZE//4
            
            current_x = x1 + (x2 - x1) * progress
            current_y = y1 + (y2 - y1) * progress
            pygame.draw.line(self.screen, COLOR_WIN_LINE, (x1, y1), (current_x, current_y), 6)

    def draw_game_over(self):
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.screen.blit(overlay, (0, 0))
        
        font = pygame.font.SysFont('Arial', 48, bold=True)
        
        # Разбиваем сообщение на две строки, чтобы оно не выходило за края при маленьком экране
        lines = self.game_msg.split("!")
        if len(lines) > 1:
            lines = [lines[0] + "!", lines[1]]
        else:
            lines = [self.game_msg, "Click to restart"]
        
        y_offset = -40
        for i, line in enumerate(lines):
            text = font.render(line, True, COLOR_TEXT)
            text_rect = text.get_rect(
                center=(self.screen.get_width()//2, 
                    self.screen.get_height()//2 + y_offset*i)
            )
            self.screen.blit(text, text_rect)

    def reset_game(self):
        self.game._Game__reset_game()
        self.game_over = False
        self.win_line = None
        self.update_game_state()

    def find_win_line(self): # Нам нужен не просто факт победы (как в солвере). Нужны координаты победной линии
        field = self.game.current_state.field
        last_move = self.game.get_last_move()  # Используем геттер из game.py
        
        if not last_move or last_move.row == -1:
            return None
        
        player = field[last_move.row][last_move.col]
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for dr, dc in directions:
            line = self.check_direction(field, last_move.row, last_move.col, dr, dc, player)
            if line:
                return line
        return None

    def check_direction(self, field, row, col, dr, dc, player):
        # Находим начальную точку линии
        start_r, start_c = row, col
        while True:
            next_r = start_r - dr
            next_c = start_c - dc
            if 0 <= next_r < Field.HEIGHT and 0 <= next_c < Field.WIDTH and field[next_r][next_c] == player:
                start_r, start_c = next_r, next_c
            else:
                break

        # Конечную
        end_r, end_c = row, col
        while True:
            next_r = end_r + dr
            next_c = end_c + dc
            if 0 <= next_r < Field.HEIGHT and 0 <= next_c < Field.WIDTH and field[next_r][next_c] == player:
                end_r, end_c = next_r, next_c
            else:
                break

        # Проверяем длину найденной линии
        if abs(end_r - start_r) + 1 >= Field.STREAK_TO_WIN or abs(end_c - start_c) + 1 >= Field.STREAK_TO_WIN:
            return (start_r, start_c, end_r, end_c)
        
        return None

if __name__ == "__main__":
    interface = PyGameInterface()
    interface.run()