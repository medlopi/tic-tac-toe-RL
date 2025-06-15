import pygame
from pygame.locals import *
from app.player import Player

class StartMenu:
    def __init__(self, m=None, n=None, k=None, ai=None, mcts=None, player_symbol=None, is_fullscreen_start=False, initial_size=None):
        self.base_width = 800
        self.base_height = 600
        self.fullscreen = is_fullscreen_start
        self.windowed_size = initial_size if initial_size else (self.base_width, self.base_height)
        flags = pygame.FULLSCREEN if self.fullscreen else pygame.RESIZABLE
        size = (0, 0) if self.fullscreen else self.windowed_size
        self.screen = pygame.display.set_mode(size, flags)
        pygame.display.set_caption("MxNxK Game - Settings")
        self.m = str(m) if m is not None else "3"
        self.n = str(n) if n is not None else "3"
        self.k = str(k) if k is not None else "3"
        self.ai_enabled = ai if ai is not None else False
        self.mcts_enabled = mcts if mcts is not None else False
        self.friend_enabled = not (self.ai_enabled or self.mcts_enabled)
        self.mcts_vs_dqn_mode = False
        self.mcts_vs_dqn_choice = None  # None, 'mcts_x', 'dqn_x'

        self.player_symbol = player_symbol if player_symbol is not None else Player.Type.CROSS
        self.active_field = None
        self.font = pygame.font.SysFont('Arial', 36)
        self.title_font = pygame.font.SysFont('Arial', 48, bold=True)
        self.small_font = pygame.font.SysFont('Arial', 28)
        self.COLOR_BG = (50, 50, 70)
        self.COLOR_INPUT = (80, 80, 100)
        self.COLOR_ACTIVE = (120, 120, 150)
        self.COLOR_TEXT = (240, 240, 240)
        self.COLOR_BUTTON = (90, 120, 200)
        self.COLOR_MODE_ON = (100, 200, 100)
        self.COLOR_MODE_OFF = (200, 100, 100)
        self.COLOR_SYMBOL_ON = (130, 100, 250)
        self.COLOR_SYMBOL_OFF = (100, 100, 100)
        self.running = True
        self.cursor_visible = False
        self.cursor_timer = 0
        self.cursor_blink_interval = 500
        self.error_message = ""
        self.error_timer = 0
        self.error_duration = 1000
        self.error_field = None

    def draw(self):
        self.screen.fill(self.COLOR_BG)
        screen_width, screen_height = self.screen.get_size()
        
        content_width = 600
        content_height = 550
        offset_x = (screen_width - content_width) // 2
        offset_y = (screen_height - content_height) // 2
        
        title = self.title_font.render("MxNxK Settings", True, self.COLOR_TEXT)
        self.screen.blit(title, (offset_x + (content_width - title.get_width())//2, offset_y + 20))
        
        self.draw_input("Width (M):", self.m, offset_y + 100, 0, offset_x)
        self.draw_input("Height (N):", self.n, offset_y + 170, 1, offset_x)
        self.draw_input("Win Streak (K):", self.k, offset_y + 240, 2, offset_x)
        
        mode_label = self.small_font.render("Play with:", True, self.COLOR_TEXT)
        self.screen.blit(mode_label, (offset_x + (content_width - mode_label.get_width())//2, offset_y + 280))
        
        friend_rect = pygame.Rect(offset_x + 30, offset_y + 310, 180, 50)
        ai_rect = pygame.Rect(offset_x + 220, offset_y + 310, 170, 50)
        mcts_rect = pygame.Rect(offset_x + 400, offset_y + 310, 170, 50)
        mcts_vs_dqn_rect = pygame.Rect(offset_x + 150, offset_y + 250, 300, 50)

        friend_color = self.COLOR_MODE_ON if self.friend_enabled else self.COLOR_MODE_OFF
        ai_color = self.COLOR_MODE_ON if self.ai_enabled else self.COLOR_MODE_OFF
        mcts_color = self.COLOR_MODE_ON if self.mcts_enabled else self.COLOR_MODE_OFF
        mcts_vs_dqn_color = self.COLOR_MODE_ON if self.mcts_vs_dqn_mode else self.COLOR_MODE_OFF

        pygame.draw.rect(self.screen, friend_color, friend_rect, border_radius=10)
        pygame.draw.rect(self.screen, ai_color, ai_rect, border_radius=10)
        pygame.draw.rect(self.screen, mcts_color, mcts_rect, border_radius=10)
        pygame.draw.rect(self.screen, mcts_vs_dqn_color, mcts_vs_dqn_rect, border_radius=10)
        
        friend_text = self.font.render("Friend", True, self.COLOR_TEXT)
        ai_text = self.font.render("AI", True, self.COLOR_TEXT)
        mcts_text = self.font.render("MCTS", True, self.COLOR_TEXT)
        mcts_vs_dqn_text = self.font.render("MCTS vs DQN", True, self.COLOR_TEXT)

        self.screen.blit(friend_text, (friend_rect.centerx - friend_text.get_width()//2, friend_rect.centery - friend_text.get_height()//2))
        self.screen.blit(ai_text, (ai_rect.centerx - ai_text.get_width()//2, ai_rect.centery - ai_text.get_height()//2))
        self.screen.blit(mcts_text, (mcts_rect.centerx - mcts_text.get_width()//2, mcts_rect.centery - mcts_text.get_height()//2))
        self.screen.blit(mcts_vs_dqn_text, (
            mcts_vs_dqn_rect.centerx - mcts_vs_dqn_text.get_width() // 2,
            mcts_vs_dqn_rect.centery - mcts_vs_dqn_text.get_height() // 2
        ))

        if self.ai_enabled or self.mcts_enabled:
            symbol_label = self.small_font.render("Choose your side:", True, self.COLOR_TEXT)
            self.screen.blit(symbol_label, (offset_x + (content_width - symbol_label.get_width())//2, offset_y + 370))
            
            button_spacing = 20
            total_width = 190 * 2 + button_spacing  
            x_rect = pygame.Rect(offset_x + (content_width - total_width) // 2, offset_y + 400, 190, 50)
            o_rect = pygame.Rect(offset_x + (content_width - total_width) // 2 + 190 + button_spacing, offset_y + 400, 190, 50)
            x_color = self.COLOR_SYMBOL_ON if self.player_symbol == Player.Type.CROSS else self.COLOR_SYMBOL_OFF
            o_color = self.COLOR_SYMBOL_ON if self.player_symbol == Player.Type.NAUGHT else self.COLOR_SYMBOL_OFF
            pygame.draw.rect(self.screen, x_color, x_rect, border_radius=10)
            pygame.draw.rect(self.screen, o_color, o_rect, border_radius=10)
            x_text = self.font.render("Play as X", True, self.COLOR_TEXT)
            o_text = self.font.render("Play as O", True, self.COLOR_TEXT)
            self.screen.blit(x_text, (x_rect.centerx - x_text.get_width()//2, x_rect.centery - x_text.get_height()//2))
            self.screen.blit(o_text, (o_rect.centerx - o_text.get_width()//2, o_rect.centery - o_text.get_height()//2))
        
        if self.mcts_vs_dqn_mode:
            # Показываем две кнопки выбора
            btn1_rect = pygame.Rect(offset_x + 150, offset_y + 400, 190, 50)
            btn2_rect = pygame.Rect(offset_x + 330, offset_y + 400, 190, 50)
            btn1_color = self.COLOR_SYMBOL_ON if self.mcts_vs_dqn_choice == 'mcts_x' else self.COLOR_SYMBOL_OFF
            btn2_color = self.COLOR_SYMBOL_ON if self.mcts_vs_dqn_choice == 'dqn_x' else self.COLOR_SYMBOL_OFF
            pygame.draw.rect(self.screen, btn1_color, btn1_rect, border_radius=10)
            pygame.draw.rect(self.screen, btn2_color, btn2_rect, border_radius=10)
            btn1_text = self.font.render("MCTS as X", True, self.COLOR_TEXT)
            btn2_text = self.font.render("DQN as X", True, self.COLOR_TEXT)
            self.screen.blit(btn1_text, (btn1_rect.centerx - btn1_text.get_width()//2, btn1_rect.centery - btn1_text.get_height()//2))
            self.screen.blit(btn2_text, (btn2_rect.centerx - btn2_text.get_width()//2, btn2_rect.centery - btn2_text.get_height()//2))
        
        
        start_rect = pygame.Rect(offset_x + 150, offset_y + 470, 300, 60)
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
        
        text_surface = self.font.render(value, True, self.COLOR_TEXT)
        text_width = min(text_surface.get_width(), field_rect.width - 20)
        text_rect = pygame.Rect(field_rect.x + 10, field_rect.centery - text_surface.get_height() // 2, 
                            text_width, text_surface.get_height())
        
        if text_surface.get_width() > field_rect.width - 20:
            cropped_surface = pygame.Surface((field_rect.width - 20, text_surface.get_height()))
            cropped_surface.blit(text_surface, (0, 0), 
                                (text_surface.get_width() - (field_rect.width - 20), 0, 
                                field_rect.width - 20, text_surface.get_height()))
            self.screen.blit(cropped_surface, text_rect)
        else:
            self.screen.blit(text_surface, text_rect)
        
        if self.active_field == index and self.cursor_visible:
            cursor_x = text_rect.right + 2 if text_rect.width == field_rect.width - 20 else text_rect.right + 2
            pygame.draw.line(self.screen, self.COLOR_TEXT, 
                            (cursor_x, text_rect.top + 2), 
                            (cursor_x, text_rect.bottom - 2), 2)

        if (hasattr(self, 'error_field') and self.error_message and self.error_field == index and pygame.time.get_ticks() - self.error_timer < self.error_duration):
            error_surface = self.small_font.render(self.error_message, True, (255, 100, 100))
            self.screen.blit(error_surface, (field_rect.right + 10, field_rect.centery - error_surface.get_height() // 2))

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.windowed_size = self.screen.get_size()
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            current_time = pygame.time.get_ticks()
            if self.active_field is not None:
                if current_time - self.cursor_timer > self.cursor_blink_interval:
                    self.cursor_visible = not self.cursor_visible
                    self.cursor_timer = current_time
            else:
                self.cursor_visible = False
            
            if self.error_message and current_time - self.error_timer > self.error_duration:
                self.error_message = ""
            
            for event in pygame.event.get():
                self.handle_event(event)
            
            self.draw()
            clock.tick(30)
        
        return (int(self.m), int(self.n), int(self.k), self.ai_enabled, self.mcts_enabled, self.mcts_vs_dqn_mode, self.mcts_vs_dqn_choice, self.player_symbol, self.fullscreen, self.screen.get_size())
    
    def validate_k(self, show_message=True):
        """Если k > max(m, n), то уменьшаем k"""
        try:
            if not self.m or not self.n or not self.k:
                return False
                
            m = int(self.m)
            n = int(self.n) 
            k = int(self.k)
            
            max_dimension = max(m, n)
            if k > max_dimension:
                if show_message:
                    self.error_message = f"K set to {max_dimension} (max field size)"
                    self.error_timer = pygame.time.get_ticks()
                    self.error_field = 2
                self.k = str(max_dimension)
                return True
        except ValueError:
            pass
        return False
    
    def handle_event(self, event):
        if event.type == VIDEORESIZE:
            if not self.fullscreen:
                self.windowed_size = (event.w, event.h)
                self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        if event.type == QUIT:
            self.running = False
            self.m = self.n = self.k = "0"
        elif event.type == KEYDOWN:
            if event.key == K_f:
                self.toggle_fullscreen()
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
                    if self.active_field in [0, 1]:
                        self.validate_k(show_message=False)
                    elif self.active_field == 2:
                        self.validate_k(show_message=True)
                elif event.unicode.isdigit():
                    current = [self.m, self.n, self.k]
                    if len(current[self.active_field]) < 2:
                        current[self.active_field] = current[self.active_field] + event.unicode
                        self.m, self.n, self.k = current
                        if self.active_field in [0, 1]:
                            self.validate_k(show_message=False)
                        elif self.active_field == 2:
                            self.validate_k(show_message=True)
        elif event.type == MOUSEBUTTONDOWN:
            if event.button != 1:
                return
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
                old_active = self.active_field
                self.active_field = None
                if old_active is not None:
                    self.validate_k(show_message=True)
            
            if (offset_x + 30 <= x <= offset_x + 210 and 
                offset_y + 310 <= y <= offset_y + 360):
                self.friend_enabled = True
                self.ai_enabled = False
                self.mcts_enabled = False
                self.mcts_vs_dqn_mode = False

            if (offset_x + 220 <= x <= offset_x + 390 and 
                offset_y + 310 <= y <= offset_y + 360):
                self.ai_enabled = True
                self.friend_enabled = False
                self.mcts_enabled = False
                self.mcts_vs_dqn_mode = False

            if (offset_x + 400 <= x <= offset_x + 570 and 
                offset_y + 310 <= y <= offset_y + 360):
                self.mcts_enabled = True
                self.friend_enabled = False
                self.ai_enabled = False
                self.mcts_vs_dqn_mode = False
            if (offset_x + 150 <= x <= offset_x + 450 and offset_y + 250 <= y <= offset_y + 300):
                self.mcts_vs_dqn_mode = True
                self.friend_enabled = False
                self.ai_enabled = False
                self.mcts_enabled = False
            
            if self.ai_enabled or self.mcts_enabled:
                if (offset_x + 150 <= x <= offset_x + 270 and 
                    offset_y + 400 <= y <= offset_y + 450):
                    self.player_symbol = Player.Type.CROSS
                if (offset_x + 330 <= x <= offset_x + 450 and 
                    offset_y + 400 <= y <= offset_y + 450):
                    self.player_symbol = Player.Type.NAUGHT

            if self.mcts_vs_dqn_mode:
                # "MCTS as X"
                if (offset_x + 150 <= x <= offset_x + 340 and offset_y + 400 <= y <= offset_y + 450):
                    self.mcts_vs_dqn_choice = 'mcts_x'
                # "DQN as X"
                if (offset_x + 330 <= x <= offset_x + 520 and offset_y + 400 <= y <= offset_y + 450):
                    self.mcts_vs_dqn_choice = 'dqn_x'
                    
            if (offset_x + 150 <= x <= offset_x + 450 and 
                offset_y + 470 <= y <= offset_y + 530):
                try:
                    if not self.m or not self.n or not self.k:
                        return
                    m = int(self.m)
                    n = int(self.n)
                    k = int(self.k)
                    if m > 0 and n > 0 and k > 0:
                        self.validate_k(show_message=True)
                        self.running = False
                except ValueError:
                    pass