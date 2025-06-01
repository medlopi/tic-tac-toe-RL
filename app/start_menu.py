import pygame
from pygame.locals import *
from app.player import Player

class StartMenu:
    def __init__(self, m=None, n=None, k=None, ai=None, mcts=None, player_symbol=None):
        pygame.init()
        self.base_width = 800
        self.base_height = 600
        self.screen = pygame.display.set_mode((self.base_width, self.base_height), pygame.RESIZABLE)
        pygame.display.set_caption("MxNxK Game - Settings")
        self.m = str(m) if m is not None else "3"
        self.n = str(n) if n is not None else "3"
        self.k = str(k) if k is not None else "3"
        self.ai_enabled = ai if ai is not None else False
        self.mcts_enabled = mcts if mcts is not None else False
        self.player_symbol = player_symbol if player_symbol is not None else Player.Type.CROSS
        self.active_field = None
        self.font = pygame.font.SysFont('Arial', 36)
        self.title_font = pygame.font.SysFont('Arial', 48, bold=True)
        self.COLOR_BG = (50, 50, 70)
        self.COLOR_INPUT = (80, 80, 100)
        self.COLOR_ACTIVE = (120, 120, 150)
        self.COLOR_TEXT = (240, 240, 240)
        self.COLOR_BUTTON = (90, 120, 200)
        self.COLOR_AI_ON = (100, 200, 100)
        self.COLOR_AI_OFF = (200, 100, 100)
        self.COLOR_MCTS_ON = (100, 200, 200)
        self.COLOR_MCTS_OFF = (200, 100, 150)
        self.COLOR_SYMBOL_ON = (130, 100, 250)
        self.COLOR_SYMBOL_OFF = (100, 100, 100)
        self.running = True
        self.fullscreen = False

    def draw(self):
        self.screen.fill(self.COLOR_BG)
        screen_width, screen_height = self.screen.get_size()
        
        # Центрирование
        content_width = 600
        content_height = 550
        offset_x = (screen_width - content_width) // 2
        offset_y = (screen_height - content_height) // 2
        
        # Рисуем кнопки
        title = self.title_font.render("MxNxK Settings", True, self.COLOR_TEXT)
        self.screen.blit(title, (offset_x + (content_width - title.get_width())//2, offset_y + 20))
        
        self.draw_input("Width (M):", self.m, offset_y + 100, 0, offset_x)
        self.draw_input("Height (N):", self.n, offset_y + 170, 1, offset_x)
        self.draw_input("Win Streak (K):", self.k, offset_y + 240, 2, offset_x)
        
        # Кнопки AI и MCTS
        ai_rect = pygame.Rect(offset_x + 50, offset_y + 310, 240, 50)
        ai_color = self.COLOR_AI_ON if self.ai_enabled else self.COLOR_AI_OFF
        pygame.draw.rect(self.screen, ai_color, ai_rect, border_radius=10)
        ai_text = self.font.render("Play with AI", True, self.COLOR_TEXT)
        self.screen.blit(ai_text, (ai_rect.centerx - ai_text.get_width()//2, ai_rect.centery - ai_text.get_height()//2))
        
        mcts_rect = pygame.Rect(offset_x + 310, offset_y + 310, 240, 50)
        mcts_color = self.COLOR_MCTS_ON if self.mcts_enabled else self.COLOR_MCTS_OFF
        pygame.draw.rect(self.screen, mcts_color, mcts_rect, border_radius=10)
        mcts_text = self.font.render("Play with MCTS", True, self.COLOR_TEXT)
        self.screen.blit(mcts_text, (mcts_rect.centerx - mcts_text.get_width()//2, mcts_rect.centery - mcts_text.get_height()//2))
        
        # Кнопки выбора символа (появляются только если выбран AI или MCTS)
        if self.ai_enabled or self.mcts_enabled:
            x_rect = pygame.Rect(offset_x + 150, offset_y + 380, 120, 50)
            o_rect = pygame.Rect(offset_x + 330, offset_y + 380, 120, 50)
            x_color = self.COLOR_SYMBOL_ON if self.player_symbol == Player.Type.CROSS else self.COLOR_SYMBOL_OFF
            o_color = self.COLOR_SYMBOL_ON if self.player_symbol == Player.Type.NAUGHT else self.COLOR_SYMBOL_OFF
            pygame.draw.rect(self.screen, x_color, x_rect, border_radius=10)
            pygame.draw.rect(self.screen, o_color, o_rect, border_radius=10)
            x_text = self.font.render("Play as X", True, self.COLOR_TEXT)
            o_text = self.font.render("Play as O", True, self.COLOR_TEXT)
            self.screen.blit(x_text, (x_rect.centerx - x_text.get_width()//2, x_rect.centery - x_text.get_height()//2))
            self.screen.blit(o_text, (o_rect.centerx - o_text.get_width()//2, o_rect.centery - o_text.get_height()//2))
        
        # Кнопка Start
        start_rect = pygame.Rect(offset_x + 150, offset_y + 450, 300, 60)
        pygame.draw.rect(self.screen, self.COLOR_BUTTON, start_rect, border_radius=10)
        start_text = self.title_font.render("START", True, self.COLOR_TEXT)
        self.screen.blit(start_text, (start_rect.centerx - start_text.get_width() // 2, start_rect.centery - start_text.get_height()//2))
        
        pygame.display.flip()

    def draw_input(self, label, value, y, index, offset_x):
        input_x = offset_x + 50
        input_y = y
        lbl = self.font.render(label, True, self.COLOR_TEXT)
        self.screen.blit(lbl, (input_x, input_y))
        
        color = self.COLOR_ACTIVE if self.active_field == index else self.COLOR_INPUT
        field_rect = pygame.Rect(input_x + 300, input_y, 200, 40)
        pygame.draw.rect(self.screen, color, field_rect, border_radius=5)
        
        text = self.font.render(value, True, self.COLOR_TEXT)
        self.screen.blit(text, (field_rect.x + 10, field_rect.centery - text.get_height() // 2))

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)
            
            self.draw()
            clock.tick(30)
        
        return int(self.m), int(self.n), int(self.k), self.ai_enabled, self.mcts_enabled, self.player_symbol

    def handle_event(self, event):
        if event.type == QUIT:
            self.running = False
            self.m = self.n = self.k = "0"
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                self.running = False
                self.m = self.n = self.k = "0"
            if self.active_field is not None:
                if event.key == K_RETURN:
                    self.active_field = None
                elif event.key == K_BACKSPACE:
                    current = [self.m, self.n, self.k]
                    current[self.active_field] = current[self.active_field][:-1]
                    self.m, self.n, self.k = current
                elif event.unicode.isdigit():
                    current = [self.m, self.n, self.k]
                    if len(current[self.active_field]) < 3:
                        current[self.active_field] += event.unicode
                        self.m, self.n, self.k = current
        elif event.type == MOUSEBUTTONDOWN:
            x, y = event.pos
            screen_width, screen_height = self.screen.get_size()
            offset_x = (screen_width - 600) // 2
            offset_y = (screen_height - 550) // 2
            
            # Проверка полей ввода
            for i in range(3):
                field_y = offset_y + 100 + i*70
                if (offset_x + 300 <= x <= offset_x + 500 and 
                    field_y <= y <= field_y + 40):
                    self.active_field = i
                    break
            else:
                self.active_field = None
            
            # Проверка кнопок AI и MCTS
            if (offset_x + 50 <= x <= offset_x + 290 and 
                offset_y + 310 <= y <= offset_y + 360):
                self.ai_enabled = not self.ai_enabled
                if self.ai_enabled:
                    self.mcts_enabled = False

            if (offset_x + 310 <= x <= offset_x + 550 and 
                offset_y + 310 <= y <= offset_y + 360):
                self.mcts_enabled = not self.mcts_enabled
                if self.mcts_enabled:
                    self.ai_enabled = False
            
            # Проверка кнопок выбора символа (только если AI или MCTS включены)
            if self.ai_enabled or self.mcts_enabled:
                if (offset_x + 150 <= x <= offset_x + 270 and 
                    offset_y + 380 <= y <= offset_y + 430):
                    self.player_symbol = Player.Type.CROSS
                if (offset_x + 330 <= x <= offset_x + 450 and 
                    offset_y + 380 <= y <= offset_y + 430):
                    self.player_symbol = Player.Type.NAUGHT
            
            # Проверка кнопки Start
            if (offset_x + 150 <= x <= offset_x + 450 and 
                offset_y + 450 <= y <= offset_y + 510):
                try:
                    m = int(self.m)
                    n = int(self.n)
                    k = int(self.k)
                    if m > 0 and n > 0 and k > 0:
                        self.running = False
                except:
                    pass
        elif event.type == VIDEORESIZE:
            if not self.fullscreen:
                self.base_width, self.base_height = event.w, event.h
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)