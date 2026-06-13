import random
from ..map.hex_grid import Hex
from ..game.turn import get_valid_moves, get_attack_targets, execute_attack


def ai_turn(game_state):
    """Execute AI turn: move toward objectives, then attack weak targets."""
    ai_units = [u for u in game_state.units.values()
                if game_state._is_ai_side(u.nation) and u.is_alive]

    vp_positions = list(game_state.victory_points.keys())

    for unit in ai_units:
        if unit.moved_this_turn:
            continue
        reachable = get_valid_moves(unit, game_state.map, game_state.unit_at_hex)
        if not reachable:
            continue

        target_pos = None
        best_dist = 999

        if vp_positions:
            for vp_pos in vp_positions:
                current = game_state.get_unit_at(vp_pos)
                if current and game_state._is_ai_side(current.nation):
                    continue
                vph = Hex(*vp_pos)
                for rp in reachable:
                    d = Hex(*rp).distance(vph)
                    if d < best_dist:
                        best_dist = d
                        target_pos = rp

        if target_pos is None:
            for pu in game_state.units.values():
                if not game_state._is_player_side(pu.nation) or not pu.is_alive:
                    continue
                ph = Hex(*pu.hex_pos)
                for rp in reachable:
                    d = Hex(*rp).distance(ph)
                    if d < best_dist:
                        best_dist = d
                        target_pos = rp

        if target_pos and target_pos != unit.hex_pos:
            game_state.move_unit(unit.unit_id, Hex(*target_pos))

    ai_units = [u for u in game_state.units.values()
                if game_state._is_ai_side(u.nation) and u.is_alive
                and not u.attacked_this_turn]

    for unit in ai_units:
        targets = get_attack_targets(unit, game_state)
        if not targets:
            continue

        best_target = None
        best_score = 999
        for t in targets:
            terrain_bonus = game_state.map.defense_bonus(Hex(*t.hex_pos))
            odds = t.defense_power + terrain_bonus
            if odds < best_score:
                best_score = odds
                best_target = t

        if best_target:
            execute_attack(unit.unit_id, best_target.unit_id, game_state)
