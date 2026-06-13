import pygame
from ..map.hex_grid import Hex
from ..game.turn import get_valid_moves, get_attack_targets, execute_attack


class InputHandler:
    def __init__(self, renderer):
        self.renderer = renderer

    def handle_event(self, event, game_state):
        buttons = self.renderer.get_button_rects(game_state)

        if event.type == pygame.MOUSEBUTTONDOWN:
            return self._on_click(event.pos, event.button, buttons, game_state)

        if event.type == pygame.MOUSEMOTION:
            if self.renderer.dragging:
                mx, my = event.pos
                dx = mx - self.renderer.drag_start[0]
                dy = my - self.renderer.drag_start[1]
                self.renderer.map_offset_x = self.renderer.drag_offset_start[0] + dx
                self.renderer.map_offset_y = self.renderer.drag_offset_start[1] + dy

        if event.type == pygame.MOUSEBUTTONUP:
            self.renderer.dragging = False

        return None

    def _on_click(self, pos, button, btn_rects, game_state):
        px, py = pos

        if btn_rects.get("help_btn") and btn_rects["help_btn"].collidepoint(px, py):
            return "show_help"
        if btn_rects["end_turn_btn"].collidepoint(px, py):
            return self._end_turn(game_state)
        if btn_rects["new_game"].collidepoint(px, py):
            return "new_game"
        if "deselect" in btn_rects and btn_rects["deselect"].collidepoint(px, py):
            game_state.selected_unit = None
            self.renderer.move_hexes.clear()
            self.renderer.attack_hexes.clear()
            return "deselect"

        panel_x = self.renderer.screen.get_width() - self.renderer.panel_width
        if px >= panel_x:
            return None

        if button == 1:
            return self._left_click_map(pos, game_state)
        elif button == 3:
            self.renderer.dragging = True
            self.renderer.drag_start = pos
            self.renderer.drag_offset_start = (self.renderer.map_offset_x,
                                                self.renderer.map_offset_y)
        return None

    def _left_click_map(self, pos, game_state):
        wx, wy = self.renderer.screen_to_world(*pos)
        clicked_hex = game_state.map.pixel_to_hex(wx, wy)

        if not game_state.map.in_bounds(clicked_hex):
            return None

        pos_key = (clicked_hex.q, clicked_hex.r)
        clicked_unit = game_state.get_unit_at(pos_key)
        selected_unit = game_state.units.get(game_state.selected_unit) if game_state.selected_unit else None

        if game_state.current_player != "player":
            return None

        # Case 1: Unit selected, clicked a valid move hex → move
        if selected_unit and pos_key in self.renderer.move_hexes:
            game_state.move_unit(game_state.selected_unit, clicked_hex)
            # After moving, show attack range for this unit
            self.renderer.move_hexes.clear()
            self._update_attack_range(game_state)
            return "moved"

        # Case 2: Unit selected, clicked a valid attack target → attack
        if selected_unit and pos_key in self.renderer.attack_hexes:
            if clicked_unit and not game_state._is_player_side(clicked_unit.nation):
                desc = execute_attack(selected_unit.unit_id, clicked_unit.unit_id, game_state)
                self.renderer.move_hexes.clear()
                self.renderer.attack_hexes.clear()
                game_state.selected_unit = None
                return f"combat: {desc}"

        # Case 3: Clicked own unit → select it (or switch to it)
        if clicked_unit and game_state._is_player_side(clicked_unit.nation):
            game_state.selected_unit = clicked_unit.unit_id
            self._update_ranges(game_state)
            return "selected"

        # Case 4: Clicked empty/enemy hex → deselect
        game_state.selected_unit = None
        self.renderer.move_hexes.clear()
        self.renderer.attack_hexes.clear()
        return None

    def _update_ranges(self, game_state):
        """Show move range and attack targets for selected unit."""
        unit = game_state.units.get(game_state.selected_unit)
        if not unit:
            return
        if not unit.moved_this_turn:
            self.renderer.move_hexes = get_valid_moves(unit, game_state.map, game_state.unit_at_hex)
        else:
            self.renderer.move_hexes.clear()

        if not unit.attacked_this_turn:
            self._update_attack_range(game_state)
        else:
            self.renderer.attack_hexes.clear()

    def _update_attack_range(self, game_state):
        unit = game_state.units.get(game_state.selected_unit)
        if unit and not unit.attacked_this_turn:
            targets = get_attack_targets(unit, game_state)
            self.renderer.attack_hexes = {t.hex_pos for t in targets}
        else:
            self.renderer.attack_hexes.clear()

    def _end_turn(self, game_state):
        from ..ai.ai_player import ai_turn
        if game_state.current_player == "player":
            game_state.current_player = "ai"
            game_state.selected_unit = None
            self.renderer.move_hexes.clear()
            self.renderer.attack_hexes.clear()
            ai_turn(game_state)
            game_state.current_player = "player"
            game_state.check_victory()
            if game_state.is_game_over():
                return "game_over"
            game_state.start_turn()
            return "turn_ended"
        return None
