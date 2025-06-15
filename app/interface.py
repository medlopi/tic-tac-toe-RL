import pygame
import threading
from pygame.locals import *
from app.game import Game
from app.field import Field, GameStates
from app.player import Player

COLOR_BG = (140, 140, 140)
COLOR_FIELD_BG = (180, 180, 180)
COLOR_STATUS = (53, 0, 211)
COLOR_MESSAGE = (36, 0, 144)
COLOR_GRID = (25, 0, 97)
COLOR_TEXT = (220, 220, 220)
COLOR_WIN_LINE = (0, 0, 0)
STATUS_HEIGHT = 50
MESSAGE_HEIGHT = 40
PADDING = 20
COLOR_MENU_BUTTON = (120, 80, 180)
MENU_BUTTON_WIDTH = 100
MENU_BUTTON_HEIGHT = STATUS_HEIGHT - 10
PIECE_SIZE = 60
INVENTORY_HEIGHT = PIECE_SIZE + PADDING * 2

class Figure:
    def __init__(self, code: int):
        self.code = code
        self.bits = list(map(int, f'{code:0{Field.COUNT_FEATURES}b}'))
        self.image = self._render()
        self.pos = (0, 0)
        self._inventory_rect = None

    def _render(self):
        size = PIECE_SIZE
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        player_bit, color_bit, size_bit, bold_bit = self.bits
        color = (0, 0, 0) if color_bit else (255, 255, 255)
        thickness = 2 + 4 * bold_bit
        scale = 0.5 if size_bit == 0 else 1.0
        area = size * scale
        rect = pygame.Rect(
            (size - area) / 2,
            (size - area) / 2,
            area,
            area
        )
        if player_bit == Player.Type.CROSS.value:
            pygame.draw.line(surf, color, rect.topleft, rect.bottomright, thickness)
            pygame.draw.line(surf, color, rect.topright, rect.bottomleft, thickness)
        else:
            pygame.draw.ellipse(surf, color, rect, thickness)
        return surf

    def draw(self, surface, rect=None, centered_at=None):
        if rect:
            surface.blit(self.image, rect)
        elif centered_at:
            x, y = centered_at
            iw, ih = self.image.get_size()
            surface.blit(self.image, (x - iw // 2, y - ih // 2))

    def __eq__(self, other):
        return isinstance(other, Figure) and self.code == other.code

class PyGameInterface:
    def __init__(
        self,
        mcts_enabled: bool,
        player_type: Player.Type,
        game=None,
        fullscreen_start=False,
        initial_size=None
    ):
        self.game = game or Game()
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
        self.need_computer_move = mcts_enabled and player_type == Player.Type.NAUGHT
        self.allowed_to_click = False
        self._update_click_allowed()

        self.zoom = 1.0
        self.min_zoom, self.max_zoom = 0.2, 5.0
        self.view_offset_x = 0
        self.view_offset_y = 0
        self.is_panning = False
        self.pan_start_pos = (0, 0)
        self.base_cell_size = self.calculate_base_cell_size()

        count_figures = 1 << (Field.COUNT_FEATURES - 1)
        self.inventory = {
            Player.Type.CROSS: [Figure(c) for c in range(count_figures)],
            Player.Type.NAUGHT: [Figure(c) for c in range(count_figures, 2 * count_figures)]
        }
        self.dragged_piece = None

        self._init_window()
        self.center_view()
        self._update_game_state()

    def calculate_base_cell_size(self):
        return 780 // max(Field.HEIGHT, Field.WIDTH, 7)

    @property
    def cell_size(self):
        return self.base_cell_size * self.zoom

    def _init_window(self):
        flags = pygame.FULLSCREEN if self.fullscreen else pygame.RESIZABLE
        size = (0, 0) if self.fullscreen else (self.initial_size or (800, 600))
        self.screen = pygame.display.set_mode(size, flags)
        pygame.display.set_caption("MxNxKxD Game")
        self._resize()

    def _update_click_allowed(self):
        if self.mcts_enabled:
            current_player = self.game.current_state.who_moves
            self.allowed_to_click = (current_player == self.player_type)
            self.need_computer_move = (current_player != self.player_type)
        else:
            self.allowed_to_click = True

    def _resize(self):
        screen_width, screen_height = self.screen.get_size()
        self.field_width = screen_width - 2 * PADDING
        self.field_height = screen_height - (
            STATUS_HEIGHT + MESSAGE_HEIGHT + INVENTORY_HEIGHT + 2 * PADDING
        )
        self.field_x = PADDING
        self.field_y = STATUS_HEIGHT + MESSAGE_HEIGHT + PADDING
        self.field_rect = pygame.Rect(
            self.field_x, self.field_y, self.field_width, self.field_height
        )
        self.field_surf = self.screen.subsurface(self.field_rect)
        self.center_view()

    def run(self):
        clock = pygame.time.Clock()
        calc_thread = None
        next_move = None

        while self.running:
            for event in pygame.event.get():
                self._handle_event(event)

            if self.need_computer_move and not self.game_over and not calc_thread:
                def worker():
                    nonlocal next_move
                    next_move = self.game.mcts_player.get_move()

                calc_thread = threading.Thread(target=worker, daemon=True)
                calc_thread.start()

            if calc_thread and not calc_thread.is_alive():
                if next_move is not None:
                    code = next_move.figure
                    inventory_list = self.inventory[self.game.current_state.who_moves]

                    for piece in inventory_list:
                        if piece.code == code:
                            inventory_list.remove(piece)
                            break

                    self.game.make_silent_move(next_move)
                    self.game.mcts_player.move_and_update(next_move)
                    self._update_game_state()
                    self.need_computer_move = False
                    self._update_click_allowed()
                    next_move = None
                calc_thread = None

            self._draw()
            pygame.display.flip()
            clock.tick(200)

        return self.fullscreen

    def _handle_event(self, event):
        if event.type == QUIT:
            self.running = False
            return

        if event.type == KEYDOWN and event.key == K_f:
            self._toggle_fullscreen()

        if event.type == VIDEORESIZE and not self.fullscreen:
            self._resize()

        if event.type == MOUSEBUTTONDOWN:
            if self.field_rect.collidepoint(event.pos):
                if event.button == 4:
                    self._zoom(event.pos, 1.15)
                elif event.button == 5:
                    self._zoom(event.pos, 1 / 1.15)
                elif event.button == 3:
                    self.is_panning = True
                    self.pan_start_pos = event.pos

            if event.button == 1:
                for piece in self.inventory[self.game.current_state.who_moves]:
                    if piece._inventory_rect and piece._inventory_rect.collidepoint(event.pos):
                        self.dragged_piece = piece
                        piece.pos = event.pos
                        return

        if event.type == MOUSEBUTTONUP:
            if event.button == 3:
                self.is_panning = False

            if event.button == 1 and self.dragged_piece:
                if self.field_rect.collidepoint(event.pos):
                    row, col = self._to_cell(event.pos)
                    if (
                        0 <= row < Field.HEIGHT 
                        and 0 <= col < Field.WIDTH 
                        and self.game.current_state.field[row][col] == -1
                    ):
                        cell = Field.Cell(row, col, self.dragged_piece.code)
                        self.inventory[self.game.current_state.who_moves].remove(self.dragged_piece)
                        self.game.make_silent_move(cell)
                        if self.mcts_enabled:
                            self.game.mcts_player.move_and_update(cell)
                        self._update_game_state()
                self.dragged_piece = None

        if event.type == MOUSEMOTION:
            if self.is_panning:
                dx = event.pos[0] - self.pan_start_pos[0]
                dy = event.pos[1] - self.pan_start_pos[1]
                self.view_offset_x += dx
                self.view_offset_y += dy
                self.pan_start_pos = event.pos

            if self.dragged_piece:
                self.dragged_piece.pos = event.pos

        if event.type == MOUSEBUTTONDOWN and event.button == 1 and not self.dragged_piece:
            if self.game_over:
                self._reset()
            elif self.allowed_to_click:
                self._click(event.pos)

    def _zoom(self, pos, factor):
        mouse_x, mouse_y = pos[0] - self.field_x, pos[1] - self.field_y
        world_x = (mouse_x - self.view_offset_x) / self.zoom
        world_y = (mouse_y - self.view_offset_y) / self.zoom
        self.zoom = max(self.min_zoom, min(self.max_zoom, self.zoom * factor))
        self.view_offset_x = mouse_x - world_x * self.zoom
        self.view_offset_y = mouse_y - world_y * self.zoom

    def center_view(self):
        view_width, view_height = self.field_width, self.field_height
        board_width = Field.WIDTH * self.cell_size
        board_height = Field.HEIGHT * self.cell_size
        self.view_offset_x = (view_width - board_width) / 2
        self.view_offset_y = (view_height - board_height) / 2

    def _toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.windowed_size = self.screen.get_size()
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        self._resize()

    def _click(self, pos):
        if not self.field_rect.collidepoint(pos):
            return
            
        row, col = self._to_cell(pos)
        if (
            0 <= row < Field.HEIGHT 
            and 0 <= col < Field.WIDTH 
            and self.game.current_state.field[row][col] == -1
        ):
            cell = Field.Cell(row, col, 0)
            self.game.make_silent_move(cell)
            if self.mcts_enabled:
                self.game.mcts_player.move_and_update(cell)
            self._update_game_state()
            if self.mcts_enabled and not self.game_over:
                self.allowed_to_click = False
                self.need_computer_move = True

    def _to_cell(self, pos):
        relative_x = pos[0] - self.field_x
        relative_y = pos[1] - self.field_y
        row = int((relative_y - self.view_offset_y) / self.cell_size)
        col = int((relative_x - self.view_offset_x) / self.cell_size)
        return row, col

    def _update_game_state(self):
        state = self.game.current_state.check_game_state()
        current_player = self.game.current_state.who_moves
        self.status_msg = f"Current: {Player.Icon[current_player]}"
        self._update_click_allowed()

        if state == GameStates.CONTINUE:
            self.game_msg = "Game in progress"
            self.game_over = False
            self.win_line = None
        else:
            self.game_over = True
            self.game_msg = {
                GameStates.CROSS_WON: "Crosses Victory! Click to restart",
                GameStates.NAUGHT_WON: "Noughts Victory! Click to restart",
                GameStates.TIE: "Tie! Click to restart"
            }[state]
            self.win_line = self._find_win_line()
            self.game_over_start_time = pygame.time.get_ticks()

    def _draw(self):
        self.screen.fill(COLOR_BG)
        self._draw_status()
        self._draw_message()
        self._draw_field()
        self._draw_opponent_inventory()
        self._draw_inventory()

        if self.game_over:
            self._draw_win_line()
            self._draw_game_over()

        if self.dragged_piece:
            self.dragged_piece.draw(self.screen, centered_at=self.dragged_piece.pos)

    def _draw_opponent_inventory(self):
        opponent = Player.Type(abs(self.game.current_state.who_moves.value - 1))
        screen_width, screen_height = self.screen.get_size()
        inventory_y = self.field_y - INVENTORY_HEIGHT
        pygame.draw.rect(self.screen, COLOR_FIELD_BG, (0, inventory_y, screen_width, INVENTORY_HEIGHT))

        x = PADDING
        for piece in self.inventory[opponent]:
            rect = pygame.Rect(x, inventory_y + PADDING, PIECE_SIZE, PIECE_SIZE)
            piece.draw(self.screen, rect=rect)
            piece._inventory_rect = rect
            x += PIECE_SIZE + PADDING

    def _draw_status(self):
        width = self.screen.get_width()
        pygame.draw.rect(self.screen, COLOR_STATUS, (0, 0, width, STATUS_HEIGHT))

        menu_rect = pygame.Rect(
            width - MENU_BUTTON_WIDTH - 10,
            5,
            MENU_BUTTON_WIDTH,
            MENU_BUTTON_HEIGHT
        )
        pygame.draw.rect(self.screen, COLOR_MENU_BUTTON, menu_rect, border_radius=5)

        font = pygame.font.SysFont('Arial', 24)
        self.screen.blit(font.render("MENU", True, COLOR_TEXT), (menu_rect.centerx - 30, menu_rect.centery - 12))

        font = pygame.font.SysFont('Arial', 28, bold=True)
        text = font.render(self.status_msg, True, COLOR_TEXT)
        self.screen.blit(text, (PADDING, (STATUS_HEIGHT - text.get_height()) // 2))

    def _draw_message(self):
        width = self.screen.get_width()
        pygame.draw.rect(self.screen, COLOR_MESSAGE, (0, STATUS_HEIGHT, width, MESSAGE_HEIGHT))

        font = pygame.font.SysFont('Arial', 24)
        text = font.render(self.game_msg, True, COLOR_TEXT)
        text_x = (width - text.get_width()) // 2
        text_y = STATUS_HEIGHT + (MESSAGE_HEIGHT - text.get_height()) // 2
        self.screen.blit(text, (text_x, text_y))

    def _draw_field(self):
        self.field_surf.fill(COLOR_FIELD_BG)

        for row in range(Field.HEIGHT):
            for col in range(Field.WIDTH):
                val = self.game.current_state.field[row][col]
                rect = pygame.Rect(
                    col * self.cell_size + self.view_offset_x,
                    row * self.cell_size + self.view_offset_y,
                    self.cell_size,
                    self.cell_size
                )
                pygame.draw.rect(self.field_surf, COLOR_GRID, rect, width=3)

                if val != -1:
                    piece = Figure(val)
                    piece.draw(self.field_surf, centered_at=rect.center)

    def _draw_inventory(self):
        screen_width, screen_height = self.screen.get_size()
        inventory_y = screen_height - INVENTORY_HEIGHT
        pygame.draw.rect(self.screen, COLOR_FIELD_BG, (0, inventory_y, screen_width, INVENTORY_HEIGHT))

        x = PADDING
        for piece in self.inventory[self.game.current_state.who_moves]:
            rect = pygame.Rect(x, inventory_y + PADDING, PIECE_SIZE, PIECE_SIZE)
            piece.draw(self.screen, rect=rect)
            piece._inventory_rect = rect
            x += PIECE_SIZE + PADDING

    def _draw_win_line(self):
        if not self.win_line:
            return

        start_row, start_col, end_row, end_col = self.win_line
        progress = min(1, (pygame.time.get_ticks() - self.game_over_start_time) / 800)
        cell_size = self.cell_size
        half_cell = cell_size / 2

        x1 = self.view_offset_x + start_col * cell_size + half_cell
        y1 = self.view_offset_y + start_row * cell_size + half_cell
        x2 = self.view_offset_x + end_col * cell_size + half_cell
        y2 = self.view_offset_y + end_row * cell_size + half_cell

        current_x = x1 + (x2 - x1) * progress
        current_y = y1 + (y2 - y1) * progress

        pygame.draw.line(
            self.field_surf,
            COLOR_WIN_LINE,
            (x1, y1),
            (current_x, current_y),
            max(4, int(cell_size * 0.1))
        )

    def _draw_game_over(self):
        overlay = pygame.Surface(self.screen.get_size(), SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.screen.blit(overlay, (0, 0))

        font = pygame.font.SysFont('Arial', 48, bold=True)
        lines = self.game_msg.split('!')

        if len(lines) > 1:
            lines = [lines[0] + '!', lines[1]]
        else:
            lines = [self.game_msg, 'Click to restart']

        for i, line in enumerate(lines):
            text = font.render(line, True, COLOR_TEXT)
            text_x = (self.screen.get_width() - text.get_width()) // 2
            text_y = (self.screen.get_height() // 2) + (i - 0.5) * 60
            self.screen.blit(text, (text_x, text_y))

    def _reset(self):
        self.game._Game__reset_game()
        self.game_over = False
        self.inventory = {
            Player.Type.CROSS: [Figure(c) for c in range(8)],
            Player.Type.NAUGHT: [Figure(c) for c in range(8, 16)]
        }
        self.dragged_piece = None
        self.win_line = None
        self._update_game_state()
        self._update_click_allowed()

    def _find_win_line(self):
        field = self.game.current_state.field
        last_move = self.game.current_state.last_move

        if not last_move or last_move.row < 0:
            return None

        player = field[last_move.row][last_move.col]
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        for dr, dc in directions:
            line = self._check_dir(field, last_move.row, last_move.col, dr, dc, player)
            if line:
                return line
      
        return None

    def _check_dir(self, field, r, c, dr, dc, player):
        start_row, start_col = r, c
        end_row, end_col = r, c

        while (
            0 <= start_row - dr < Field.HEIGHT 
            and 0 <= start_col - dc < Field.WIDTH 
            and field[start_row - dr][start_col - dc] == player
        ):
            start_row -= dr
            start_col -= dc

        while (
            0 <= end_row + dr < Field.HEIGHT 
            and 0 <= end_col + dc < Field.WIDTH 
            and field[end_row + dr][end_col + dc] == player
        ):
            end_row += dr
            end_col += dc

        if (
            abs(end_row - start_row) + 1 >= Field.STREAK_TO_WIN 
            or abs(end_col - start_col) + 1 >= Field.STREAK_TO_WIN
        ):
            return (start_row, start_col, end_row, end_col)

        return None

    def return_to_menu(self):
        self.running = False
        self.fullscreen_state = self.fullscreen
        self.screen_size = self.screen.get_size()
