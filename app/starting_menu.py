import pygame
from pygame.locals import *

class StartMenu:
    def __init__(self):
        pygame.init()
        self.base_width = 800
        self.base_height = 600
        self.screen = pygame.display.set_mode((self.base_width, self.base_height), pygame.RESIZABLE)
        pygame.display.set_caption("MxNxK Game - Settings")
        self.m = "10" # Параметры по умолчанию в полях меню
        self.n = "10"
        self.k = "5"
        self.ai_enabled = False
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
        self.running = True
        self.fullscreen = False

    def draw(self):
        self.screen.fill(self.COLOR_BG)
        screen_width, screen_height = self.screen.get_size()
        
        # Центрирование
        content_width = 600
        content_height = 500
        offset_x = (screen_width - content_width) // 2
        offset_y = (screen_height - content_height) // 2
        # Рисуем кнопки
        title = self.title_font.render("MxNxK Settings", True, self.COLOR_TEXT)
        self.screen.blit(title, (offset_x + (content_width - title.get_width())//2, offset_y + 30))
        self.draw_input("Width (M):", self.m, offset_y + 120, 0, offset_x)
        self.draw_input("Height (N):", self.n, offset_y + 200, 1, offset_x)
        self.draw_input("Win Streak (K):", self.k, offset_y + 280, 2, offset_x)
        
        ai_rect = pygame.Rect(offset_x + 150, offset_y + 360, 300, 50)
        ai_color = self.COLOR_AI_ON if self.ai_enabled else self.COLOR_AI_OFF
        pygame.draw.rect(self.screen, ai_color, ai_rect, border_radius=10)
        ai_text = self.font.render("AI: " + ("ON" if self.ai_enabled else "OFF"), True, self.COLOR_TEXT)
        self.screen.blit(ai_text, (ai_rect.centerx - ai_text.get_width()//2, ai_rect.centery - ai_text.get_height()//2))
        
        start_rect = pygame.Rect(offset_x + 150, offset_y + 440, 300, 60)
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
        
        return int(self.m), int(self.n), int(self.k), self.ai_enabled

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
            offset_y = (screen_height - 500) // 2
            for i in range(3):
                field_y = offset_y + 120 + i*80
                if (offset_x + 300 <= x <= offset_x + 500 and 
                    field_y <= y <= field_y + 40):
                    self.active_field = i
                    break
            else:
                self.active_field = None
            
            if (offset_x + 150 <= x <= offset_x + 450 and 
                offset_y + 360 <= y <= offset_y + 410):
                self.ai_enabled = not self.ai_enabled
            
            # Проверка кнопки Start (после нажатия на неё начинается игра)
            if (offset_x + 150 <= x <= offset_x + 450 and 
                offset_y + 440 <= y <= offset_y + 500):
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