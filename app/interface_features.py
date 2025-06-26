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
COLOR_INV_BG = (160, 160, 160)

STATUS_HEIGHT = 50
MESSAGE_HEIGHT = 40
PADDING = 10
CANONICAL_FIGURE_RENDER_SIZE = 100

class Figure:
    def __init__(self, code: int, num_features: int):
        self.code = code
        self.num_features = num_features
        self.bits = list(map(int, f'{code:0{num_features}b}'))
        self.image = self._render(CANONICAL_FIGURE_RENDER_SIZE)
        self.pos = (0, 0)
        self._inventory_rect = None
        
    def _render(self, size: int):
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        
        player_bit = self.bits[0]
        
        primary_color_is_light = len(self.bits) > 1 and self.bits[1] == 1
        primary_color = (220, 220, 220) if primary_color_is_light else (60, 60, 60)
        
        is_small_figure_feature = len(self.bits) > 2 and self.bits[2] == 0
        base_scale_on_canvas = 0.6 if is_small_figure_feature else 0.9

        is_thin_line = len(self.bits) > 3 and self.bits[3] == 0
        thickness = int(size * 0.04) if is_thin_line else int(size * 0.08)
        
        has_center_dot = len(self.bits) > 4 and self.bits[4] == 1
        center_dot_color = (255, 0, 0)

        has_center_square_outline = len(self.bits) > 5 and self.bits[5] == 1
        center_square_color = (0, 0, 255)
        
        render_area_size = size * base_scale_on_canvas
        rect_margin = (size - render_area_size) / 2
        shape_rect = pygame.Rect(rect_margin, rect_margin, render_area_size, render_area_size)

        if player_bit == Player.Type.CROSS.value:
            line_points = [(shape_rect.topleft, shape_rect.bottomright), (shape_rect.topright, shape_rect.bottomleft)]
            for p1, p2 in line_points:
                pygame.draw.line(surf, primary_color, p1, p2, thickness)
        else:
            pygame.draw.ellipse(surf, primary_color, shape_rect, thickness)

        if has_center_square_outline:
            square_size = max(5, int(render_area_size * 0.3))
            square_rect = pygame.Rect(0, 0, square_size, square_size)
            square_rect.center = shape_rect.center
            pygame.draw.rect(surf, center_square_color, square_rect, max(1, thickness // 3))

        if has_center_dot:
            dot_radius = max(2, thickness // 2, int(render_area_size * 0.1))
            if has_center_square_outline:
                dot_radius = max(1, int(square_size * 0.3)) 
            pygame.draw.circle(surf, center_dot_color, shape_rect.center, dot_radius)
            
        return surf

    def draw(self, surface, display_rect: pygame.Rect = None, center_pos: tuple = None, display_size: int = None):
        if display_rect:
            current_display_size = min(display_rect.width, display_rect.height)
            target_pos = display_rect.topleft
        elif center_pos and display_size:
            current_display_size = display_size
            target_pos = (center_pos[0] - current_display_size // 2, center_pos[1] - current_display_size // 2)
        else:
            surface.blit(self.image, self.pos); return
        if current_display_size <= 0: return
        scaled_image = pygame.transform.smoothscale(self.image, (current_display_size, current_display_size))
        surface.blit(scaled_image, target_pos)

    def __eq__(self, other):
        return isinstance(other, Figure) and self.code == other.code

class PyGameInterfaceFeatures:
    MIN_INV_PIECE_SIZE = 35
    MAX_INV_PIECE_SIZE = 70
    MAX_PIECES_PER_INV_COLUMN = 8 
    INV_PANEL_MIN_WIDTH = 80

    def __init__(
        self, game, dqn_player, pure_mcts_ref, mcts_enabled: bool, player_type: Player.Type,
        fullscreen_start=False, initial_size=None, mcts_vs_dqn=False, mcts_vs_dqn_choice='mcts_x'
    ):
        self.game = game
        self.running = True
        self.game_over = False
        self.win_line = None
        self.fullscreen = fullscreen_start
        self.initial_size = initial_size if initial_size else (1200, 800)
        self.screen_size = self.initial_size
        self.inv_columns = 1
        
        if fullscreen_start:
            self.windowed_size = self.initial_size
 
        self.game_over_start_time = 0
        self.game_over_duration = 3000
        self.game_msg = "Game in progress"
        
        self.az_player = dqn_player
        self.pure_mcts_player = pure_mcts_ref
        self.human_player_type = player_type
        self.mcts_vs_dqn = mcts_vs_dqn
        self.mcts_vs_dqn_choice = mcts_vs_dqn_choice
        self.human_plays_against_ai = mcts_enabled and not self.mcts_vs_dqn
        self.ai_opponent_for_human = self.az_player if self.human_plays_against_ai else None
        
        self.need_computer_move = False
        self.allowed_to_click = False

        self.zoom = 1.0
        self.min_zoom, self.max_zoom = 0.2, 5.0
        self.view_offset_x = 0
        self.view_offset_y = 0
        self.is_panning = False
        self.pan_start_pos = (0, 0)
        
        self.inv_piece_size = self._calculate_inv_piece_size()
        self.inventory_panel_width = (self.inv_piece_size * self.inv_columns) + (PADDING * (self.inv_columns + 1))
        self.inventory_panel_width = max(self.inventory_panel_width, self.INV_PANEL_MIN_WIDTH)
        self.base_cell_size = self._calculate_base_cell_size()

        self._init_inventories()
        self.dragged_piece = None

        self._init_window()
        self.center_view()
        self._update_game_state()

    def _init_inventories(self):
        count_figures_per_player = 1 << (Field.COUNT_FEATURES - 1)
        self.inventory = {
            Player.Type.CROSS: [Figure(c, Field.COUNT_FEATURES) for c in range(count_figures_per_player)],
            Player.Type.NAUGHT: [Figure(c, Field.COUNT_FEATURES) for c in range(count_figures_per_player, 2 * count_figures_per_player)]
        }

    def _calculate_base_cell_size(self):
        screen_w, screen_h = self.initial_size
        current_inv_panel_width = (self.inv_piece_size * self.inv_columns) + (PADDING * (self.inv_columns + 1))
        current_inv_panel_width = max(current_inv_panel_width, self.INV_PANEL_MIN_WIDTH)

        eff_field_w = screen_w - 2 * current_inv_panel_width - 2 * PADDING
        eff_field_h = screen_h - (STATUS_HEIGHT + MESSAGE_HEIGHT + 2 * PADDING)
        if Field.WIDTH == 0 or Field.HEIGHT == 0: return 50
        return min(eff_field_w // Field.WIDTH, eff_field_h // Field.HEIGHT, 100)

    def _calculate_inv_piece_size(self, available_height_for_inv=None):
        if available_height_for_inv is None:
            available_height_for_inv = (self.initial_size[1]) - (STATUS_HEIGHT + MESSAGE_HEIGHT + 2 * PADDING)

        num_pieces_per_player = 1 << (Field.COUNT_FEATURES - 1)
        if num_pieces_per_player == 0: return self.MIN_INV_PIECE_SIZE

        size_one_col = (available_height_for_inv - (num_pieces_per_player + 1) * PADDING) / num_pieces_per_player
        
        self.inv_columns = 1
        calculated_size = size_one_col
        if num_pieces_per_player > self.MAX_PIECES_PER_INV_COLUMN and size_one_col < self.MIN_INV_PIECE_SIZE * 1.5 :
            potential_cols = 2
            rows_per_column_multi = (num_pieces_per_player + potential_cols -1) // potential_cols
            if rows_per_column_multi == 0 : rows_per_column_multi = 1 # Avoid division by zero
            size_multi_col = (available_height_for_inv - (rows_per_column_multi + 1) * PADDING) / rows_per_column_multi
            
            if size_multi_col > size_one_col or size_one_col < self.MIN_INV_PIECE_SIZE :
                 self.inv_columns = potential_cols
                 calculated_size = size_multi_col
            
        final_size = max(self.MIN_INV_PIECE_SIZE, min(int(calculated_size), self.MAX_INV_PIECE_SIZE))
        return final_size

    @property
    def cell_size(self):
        return self.base_cell_size * self.zoom

    def _init_window(self):
        flags = pygame.FULLSCREEN if self.fullscreen else pygame.RESIZABLE
        size = (0, 0) if self.fullscreen else self.initial_size
        self.screen = pygame.display.set_mode(size, flags)
        pygame.display.set_caption(f"MxNxKxD Game ({Field.WIDTH}x{Field.HEIGHT}x{Field.STREAK_TO_WIN}x{Field.COUNT_FEATURES})")
        self.screen_size = self.screen.get_size()
        self._resize()

    def _update_click_allowed(self):
        current_player_on_board = self.game.current_state.who_moves
        if self.mcts_vs_dqn:
            self.allowed_to_click = False 
            self.need_computer_move = True 
        elif self.human_plays_against_ai:
            self.allowed_to_click = (current_player_on_board == self.human_player_type)
            self.need_computer_move = (current_player_on_board != self.human_player_type)
        else:
            self.allowed_to_click = True
            self.need_computer_move = False

    def _resize(self):
        screen_width, screen_height = self.screen.get_size()
        self.screen_size = (screen_width, screen_height)
        self.available_inv_height = screen_height - (STATUS_HEIGHT + MESSAGE_HEIGHT + 2 * PADDING)
        
        self.inv_piece_size = self._calculate_inv_piece_size(self.available_inv_height)
        self.inventory_panel_width = (self.inv_piece_size * self.inv_columns) + (PADDING * (self.inv_columns + 1))
        self.inventory_panel_width = max(self.inventory_panel_width, self.INV_PANEL_MIN_WIDTH)

        self.base_cell_size = self._calculate_base_cell_size()

        self.status_rect = pygame.Rect(0, 0, screen_width, STATUS_HEIGHT)
        self.message_rect = pygame.Rect(0, STATUS_HEIGHT, screen_width, MESSAGE_HEIGHT)
        
        self.left_inventory_rect = pygame.Rect(PADDING, STATUS_HEIGHT + MESSAGE_HEIGHT + PADDING, self.inventory_panel_width, self.available_inv_height)
        self.right_inventory_rect = pygame.Rect(screen_width - PADDING - self.inventory_panel_width, STATUS_HEIGHT + MESSAGE_HEIGHT + PADDING, self.inventory_panel_width, self.available_inv_height)

        self.field_x = self.left_inventory_rect.right + PADDING
        self.field_y = STATUS_HEIGHT + MESSAGE_HEIGHT + PADDING
        self.field_width = self.right_inventory_rect.left - PADDING - self.field_x
        self.field_height = self.available_inv_height
        
        self.field_rect = pygame.Rect(self.field_x, self.field_y, self.field_width, self.field_height)
        
        if self.field_width > 0 and self.field_height > 0:
            self.field_surf = self.screen.subsurface(self.field_rect)
        else:
            self.field_surf = pygame.Surface((1,1)) 
        self.center_view()

    def run(self):
        clock = pygame.time.Clock()
        calc_thread = None
        next_move = None
        while self.running:
            for event in pygame.event.get():
                self._handle_event(event)
            current_time = pygame.time.get_ticks()
            if self.game_over and (current_time - self.game_over_start_time) > self.game_over_duration:
                self._reset()
            who_moves = self.game.current_state.who_moves
            if self.mcts_vs_dqn:
                if not self.game_over and calc_thread is None:
                    def calculate_move_ai_vs_ai():
                        nonlocal next_move
                        if who_moves == Player.Type.CROSS:
                            if self.mcts_vs_dqn_choice == 'mcts_x':
                                if self.pure_mcts_player: next_move = self.pure_mcts_player.get_move()
                            else:
                                if self.az_player: next_move = self.az_player.get_move()
                        elif who_moves == Player.Type.NAUGHT:
                            if self.mcts_vs_dqn_choice == 'mcts_x':
                                if self.az_player: next_move = self.az_player.get_move()
                            else:
                                if self.pure_mcts_player: next_move = self.pure_mcts_player.get_move()
                    if self.az_player or self.pure_mcts_player:
                        calc_thread = threading.Thread(target=calculate_move_ai_vs_ai, daemon=True); calc_thread.start()
                if calc_thread and not calc_thread.is_alive():
                    if next_move is not None:
                        moving_player_type = self.game.current_state.who_moves
                        inventory_list = self.inventory[moving_player_type]
                        piece_to_remove = next((p for p in inventory_list if p.code == next_move.figure), None)
                        if piece_to_remove: inventory_list.remove(piece_to_remove)
                        self.game.make_silent_move(next_move)
                        if self.az_player: self.az_player.move_and_update(next_move)
                        if self.pure_mcts_player: self.pure_mcts_player.move_and_update(next_move)
                        self._update_game_state(); next_move = None
                    calc_thread = None
            elif self.human_plays_against_ai and self.need_computer_move:
                if not self.game_over and not calc_thread and self.ai_opponent_for_human:
                    def worker_ai_move():
                        nonlocal next_move
                        next_move = self.ai_opponent_for_human.get_move()
                    calc_thread = threading.Thread(target=worker_ai_move, daemon=True); calc_thread.start()
                if calc_thread and not calc_thread.is_alive():
                    if next_move is not None:
                        moving_player_type = self.game.current_state.who_moves
                        inventory_list = self.inventory[moving_player_type]
                        piece_to_remove = next((p for p in inventory_list if p.code == next_move.figure), None)
                        if piece_to_remove: inventory_list.remove(piece_to_remove)
                        self.game.make_silent_move(next_move)
                        if self.ai_opponent_for_human: self.ai_opponent_for_human.move_and_update(next_move)
                        self._update_game_state(); next_move = None
                    calc_thread = None
            self._draw(); pygame.display.flip(); clock.tick(60)
        return self.fullscreen

    def _handle_event(self, event):
        if event.type == QUIT: self.running = False; return
        if event.type == KEYDOWN:
            if event.key == K_f: self._toggle_fullscreen()
            elif event.key == K_r: self._reset()
        if event.type == VIDEORESIZE and not self.fullscreen:
            self.initial_size = event.size; self._resize()

        current_player_board_turn = self.game.current_state.who_moves
        can_human_interact = self.allowed_to_click

        if event.type == MOUSEBUTTONDOWN:
            if event.button == 1 and can_human_interact:
                active_inventory_rect = self.left_inventory_rect if current_player_board_turn == Player.Type.CROSS else self.right_inventory_rect
                if not self.dragged_piece and active_inventory_rect.collidepoint(event.pos):
                    for piece in self.inventory[current_player_board_turn]:
                        if piece._inventory_rect and piece._inventory_rect.collidepoint(event.pos):
                            self.dragged_piece = piece; self.dragged_piece.pos = event.pos; return 
            if self.field_rect.collidepoint(event.pos):
                if event.button == 4: self._zoom(event.pos, 1.15)
                elif event.button == 5: self._zoom(event.pos, 1 / 1.15)
                elif event.button == 3: self.is_panning = True; self.pan_start_pos = event.pos
            if event.button == 1 and not self.dragged_piece and self.field_rect.collidepoint(event.pos):
                if self.game_over: self._reset()
        if event.type == MOUSEBUTTONUP:
            if event.button == 3: self.is_panning = False
            if event.button == 1 and self.dragged_piece:
                if self.field_rect.collidepoint(event.pos) and can_human_interact:
                    row, col = self._to_cell(event.pos)
                    if (0 <= row < Field.HEIGHT and 0 <= col < Field.WIDTH and self.game.current_state.field[row][col] == -1):
                        cell_move = Field.Cell(row, col, self.dragged_piece.code)
                        self.inventory[current_player_board_turn].remove(self.dragged_piece)
                        self.game.make_silent_move(cell_move)
                        if self.human_plays_against_ai and self.ai_opponent_for_human:
                             self.ai_opponent_for_human.move_and_update(cell_move)
                        self._update_game_state()
                self.dragged_piece = None
        if event.type == MOUSEMOTION:
            if self.is_panning:
                dx = event.pos[0] - self.pan_start_pos[0]; dy = event.pos[1] - self.pan_start_pos[1]
                self.view_offset_x += dx; self.view_offset_y += dy; self.pan_start_pos = event.pos
            if self.dragged_piece: self.dragged_piece.pos = event.pos

    def _zoom(self, mouse_screen_pos, factor):
        mouse_field_x = mouse_screen_pos[0] - self.field_x; mouse_field_y = mouse_screen_pos[1] - self.field_y
        world_x = (mouse_field_x - self.view_offset_x) / self.zoom; world_y = (mouse_field_y - self.view_offset_y) / self.zoom
        self.zoom = max(self.min_zoom, min(self.max_zoom, self.zoom * factor))
        self.view_offset_x = mouse_field_x - world_x * self.zoom; self.view_offset_y = mouse_field_y - world_y * self.zoom

    def center_view(self):
        board_pixel_width = Field.WIDTH * self.cell_size; board_pixel_height = Field.HEIGHT * self.cell_size
        self.view_offset_x = (self.field_width - board_pixel_width) / 2; self.view_offset_y = (self.field_height - board_pixel_height) / 2

    def _toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen; current_size = self.screen.get_size()
        pygame.display.quit(); pygame.display.init()
        if self.fullscreen:
            self.windowed_size = current_size; self.screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        self.screen_size = self.screen.get_size(); self._resize()

    def _to_cell(self, screen_pos):
        relative_x_to_field_surf = screen_pos[0] - self.field_x; relative_y_to_field_surf = screen_pos[1] - self.field_y
        if self.cell_size == 0: return -1, -1
        row = int((relative_y_to_field_surf - self.view_offset_y) / self.cell_size)
        col = int((relative_x_to_field_surf - self.view_offset_x) / self.cell_size)
        return row, col

    def _update_game_state(self):
        state = self.game.current_state.check_game_state()
        current_player_type = self.game.current_state.who_moves
        self.status_msg = f"Current: {Player.Icon[current_player_type]}"
        self._update_click_allowed()
        if state == GameStates.CONTINUE:
            self.game_msg = "Game in progress"; self.game_over = False; self.win_line = None
        else:
            self.game_over = True
            self.game_msg = { GameStates.CROSS_WON: "Crosses Victory! Click/R to restart", GameStates.NAUGHT_WON: "Noughts Victory! Click/R to restart", GameStates.TIE: "Tie! Click/R to restart"}[state]
            self.win_line = self._find_win_line(); self.game_over_start_time = pygame.time.get_ticks()

    def _draw(self):
        self.screen.fill(COLOR_BG); self._draw_status(); self._draw_message()
        self._draw_inventories(); self._draw_field()
        if self.game_over and self.win_line: self._draw_win_line()
        if self.dragged_piece: self.dragged_piece.draw(self.screen, center_pos=self.dragged_piece.pos, display_size=self.inv_piece_size)
        if self.game_over: self._draw_game_over_overlay()

    def _draw_single_inventory(self, pieces_list, panel_rect, is_active_player_inv):
        num_pieces = len(pieces_list)
        if num_pieces == 0: return
        rows_per_visual_column = (num_pieces + self.inv_columns - 1) // self.inv_columns
        current_piece_index = 0
        for col_idx in range(self.inv_columns):
            x_offset_col = panel_rect.left + PADDING + col_idx * (self.inv_piece_size + PADDING)
            y_offset = panel_rect.top + PADDING 
            for row_idx_in_col in range(rows_per_visual_column):
                if current_piece_index >= num_pieces: break
                piece = pieces_list[current_piece_index]
                if piece == self.dragged_piece:
                    current_piece_index += 1; continue
                piece_rect = pygame.Rect(x_offset_col, y_offset, self.inv_piece_size, self.inv_piece_size)
                piece.draw(self.screen, display_rect=piece_rect); piece._inventory_rect = piece_rect
                if is_active_player_inv: pygame.draw.rect(self.screen, (255,255,0, 100), piece_rect, 2)
                y_offset += self.inv_piece_size + PADDING; current_piece_index += 1

    def _draw_inventories(self):
        pygame.draw.rect(self.screen, COLOR_INV_BG, self.left_inventory_rect)
        current_player_board_turn = self.game.current_state.who_moves; is_human_turn = self.allowed_to_click 
        self._draw_single_inventory(self.inventory[Player.Type.CROSS], self.left_inventory_rect, is_human_turn and current_player_board_turn == Player.Type.CROSS)
        pygame.draw.rect(self.screen, COLOR_INV_BG, self.right_inventory_rect)
        self._draw_single_inventory(self.inventory[Player.Type.NAUGHT], self.right_inventory_rect, is_human_turn and current_player_board_turn == Player.Type.NAUGHT)

    def _draw_status(self):
        pygame.draw.rect(self.screen, COLOR_STATUS, self.status_rect)
        font = pygame.font.SysFont('Arial', 28, bold=True); text = font.render(self.status_msg, True, COLOR_TEXT)
        self.screen.blit(text, (self.status_rect.left + PADDING, (self.status_rect.height - text.get_height()) // 2))

    def _draw_message(self):
        pygame.draw.rect(self.screen, COLOR_MESSAGE, self.message_rect)
        font = pygame.font.SysFont('Arial', 24); text = font.render(self.game_msg, True, COLOR_TEXT)
        text_x = (self.message_rect.width - text.get_width()) // 2; text_y = self.message_rect.top + (self.message_rect.height - text.get_height()) // 2
        self.screen.blit(text, (text_x, text_y))

    def _draw_field(self):
        if not hasattr(self, 'field_surf'): return
        self.field_surf.fill(COLOR_FIELD_BG)
        if self.cell_size == 0 : return
        min_row = max(0, int(-self.view_offset_y / self.cell_size) -1)
        max_row = min(Field.HEIGHT, int((-self.view_offset_y + self.field_height) / self.cell_size) +1)
        min_col = max(0, int(-self.view_offset_x / self.cell_size) -1)
        max_col = min(Field.WIDTH, int((-self.view_offset_x + self.field_width) / self.cell_size) +1)
        for row in range(min_row, max_row):
            for col in range(min_col, max_col):
                val = self.game.current_state.field[row][col]
                cell_rect_fs = pygame.Rect(col * self.cell_size + self.view_offset_x, row * self.cell_size + self.view_offset_y, self.cell_size, self.cell_size)
                pygame.draw.rect(self.field_surf, COLOR_GRID, cell_rect_fs, width=max(1,int(self.cell_size*0.03)))
                if val != -1:
                    piece_to_draw = Figure(val, Field.COUNT_FEATURES)
                    piece_to_draw.draw(self.field_surf, center_pos=cell_rect_fs.center, display_size=int(self.cell_size * 0.85))

    def _draw_win_line(self):
        if not self.win_line or not hasattr(self, 'field_surf') or self.cell_size == 0: return
        start_row, start_col, end_row, end_col = self.win_line; progress = min(1.0, (pygame.time.get_ticks() - self.game_over_start_time) / 800.0)
        half_cell = self.cell_size / 2
        x1_fs = self.view_offset_x + start_col * self.cell_size + half_cell; y1_fs = self.view_offset_y + start_row * self.cell_size + half_cell
        x2_fs = self.view_offset_x + end_col * self.cell_size + half_cell; y2_fs = self.view_offset_y + end_row * self.cell_size + half_cell
        current_x_fs = x1_fs + (x2_fs - x1_fs) * progress; current_y_fs = y1_fs + (y2_fs - y1_fs) * progress
        pygame.draw.line(self.field_surf, COLOR_WIN_LINE, (x1_fs, y1_fs), (current_x_fs, current_y_fs), max(4, int(self.cell_size * 0.1)))

    def _draw_game_over_overlay(self):
        overlay_surf = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA); overlay_surf.fill((0, 0, 0, 150)); self.screen.blit(overlay_surf, (0,0))
        font = pygame.font.SysFont('Arial', 48, bold=True); text_parts = self.game_msg.split('!') 
        main_msg = text_parts[0] + ('!' if len(text_parts) > 1 else ''); sub_msg = text_parts[1].strip() if len(text_parts) > 1 else "Click or Press R to restart"
        lines_to_draw = [main_msg, sub_msg]
        for i, line_text in enumerate(lines_to_draw):
            text_surf = font.render(line_text, True, COLOR_TEXT)
            text_rect = text_surf.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 + (i * 60) - 30))
            self.screen.blit(text_surf, text_rect)

    def _reset(self):
        self.game._Game__reset_game(); self.game_over = False; self._init_inventories()
        self.dragged_piece = None; self.win_line = None; self.center_view(); self._update_game_state()
        if self.mcts_vs_dqn:
            if self.az_player: self.az_player.reset_player()
            if self.pure_mcts_player: self.pure_mcts_player.reset_player()
        elif self.human_plays_against_ai and self.ai_opponent_for_human:
            self.ai_opponent_for_human.reset_player()

    def _find_win_line(self):
        field = self.game.current_state.field; last_move = self.game.current_state.last_move
        if not last_move or last_move.row < 0: return None
        placed_piece_code = field[last_move.row][last_move.col]
        if placed_piece_code == -1: return None
        if hasattr(self.game.current_state, 'winning_line_info') and self.game.current_state.winning_line_info:
            return self.game.current_state.winning_line_info
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            line = self._check_dir_visual_streak(field, last_move.row, last_move.col, dr, dc, placed_piece_code)
            if line: return line
        return None

    def _check_dir_visual_streak(self, field_array, r_start, c_start, dr, dc, target_code):
        line_coords = []
        curr_r, curr_c = r_start, c_start
        while 0 <= curr_r < Field.HEIGHT and 0 <= curr_c < Field.WIDTH and field_array[curr_r][curr_c] == target_code:
            line_coords.append((curr_r, curr_c)); curr_r -= dr; curr_c -= dc
        line_coords.reverse() 
        curr_r, curr_c = r_start + dr, c_start + dc
        while 0 <= curr_r < Field.HEIGHT and 0 <= curr_c < Field.WIDTH and field_array[curr_r][curr_c] == target_code:
            line_coords.append((curr_r, curr_c)); curr_r += dr; curr_c += dc
        if len(line_coords) >= Field.STREAK_TO_WIN:
            return (line_coords[0][0], line_coords[0][1], line_coords[-1][0], line_coords[-1][1])
        return None

    def return_to_menu(self):
        self.running = False