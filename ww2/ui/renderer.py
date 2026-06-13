import pygame
import math
from ..map.hex_grid import Hex
from ..map.terrain import Terrain, TERRAIN_COLORS
from ..units.combat import NATION_NAMES
from .colors import *

pygame.font.init()
try:
    FONT_SMALL = pygame.font.SysFont("Microsoft YaHei", 14)
    FONT_MED = pygame.font.SysFont("Microsoft YaHei", 18)
    FONT_LARGE = pygame.font.SysFont("Microsoft YaHei", 24)
    FONT_BOLD = pygame.font.SysFont("Microsoft YaHei", 28)
except:
    FONT_SMALL = pygame.font.Font(None, 14)
    FONT_MED = pygame.font.Font(None, 18)
    FONT_LARGE = pygame.font.Font(None, 24)
    FONT_BOLD = pygame.font.Font(None, 28)


class Renderer:
    def __init__(self, screen, map_offset_x=0, map_offset_y=0):
        self.screen = screen
        self.map_offset_x = map_offset_x
        self.map_offset_y = map_offset_y
        self.panel_width = 280
        self.move_hexes = set()
        self.attack_hexes = set()
        self.dragging = False
        self.drag_start = (0, 0)
        self.drag_offset_start = (0, 0)

    def world_to_screen(self, wx, wy):
        return (wx + self.map_offset_x, wy + self.map_offset_y)

    def screen_to_world(self, sx, sy):
        return (sx - self.map_offset_x, sy - self.map_offset_y)

    def render(self, game_state):
        self.screen.fill(DARK_GRAY)
        self._render_map(game_state)
        self._render_units(game_state)
        self._render_overlays(game_state)
        self._render_panel(game_state)
        pygame.display.flip()

    def _render_map(self, game_state):
        m = game_state.map
        for q in range(m.cols):
            for r in range(m.rows):
                h = Hex(q, r)
                t_val = m.terrain.get((q, r), 0)
                terrain = Terrain(t_val)
                color = TERRAIN_COLORS.get(terrain, (100, 100, 100))
                corners = m.hex_corners(h)
                screen_corners = [self.world_to_screen(c[0], c[1]) for c in corners]
                if len(screen_corners) >= 3:
                    pygame.draw.polygon(self.screen, color, screen_corners)
                    pygame.draw.polygon(self.screen, GRAY, screen_corners, 1)

        for pos, vp in game_state.victory_points.items():
            h = Hex(*pos)
            cx, cy = self.world_to_screen(*m.hex_to_pixel(h))
            vp_color = YELLOW
            unit = game_state.get_unit_at(pos)
            if unit:
                if game_state._is_player_side(unit.nation):
                    vp_color = GREEN
                else:
                    vp_color = RED
            pygame.draw.circle(self.screen, vp_color, (int(cx), int(cy)), 8, 2)
            txt = FONT_SMALL.render(str(vp["value"]), True, vp_color)
            self.screen.blit(txt, (cx - 3, cy - 3))

    def _render_units(self, game_state):
        m = game_state.map
        for unit in game_state.units.values():
            if not unit.is_alive:
                continue
            h = Hex(*unit.hex_pos)
            cx, cy = self.world_to_screen(*m.hex_to_pixel(h))
            cx, cy = int(cx), int(cy)
            nation_color = NATION_COLORS.get(unit.nation, GRAY)

            rect = pygame.Rect(cx - 14, cy - 12, 28, 24)
            pygame.draw.rect(self.screen, nation_color, rect, border_radius=2)
            pygame.draw.rect(self.screen, BLACK, rect, 2)

            if unit.current_steps < unit.max_steps:
                pygame.draw.line(self.screen, YELLOW, (cx - 14, cy - 12), (cx + 14, cy + 12), 2)

            atk_txt = FONT_SMALL.render(str(unit.attack_power), True, WHITE)
            def_txt = FONT_SMALL.render(str(unit.defense_power), True, WHITE)
            self.screen.blit(atk_txt, (cx - 13, cy - 10))
            self.screen.blit(def_txt, (cx - 1, cy - 10))

            if unit.moved_this_turn and unit.attacked_this_turn:
                pygame.draw.circle(self.screen, RED, (cx + 14, cy + 12), 4)

    def _render_overlays(self, game_state):
        m = game_state.map
        for pos in self.move_hexes:
            h = Hex(*pos)
            corners = m.hex_corners(h)
            screen_corners = [self.world_to_screen(c[0], c[1]) for c in corners]
            s = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
            pygame.draw.polygon(s, MOVE_RANGE, screen_corners)
            self.screen.blit(s, (0, 0))

        for pos in self.attack_hexes:
            h = Hex(*pos)
            corners = m.hex_corners(h)
            screen_corners = [self.world_to_screen(c[0], c[1]) for c in corners]
            s = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
            pygame.draw.polygon(s, ATTACK_RANGE, screen_corners)
            self.screen.blit(s, (0, 0))

        if game_state.selected_unit:
            unit = game_state.units.get(game_state.selected_unit)
            if unit:
                h = Hex(*unit.hex_pos)
                cx, cy = self.world_to_screen(*m.hex_to_pixel(h))
                pygame.draw.circle(self.screen, SELECTED, (int(cx), int(cy)), 16, 2)

    def _render_panel(self, game_state):
        sw = self.screen.get_width()
        sh = self.screen.get_height()
        px = sw - self.panel_width
        pygame.draw.rect(self.screen, PANEL_BG, (px, 0, self.panel_width, sh))
        pygame.draw.line(self.screen, GRAY, (px, 0), (px, sh), 2)

        y = 10

        txt = FONT_LARGE.render(f"回合 {game_state.turn_number}/{game_state.max_turns}", True, WHITE)
        self.screen.blit(txt, (px + 10, y))
        y += 30

        player_tag = "我方行动" if game_state.current_player == "player" else "AI 思考中"
        txt = FONT_MED.render(player_tag, True, YELLOW)
        self.screen.blit(txt, (px + 10, y))
        y += 26

        pn_cn = NATION_NAMES.get(game_state.player_nation, game_state.player_nation)
        txt = FONT_MED.render(f"阵营: {pn_cn}", True, WHITE)
        self.screen.blit(txt, (px + 10, y))
        y += 24

        txt = FONT_MED.render(f"我方 VP: {game_state.player_vp}  敌方 VP: {game_state.ai_vp}", True, GREEN)
        self.screen.blit(txt, (px + 10, y))
        y += 28

        y += 8
        pygame.draw.line(self.screen, GRAY, (px + 5, y), (px + self.panel_width - 5, y), 1)
        y += 10

        if game_state.selected_unit and game_state.selected_unit in game_state.units:
            u = game_state.units[game_state.selected_unit]
            txt = FONT_BOLD.render(u.name, True, YELLOW)
            self.screen.blit(txt, (px + 10, y))
            y += 26
            cn = NATION_NAMES.get(u.nation, u.nation)
            moved = "已移动" if u.moved_this_turn else "可移动"
            fought = "已攻击" if u.attacked_this_turn else "可攻击"
            lines = [
                f"攻击: {u.attack_power}  防御: {u.defense_power}",
                f"移动: {u.movement_points}  兵力: {u.current_steps}/{u.max_steps}",
                f"国籍: {cn}",
                f"状态: {moved} / {fought}",
            ]
            for line in lines:
                txt = FONT_SMALL.render(line, True, TEXT_COLOR)
                self.screen.blit(txt, (px + 10, y))
                y += 16
        else:
            txt = FONT_SMALL.render("点击己方单位以选择", True, GRAY)
            self.screen.blit(txt, (px + 10, y))
            y += 10
            txt = FONT_SMALL.render("左键移动 / 左键攻击", True, GRAY)
            self.screen.blit(txt, (px + 10, y))
            y += 16

        y += 10
        pygame.draw.line(self.screen, GRAY, (px + 5, y), (px + self.panel_width - 5, y), 1)
        y += 10
        txt = FONT_SMALL.render("战斗记录:", True, YELLOW)
        self.screen.blit(txt, (px + 10, y))
        y += 16
        for entry in game_state.combat_log[-8:]:
            txt = FONT_SMALL.render(entry[:40], True, TEXT_COLOR)
            self.screen.blit(txt, (px + 10, y))
            y += 14

        y = sh - 85
        self._draw_button(px + 20, y, self.panel_width - 40, 32, "结束回合 (AI行动)", game_state)
        y += 38
        self._draw_button(px + 20, y, self.panel_width - 40, 32, "返回主菜单", game_state)

        # Deselect button when unit selected
        if game_state.selected_unit:
            y += 40
            self._draw_button(px + 60, y, self.panel_width - 120, 26, "取消选择", game_state)

    def _draw_button(self, x, y, w, h, text, game_state):
        rect = pygame.Rect(x, y, w, h)
        mouse_pos = pygame.mouse.get_pos()
        if rect.collidepoint(mouse_pos):
            pygame.draw.rect(self.screen, BUTTON_HOVER, rect, border_radius=4)
        else:
            pygame.draw.rect(self.screen, BUTTON_BG, rect, border_radius=4)
        txt = FONT_SMALL.render(text, True, WHITE)
        txt_x = x + (w - txt.get_width()) // 2
        txt_y = y + (h - txt.get_height()) // 2
        self.screen.blit(txt, (txt_x, txt_y))
        return rect

    def get_button_rects(self, game_state):
        sw = self.screen.get_width()
        sh = self.screen.get_height()
        px = sw - self.panel_width
        py = sh - 85
        buttons = {
            "end_turn_btn": pygame.Rect(px + 20, py, self.panel_width - 40, 32),
            "new_game": pygame.Rect(px + 20, py + 38, self.panel_width - 40, 32),
        }
        if game_state.selected_unit:
            buttons["deselect"] = pygame.Rect(px + 60, py + 80, self.panel_width - 120, 26)
        return buttons
