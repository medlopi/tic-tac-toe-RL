from app.start_menu import StartMenu
import pygame
import threading
from pygame.locals import *
from app.game import Game
from app.field import Field, GameStates
from app.player import Player
from app.mcts import MCTSPlayer
from app.game_config import MCTS_ITERATIONS

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
STATUS_HEIGHT = 50
MESSAGE_HEIGHT = 40
PADDING = 20
MIN_WIDTH = 400
COLOR_MENU_BUTTON = (120, 80, 180)
MENU_BUTTON_WIDTH = 100
MENU_BUTTON_HEIGHT = STATUS_HEIGHT - 10

class PyGameInterface:
    def __init__(self, mcts_enabled : bool, player_type : Player.Type, game=None, fullscreen_start=False, initial_size=None):
        self.game = game if game else Game()
        self.running = True
        self.game_over = False
        self.win_line = None
        self.fullscreen = fullscreen_start
        self.initial_size = initial_size
        if fullscreen_start:
            self.windowed_size = initial_size
        self.game_over_start_time = 0
        self.game_over_duration = 3000
        self.game_msg = "Game in progress"
        self.mcts_enabled = mcts_enabled
        self.player_type = player_type
        self.need_computer_move = True if (mcts_enabled and player_type == Player.Type.NAUGHT) else False
        self.allowed_to_click = False 
        self.update_allowed_click() 
        self.cell_size = self.calculate_cell_size()
        self.init_window()
        self.update_game_state()

    def calculate_cell_size(self):
        return 780 // max(Field.HEIGHT, Field.WIDTH)

    def init_window(self):
        flags = 0
        size = (0, 0)

        if self.fullscreen:
            flags = pygame.FULLSCREEN
            size = (0, 0)
        elif self.initial_size:
            flags = pygame.RESIZABLE
            size = self.initial_size
        else:
            flags = pygame.RESIZABLE
            self.default_width = max(Field.WIDTH * self.cell_size + PADDING*2, MIN_WIDTH)
            self.default_height = Field.HEIGHT * self.cell_size + STATUS_HEIGHT + MESSAGE_HEIGHT + PADDING*2
            size = (self.default_width, self.default_height)
        
        self.screen = pygame.display.set_mode(size, flags)
        pygame.display.set_caption("MxNxK Game")
        self.handle_resize()


    def update_allowed_click(self):
        """Обновляет разрешение на клики на основе текущего игрока"""
        if self.mcts_enabled:
            self.allowed_to_click = (self.game.current_state.who_moves == self.player_type)
            self.need_computer_move = (self.game.current_state.who_moves != self.player_type)
        else:
            self.allowed_to_click = True

    def handle_resize(self):
        screen_width, screen_height = self.screen.get_size()
        self.cell_size = self.calculate_cell_size()
        self.field_width = Field.WIDTH * self.cell_size
        self.field_height = Field.HEIGHT * self.cell_size
        self.field_x = (screen_width - self.field_width) // 2
        self.field_y = STATUS_HEIGHT + MESSAGE_HEIGHT + PADDING
        
        if self.field_x < PADDING:
            self.field_x = PADDING
            self.field_width = screen_width - PADDING*2
            
        required_height = self.field_y + self.field_height + PADDING
        if not self.fullscreen and screen_height < required_height:
            self.screen = pygame.display.set_mode((screen_width, required_height), pygame.RESIZABLE)

    def run(self):
        print("RUNNING")
        clock = pygame.time.Clock()
        calculated_move = None
        calculating_thread = None

        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)
            
            current_time = pygame.time.get_ticks()
            if self.game_over and (current_time - self.game_over_start_time) > self.game_over_duration:
                self.reset_game()

            if self.need_computer_move and not self.game_over and calculating_thread is None:
                def calculate_move():
                    nonlocal calculated_move
                    calculated_move = self.game.mcts_player.get_move()

                calculating_thread = threading.Thread(target=calculate_move, daemon=True)
                calculating_thread.start()

            if calculating_thread and not calculating_thread.is_alive():
                if calculated_move is not None:
                    self.game.make_silent_move(calculated_move)
                    self.game.mcts_player.move_and_update(calculated_move)
                    self.update_game_state()
                    self.need_computer_move = False
                    self.update_allowed_click()
                    calculated_move = None
                calculating_thread = None

            self.draw()
            pygame.display.flip()
            clock.tick(30)

    def handle_event(self, event):
        if event.type == QUIT:
            self.running = False
            return

        if event.type == KEYDOWN:
            if event.key == K_f:
                self.toggle_fullscreen()
        
        if event.type == VIDEORESIZE:
            if not self.fullscreen:
                self.handle_resize()

        if event.type == MOUSEBUTTONDOWN:
            menu_button_rect = pygame.Rect(
                self.screen.get_width() - MENU_BUTTON_WIDTH - 10, 5, MENU_BUTTON_WIDTH, MENU_BUTTON_HEIGHT
            )
            if menu_button_rect.collidepoint(event.pos):
                self.return_to_menu()
                return

            if self.allowed_to_click:
                if self.game_over:
                    self.reset_game()
                else:
                    self.handle_click(event.pos)

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.windowed_size = self.screen.get_size()
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        self.handle_resize()

    def handle_click(self, pos):
        col = (pos[0] - self.field_x) // self.cell_size
        row = (pos[1] - self.field_y - PADDING) // self.cell_size
        if 0 <= row < Field.HEIGHT and 0 <= col < Field.WIDTH:
            if self.game.current_state.field[row][col] == Player.Type.NONE:
                self.game.make_silent_move(Field.Cell(row, col))
                if self.mcts_enabled:
                    self.game.mcts_player.move_and_update(Field.Cell(row, col))
                
                self.update_game_state()
                
                if self.mcts_enabled and not self.game_over:
                    self.allowed_to_click = False
                    self.need_computer_move = True
                              

    def update_game_state(self):
        state = self.game.current_state.check_game_state()
        current_player = self.game.current_state.who_moves
        self.status_msg = f"                    Current: {Player.Icon[current_player]}"
        self.update_allowed_click()
        
        if state == GameStates.CONTINUE:
            self.game_msg = "Game in progress"
            self.game_over = False
            self.win_line = None
        else:
            self.game_over = True
            if state == GameStates.CROSS_WON:
                self.game_msg = "Crosses Victory! Click to restart"
            elif state == GameStates.NAUGHT_WON:
                self.game_msg = "Noughts Victory! Click to restart"
            elif state == GameStates.TIE:
                self.game_msg = "Tie! Click to restart"
            
            self.win_line = self.find_win_line()
            self.game_over_start_time = pygame.time.get_ticks()

    def draw(self):
        self.screen.fill(COLOR_BG)
        menu_button_rect = self.draw_status_bar()
        self.draw_message_panel()
        self.draw_game_field()
        
        if self.game_over:
            self.draw_win_line()
            self.draw_game_over()
        
        return menu_button_rect

    def draw_status_bar(self):
        screen_width = self.screen.get_width()
        pygame.draw.rect(self.screen, COLOR_STATUS, (0, 0, screen_width, STATUS_HEIGHT))
        menu_button_rect = pygame.Rect(
            screen_width - MENU_BUTTON_WIDTH - 10, 
            5, 
            MENU_BUTTON_WIDTH, 
            MENU_BUTTON_HEIGHT
        )
        pygame.draw.rect(self.screen, COLOR_MENU_BUTTON, menu_button_rect, border_radius=5)
        
        font = pygame.font.SysFont('Arial', 24)
        menu_text = font.render("MENU", True, COLOR_TEXT)
        self.screen.blit(menu_text, (
            menu_button_rect.centerx - menu_text.get_width()//2,
            menu_button_rect.centery - menu_text.get_height()//2
        ))
        
        font = pygame.font.SysFont('Arial', 28, bold=True)
        text = font.render(self.status_msg, True, COLOR_TEXT)
        text_rect = text.get_rect(center=((screen_width - MENU_BUTTON_WIDTH)//2, STATUS_HEIGHT//2))
        self.screen.blit(text, text_rect)
        
        return menu_button_rect

    def draw_message_panel(self):
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
                x = self.field_x + col * self.cell_size
                y = self.field_y + row * self.cell_size + PADDING
                self.draw_cell(x, y, row, col)

       

    def draw_cell(self, x, y, row, col):
        if hasattr(self.game.current_state, 'last_move') and self.game.current_state.last_move.row != -1:
            last_row, last_col = self.game.current_state.last_move.row, self.game.current_state.last_move.col
            if row == last_row and col == last_col:
                highlight = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
                highlight.fill((255, 255, 100, 30))
                self.screen.blit(highlight, (x, y))
        
        pygame.draw.rect(self.screen, COLOR_GRID, (x, y, self.cell_size, self.cell_size), 3)
        
        cell = self.game.current_state.field[row][col]
        if cell == Player.Type.CROSS:
            
            pygame.draw.line(self.screen, COLOR_X_OUTLINE,
                            (x + 10, y + 10), (x + self.cell_size - 10, y + self.cell_size - 10), 8)
            pygame.draw.line(self.screen, COLOR_X_OUTLINE,
                            (x + self.cell_size - 10, y + 10), (x + 10, y + self.cell_size - 10), 8)
            
            pygame.draw.line(self.screen, COLOR_X_MAIN,
                            (x + 15, y + 15), (x + self.cell_size - 15, y + self.cell_size - 15), 6)
            pygame.draw.line(self.screen, COLOR_X_MAIN,
                            (x + self.cell_size - 15, y + 15), (x + 15, y + self.cell_size - 15), 6)
        
        elif cell == Player.Type.NAUGHT:
            pygame.draw.circle(self.screen, COLOR_O_OUTLINE,
                            (x + self.cell_size//2, y + self.cell_size//2),
                            self.cell_size//2 - 10, 8)
            
            pygame.draw.circle(self.screen, COLOR_O_MAIN,
                            (x + self.cell_size//2, y + self.cell_size//2),
                            self.cell_size//2 - 13, 6)

    def draw_win_line(self):
        if self.win_line:
            progress = min(1.0, (pygame.time.get_ticks() - self.game_over_start_time) / 800)
            start_row, start_col, end_row, end_col = self.win_line
            
            x1 = self.field_x + start_col * self.cell_size + self.cell_size//2
            y1 = self.field_y + start_row * self.cell_size + self.cell_size//2 + PADDING
            x2 = self.field_x + end_col * self.cell_size + self.cell_size//2
            y2 = self.field_y + end_row * self.cell_size + self.cell_size//2 + PADDING
            
            # Для диагональных линий корректируем координаты, чтобы линия проходила точно через центры
            if abs(start_row - end_row) == abs(start_col - end_col):
                if start_col < end_col:
                    x1 -= self.cell_size//4
                    x2 += self.cell_size//4
                else:
                    x1 += self.cell_size//4
                    x2 -= self.cell_size//4
                    
                if start_row < end_row:
                    y1 -= self.cell_size//4
                    y2 += self.cell_size//4
                else:
                    y1 += self.cell_size//4
                    y2 -= self.cell_size//4
            
            current_x = x1 + (x2 - x1) * progress
            current_y = y1 + (y2 - y1) * progress
            pygame.draw.line(self.screen, COLOR_WIN_LINE, (x1, y1), (current_x, current_y), 6)

    def draw_game_over(self):
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.screen.blit(overlay, (0, 0))
        
        font = pygame.font.SysFont('Arial', 48, bold=True)
        
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
        self.update_allowed_click()

    def find_win_line(self):
        field = self.game.current_state.field
        last_move = self.game.current_state.last_move
        
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

        if abs(end_r - start_r) + 1 >= Field.STREAK_TO_WIN or abs(end_c - start_c) + 1 >= Field.STREAK_TO_WIN:
            return (start_r, start_c, end_r, end_c)
        
        return None
    
    def return_to_menu(self):
        self.running = False
        pygame.quit()
        
        current_m = Field.WIDTH
        current_n = Field.HEIGHT
        current_k = Field.STREAK_TO_WIN
        current_ai = False
        
        # Запускаем меню
        menu = StartMenu()
        m, n, k, ai_enabled, mcts_enabled, player_type, is_fullscreen, screen_size = menu.run()
        
        if m > 0 and n > 0 and k > 0:
            Field.set_dimensions(m, n, k)
            mcts_player = MCTSPlayer(
                puct_constant=5,
                playout_number=MCTS_ITERATIONS,
            )
            game = Game(mcts_player)
            interface = PyGameInterface(mcts_enabled, player_type, game, is_fullscreen, screen_size)
            interface.run()
