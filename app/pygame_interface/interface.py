import pygame
import threading
from pygame.locals import *
from app.basic_game_core.game import Game
from app.basic_game_core.field import Field, GameStates
from app.basic_game_core.player import Player

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
    def __init__(
        self,
        dqn_player,
        mcts_enabled: bool,
        player_type: Player.Type,
        game=None,
        fullscreen_start=False,
        initial_size=None,
        mcts_vs_dqn=False,
        mcts_vs_dqn_choice="mcts_x",
    ):
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
        self.comp_player = dqn_player
        self.mcts_vs_dqn = mcts_vs_dqn
        self.player_type = player_type
        self.mcts_vs_dqn_choice = mcts_vs_dqn_choice
        self.need_computer_move = (
            True if (mcts_enabled and player_type == Player.Type.NAUGHT) else False
        )
        self.dqn_vs_mcts_thread = None
        self.dqn_vs_mcts_move = None

        self.allowed_to_click = False
        self.update_allowed_click()
        self.zoom = 1.0
        self.min_zoom, self.max_zoom = (
            0.2,
            5.0,
        )  # Ограничения зума и тп: теперь поле можно перетаскивать и приближать
        self.view_offset_x = 0
        self.view_offset_y = 0
        self.is_panning = False
        self.pan_start_pos = (0, 0)
        self.base_cell_size = self.calculate_base_cell_size()
        self.init_window()
        self.center_view()
        self.update_game_state()

    def calculate_base_cell_size(self):
        return 780 // max(Field.HEIGHT, Field.WIDTH, 7)

    @property
    def current_cell_size(self):
        """Для приближения поля"""
        return self.base_cell_size * self.zoom

    def init_window(self):
        flags = pygame.FULLSCREEN if self.fullscreen else pygame.RESIZABLE
        size = (
            (0, 0)
            if self.fullscreen
            else self.initial_size if self.initial_size else (800, 600)
        )

        self.screen = pygame.display.set_mode(size, flags)
        pygame.display.set_caption(
            "MxNxKxD Game (Scroll to Zoom, Right-Click+Drag to Pan)"
        )
        self.handle_resize()

    def update_allowed_click(self):
        if self.mcts_vs_dqn:
            self.allowed_to_click = False
            return

        if self.mcts_enabled:
            self.allowed_to_click = (
                self.game.current_state.who_moves == self.player_type
            )
            self.need_computer_move = (
                self.game.current_state.who_moves != self.player_type
            )
        else:
            self.allowed_to_click = True

    def handle_resize(self):
        screen_width, screen_height = self.screen.get_size()
        self.field_width = screen_width - PADDING * 2
        self.field_height = screen_height - (
            STATUS_HEIGHT + MESSAGE_HEIGHT + PADDING * 2
        )
        self.field_x = PADDING
        self.field_y = STATUS_HEIGHT + MESSAGE_HEIGHT + PADDING
        self.field_surface_rect = pygame.Rect(
            self.field_x, self.field_y, self.field_width, self.field_height
        )
        self.field_surface = self.screen.subsurface(self.field_surface_rect)
        self.center_view()

    def run(self):
        print("RUNNING")
        clock = pygame.time.Clock()
        calculated_move = None
        calculating_thread = None

        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)

            if self.mcts_vs_dqn:
                current_time = pygame.time.get_ticks()
                if (
                    self.game_over
                    and (current_time - self.game_over_start_time)
                    > self.game_over_duration
                ):
                    self.reset_game()
                    self.comp_player.reset_player()

                who_moves = self.game.current_state.who_moves

                if not self.game_over and calculating_thread is None:

                    def calculate_move():
                        nonlocal calculated_move
                        if who_moves == Player.Type.CROSS:
                            if self.mcts_vs_dqn_choice == "mcts_x":
                                calculated_move = self.game.mcts_player.get_move()
                            else:
                                calculated_move = self.comp_player.get_move()

                        elif who_moves == Player.Type.NAUGHT:
                            if self.mcts_vs_dqn_choice == "dqn_x":
                                calculated_move = self.game.mcts_player.get_move()
                            else:
                                calculated_move = self.comp_player.get_move()

                    calculating_thread = threading.Thread(
                        target=calculate_move, daemon=True
                    )
                    calculating_thread.start()

                if calculating_thread and not calculating_thread.is_alive():
                    if calculated_move is not None:
                        self.game.make_silent_move(calculated_move)

                        prev_player = (
                            Player.Type.NAUGHT
                            if self.game.current_state.who_moves == Player.Type.CROSS
                            else Player.Type.CROSS
                        )
                        if prev_player == Player.Type.CROSS:
                            if self.mcts_vs_dqn_choice == "mcts_x":
                                self.game.mcts_player.move_and_update(calculated_move)
                            else:
                                self.comp_player.move_and_update(calculated_move)
                        elif prev_player == Player.Type.NAUGHT:
                            if self.mcts_vs_dqn_choice == "mcts_x":
                                self.comp_player.move_and_update(calculated_move)
                            else:
                                self.game.mcts_player.move_and_update(calculated_move)
                        self.update_game_state()
                        calculated_move = None
                    calculating_thread = None

            else:
                if (
                    self.need_computer_move
                    and not self.game_over
                    and calculating_thread is None
                ):

                    def calculate_move():
                        nonlocal calculated_move
                        calculated_move = self.game.mcts_player.get_move()

                    calculating_thread = threading.Thread(
                        target=calculate_move, daemon=True
                    )
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

            current_time = pygame.time.get_ticks()
            if (
                self.game_over
                and (current_time - self.game_over_start_time) > self.game_over_duration
            ):
                self.reset_game()
                self.comp_player.reset_player()

            self.draw()
            pygame.display.flip()
            clock.tick(200)
        return self.fullscreen

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
            if self.field_surface_rect.collidepoint(event.pos):
                if event.button == 4:
                    self.zoom_at_point(event.pos, 1.15)
                elif event.button == 5:
                    self.zoom_at_point(event.pos, 1 / 1.15)
                elif event.button == 3:
                    self.is_panning = True
                    self.pan_start_pos = event.pos
        if event.type == MOUSEBUTTONUP:
            if event.button == 3:
                self.is_panning = False
        if event.type == MOUSEMOTION:
            if self.is_panning:
                dx = event.pos[0] - self.pan_start_pos[0]
                dy = event.pos[1] - self.pan_start_pos[1]
                self.view_offset_x += dx
                self.view_offset_y += dy
                self.pan_start_pos = event.pos
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            menu_button_rect = pygame.Rect(
                self.screen.get_width() - MENU_BUTTON_WIDTH - 10,
                5,
                MENU_BUTTON_WIDTH,
                MENU_BUTTON_HEIGHT,
            )
            if menu_button_rect.collidepoint(event.pos):
                self.return_to_menu()
                return

            if self.game_over:
                self.reset_game()
                if self.comp_player is not None:
                    self.comp_player.reset_player()
            elif self.allowed_to_click:
                self.handle_click(event.pos)

    def zoom_at_point(self, mouse_pos, zoom_factor):
        mx = mouse_pos[0] - self.field_x
        my = mouse_pos[1] - self.field_y

        world_x_before_zoom = (mx - self.view_offset_x) / self.zoom
        world_y_before_zoom = (my - self.view_offset_y) / self.zoom

        new_zoom = self.zoom * zoom_factor
        self.zoom = max(self.min_zoom, min(self.max_zoom, new_zoom))

        self.view_offset_x = mx - world_x_before_zoom * self.zoom
        self.view_offset_y = my - world_y_before_zoom * self.zoom

    def center_view(self):
        """Центрирование поля"""
        viewport_width = self.field_width
        viewport_height = self.field_height

        board_pixel_width = Field.WIDTH * self.current_cell_size
        board_pixel_height = Field.HEIGHT * self.current_cell_size

        self.view_offset_x = (viewport_width - board_pixel_width) / 2
        self.view_offset_y = (viewport_height - board_pixel_height) / 2

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.windowed_size = self.screen.get_size()
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        self.handle_resize()
        self.screen_size = self.screen.get_size()

    def handle_click(self, pos):
        if not self.field_surface_rect.collidepoint(pos):
            return

        relative_x = pos[0] - self.field_x
        relative_y = pos[1] - self.field_y

        col = int((relative_x - self.view_offset_x) / self.current_cell_size)
        row = int((relative_y - self.view_offset_y) / self.current_cell_size)

        if 0 <= row < Field.HEIGHT and 0 <= col < Field.WIDTH:
            if self.game.current_state.field[row][col] == -1:
                move = Field.Cell(row, col, self.game.current_state.who_moves.value)
                self.game.make_silent_move(move)
                if self.mcts_enabled:
                    self.game.mcts_player.move_and_update(move)

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
        self.draw_status_bar()
        self.draw_message_panel()
        self.draw_game_field()

        if self.game_over:
            self.draw_win_line()
            self.draw_game_over()

    def draw_status_bar(self):
        screen_width = self.screen.get_width()
        pygame.draw.rect(self.screen, COLOR_STATUS, (0, 0, screen_width, STATUS_HEIGHT))
        menu_button_rect = pygame.Rect(
            screen_width - MENU_BUTTON_WIDTH - 10,
            5,
            MENU_BUTTON_WIDTH,
            MENU_BUTTON_HEIGHT,
        )
        pygame.draw.rect(
            self.screen, COLOR_MENU_BUTTON, menu_button_rect, border_radius=5
        )
        font = pygame.font.SysFont("Arial", 24)
        menu_text = font.render("MENU", True, COLOR_TEXT)
        self.screen.blit(
            menu_text,
            (
                menu_button_rect.centerx - menu_text.get_width() // 2,
                menu_button_rect.centery - menu_text.get_height() // 2,
            ),
        )
        font = pygame.font.SysFont("Arial", 28, bold=True)
        text = font.render(self.status_msg, True, COLOR_TEXT)
        text_rect = text.get_rect(
            center=((screen_width - MENU_BUTTON_WIDTH) // 2, STATUS_HEIGHT // 2)
        )
        self.screen.blit(text, text_rect)
        return menu_button_rect

    def draw_message_panel(self):
        screen_width = self.screen.get_width()
        pygame.draw.rect(
            self.screen, COLOR_MESSAGE, (0, STATUS_HEIGHT, screen_width, MESSAGE_HEIGHT)
        )
        font = pygame.font.SysFont("Arial", 24)
        text = font.render(self.game_msg, True, COLOR_TEXT)
        text_rect = text.get_rect(
            center=(screen_width // 2, STATUS_HEIGHT + MESSAGE_HEIGHT // 2)
        )
        self.screen.blit(text, text_rect)

    def draw_game_field(self):
        self.field_surface.fill(COLOR_FIELD_BG)

        cell_size = self.current_cell_size
        start_col = max(0, int(-self.view_offset_x / cell_size))
        end_col = min(
            Field.WIDTH, int((-self.view_offset_x + self.field_width) / cell_size) + 1
        )
        start_row = max(0, int(-self.view_offset_y / cell_size))
        end_row = min(
            Field.HEIGHT, int((-self.view_offset_y + self.field_height) / cell_size) + 1
        )

        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                x = self.view_offset_x + col * cell_size
                y = self.view_offset_y + row * cell_size
                self.draw_cell(self.field_surface, x, y, row, col)

    def draw_cell(self, surface, x, y, row, col):
        cell_size = self.current_cell_size
        cell_rect = pygame.Rect(x, y, cell_size, cell_size)

        if (
            hasattr(self.game.current_state, "last_move")
            and self.game.current_state.last_move.row != -1
        ):
            if (
                row == self.game.current_state.last_move.row
                and col == self.game.current_state.last_move.col
            ):
                highlight = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
                highlight.fill((255, 255, 100, 30))
                surface.blit(highlight, cell_rect.topleft)

        pygame.draw.rect(surface, COLOR_GRID, cell_rect, max(1, int(cell_size * 0.04)))

        cell_content = self.game.current_state.field[row][col]
        padding = int(cell_size * 0.15)
        outline_thickness = max(2, int(cell_size * 0.1))
        main_thickness = max(1, int(cell_size * 0.08))

        if cell_content == 0:
            pygame.draw.line(
                surface,
                COLOR_X_OUTLINE,
                (x + padding, y + padding),
                (x + cell_size - padding, y + cell_size - padding),
                outline_thickness,
            )
            pygame.draw.line(
                surface,
                COLOR_X_OUTLINE,
                (x + cell_size - padding, y + padding),
                (x + padding, y + cell_size - padding),
                outline_thickness,
            )
            pygame.draw.line(
                surface,
                COLOR_X_MAIN,
                (x + padding, y + padding),
                (x + cell_size - padding, y + cell_size - padding),
                main_thickness,
            )
            pygame.draw.line(
                surface,
                COLOR_X_MAIN,
                (x + cell_size - padding, y + padding),
                (x + padding, y + cell_size - padding),
                main_thickness,
            )

        elif cell_content == 1:
            center = (x + cell_size / 2, y + cell_size / 2)
            radius = cell_size / 2 - padding
            if radius > 0:
                pygame.draw.circle(
                    surface, COLOR_O_OUTLINE, center, radius, outline_thickness
                )
                pygame.draw.circle(
                    surface, COLOR_O_MAIN, center, radius, main_thickness
                )

    def draw_win_line(self):
        if not self.win_line:
            return

        progress = min(1.0, (pygame.time.get_ticks() - self.game_over_start_time) / 800)
        start_row, start_col, end_row, end_col = self.win_line

        cell_size = self.current_cell_size
        half_cell = cell_size / 2

        x1 = self.view_offset_x + start_col * cell_size + half_cell
        y1 = self.view_offset_y + start_row * cell_size + half_cell
        x2 = self.view_offset_x + end_col * cell_size + half_cell
        y2 = self.view_offset_y + end_row * cell_size + half_cell

        current_x = x1 + (x2 - x1) * progress
        current_y = y1 + (y2 - y1) * progress

        pygame.draw.line(
            self.field_surface,
            COLOR_WIN_LINE,
            (x1, y1),
            (current_x, current_y),
            max(4, int(cell_size * 0.1)),
        )

    def draw_game_over(self):
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.screen.blit(overlay, (0, 0))
        font = pygame.font.SysFont("Arial", 48, bold=True)
        lines = self.game_msg.split("!")
        if len(lines) > 1:
            lines = [lines[0] + "!", lines[1]]
        else:
            lines = [self.game_msg, "Click to restart"]
        y_offset = -40
        for i, line in enumerate(lines):
            text = font.render(line, True, COLOR_TEXT)
            text_rect = text.get_rect(
                center=(
                    self.screen.get_width() // 2,
                    self.screen.get_height() // 2 + y_offset * i,
                )
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
            line = self.check_direction(
                field, last_move.row, last_move.col, dr, dc, player
            )
            if line:
                return line
        return None

    def check_direction(self, field, row, col, dr, dc, player):
        start_r, start_c = row, col
        while True:
            next_r, next_c = start_r - dr, start_c - dc
            if (
                0 <= next_r < Field.HEIGHT
                and 0 <= next_c < Field.WIDTH
                and field[next_r][next_c] == player
            ):
                start_r, start_c = next_r, next_c
            else:
                break
        end_r, end_c = row, col
        while True:
            next_r, next_c = end_r + dr, end_c + dc
            if (
                0 <= next_r < Field.HEIGHT
                and 0 <= next_c < Field.WIDTH
                and field[next_r][next_c] == player
            ):
                end_r, end_c = next_r, next_c
            else:
                break
        if (
            abs(end_r - start_r) + 1 >= Field.STREAK_TO_WIN
            or abs(end_c - start_c) + 1 >= Field.STREAK_TO_WIN
        ):
            return (start_r, start_c, end_r, end_c)
        return None

    def return_to_menu(self):
        self.running = False
        self.fullscreen_state = self.fullscreen
        self.screen_size = self.screen.get_size()
