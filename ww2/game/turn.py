from ..map.hex_grid import Hex
from ..map.terrain import Terrain
from ..units.combat import resolve_combat, RESULT_NAMES
import random


def _same_side(unit_a, unit_b, game_state):
    """True if both units are on the same side."""
    a_player = game_state._is_player_side(unit_a.nation)
    b_player = game_state._is_player_side(unit_b.nation)
    a_ai = game_state._is_ai_side(unit_a.nation)
    b_ai = game_state._is_ai_side(unit_b.nation)
    return (a_player and b_player) or (a_ai and b_ai)


def get_valid_moves(unit, game_map, unit_at_hex):
    """Return set of (q,r) reachable within movement_points."""
    from collections import deque
    start = Hex(*unit.hex_pos)
    mp = unit.movement_points
    visited = {unit.hex_pos: 0}
    queue = deque([(start, 0)])
    reachable = set()

    while queue:
        h, cost = queue.popleft()
        for nb in h.neighbors():
            if not game_map.in_bounds(nb):
                continue
            pos = (nb.q, nb.r)
            terrain = game_map.terrain.get(pos, 0)
            if terrain in (5,):
                continue
            if pos in unit_at_hex and pos != unit.hex_pos:
                continue
            move_cost = game_map.movement_cost(nb)
            new_cost = cost + move_cost
            if new_cost <= mp:
                if pos not in visited or new_cost < visited[pos]:
                    visited[pos] = new_cost
                    queue.append((nb, new_cost))
                    reachable.add(pos)
    return reachable


def get_attack_targets(unit, game_state):
    """Return list of adjacent enemy units (opposite side)."""
    h = Hex(*unit.hex_pos)
    targets = []
    for nb in h.neighbors():
        pos = (nb.q, nb.r)
        target = game_state.get_unit_at(pos)
        if target and not _same_side(unit, target, game_state):
            targets.append(target)
    return targets


def get_encirclement_bonus(attacker, defender, game_state):
    """+1 if defender has >=4 adjacent hexes occupied/cutoff by attacker's side."""
    dh = Hex(*defender.hex_pos)
    count = 0
    for nb in dh.neighbors():
        pos = (nb.q, nb.r)
        if not game_state.map.in_bounds(nb):
            count += 1
        elif game_state.map.terrain.get(pos, 0) == 5:
            count += 1
        else:
            u = game_state.get_unit_at(pos)
            if u and _same_side(u, attacker, game_state):
                count += 1
    return 1 if count >= 4 else 0


def find_retreat_hex(unit, game_state):
    """Find a hex to retreat to, preferring away from enemies."""
    h = Hex(*unit.hex_pos)
    enemies = []
    for nb in h.neighbors():
        u = game_state.get_unit_at((nb.q, nb.r))
        if u and not _same_side(u, unit, game_state):
            enemies.append(nb)

    candidates = []
    for nb in h.neighbors():
        pos = (nb.q, nb.r)
        if not game_state.map.is_passable(nb):
            continue
        if pos in game_state.unit_at_hex:
            continue
        is_safe = True
        for en in enemies:
            if nb.distance(en) <= 1:
                is_safe = False
                break
        candidates.append((pos, is_safe))

    if not candidates:
        return None

    candidates.sort(key=lambda x: (not x[1], random.random()))
    return candidates[0][0]


def execute_attack(attacker_id, defender_id, game_state):
    """Execute one combat and apply results. Returns result description string."""
    attacker = game_state.units[attacker_id]
    defender = game_state.units[defender_id]

    terrain_bonus = game_state.map.defense_bonus(Hex(*defender.hex_pos))
    encirclement = get_encirclement_bonus(attacker, defender, game_state)

    result_name, a_loss, d_loss, retreat = resolve_combat(
        attacker, defender, terrain_bonus, encirclement)

    attacker.attacked_this_turn = True

    result_cn = RESULT_NAMES.get(result_name, result_name)
    desc = f"{attacker.name} 攻击 {defender.name}: {result_cn}"

    for _ in range(a_loss):
        if attacker.current_steps > 0:
            attacker.take_loss()
    for _ in range(d_loss):
        if defender.current_steps > 0:
            defender.take_loss()

    if retreat:
        if result_name in ("AR",):
            retreat_pos = find_retreat_hex(attacker, game_state)
            if retreat_pos:
                old = attacker.hex_pos
                del game_state.unit_at_hex[old]
                attacker.hex_pos = retreat_pos
                game_state.unit_at_hex[retreat_pos] = attacker.unit_id
                desc += " (进攻方撤退)"
            else:
                desc += " (无法撤退: 进攻方被歼灭)"
                attacker.current_steps = 0
        else:
            retreat_pos = find_retreat_hex(defender, game_state)
            if retreat_pos:
                old = defender.hex_pos
                del game_state.unit_at_hex[old]
                defender.hex_pos = retreat_pos
                game_state.unit_at_hex[retreat_pos] = defender.unit_id
                desc += " (防御方撤退)"
            else:
                desc += " (无法撤退: 防御方被歼灭)"
                defender.current_steps = 0

    to_remove = [uid for uid, u in game_state.units.items() if not u.is_alive]
    for uid in to_remove:
        u = game_state.units[uid]
        pos = u.hex_pos
        if game_state.unit_at_hex.get(pos) == uid:
            del game_state.unit_at_hex[pos]
        del game_state.units[uid]

    game_state.combat_log.append(desc)
    return desc
