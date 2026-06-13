import json
from ..map.hex_grid import HexMap
from ..units.unit import Unit
from ..units.stats import get_unit_stats
from ..data_path import get_scenario_path


class GameState:
    def __init__(self):
        self.map = None
        self.units = {}
        self.unit_at_hex = {}
        self.current_player = "player"
        self.turn_number = 0
        self.phase = "movement"
        self.selected_unit = None
        self.scenario_name = ""
        self.player_nation = ""
        self.ai_nation = ""
        self.player_allies = []
        self.ai_allies = []
        self.player_has_air = True
        self.ai_has_air = False
        self.victory_points = {}
        self.max_turns = 12
        self.player_vp = 0
        self.ai_vp = 0
        self.combat_log = []

    def _is_player_side(self, nation):
        return nation == self.player_nation or nation in self.player_allies

    def _is_ai_side(self, nation):
        return nation == self.ai_nation or nation in self.ai_allies

    def load_scenario(self, name):
        path = get_scenario_path(name)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.scenario_name = data["name"]
        self.player_nation = data["player_nation"]
        self.ai_nation = data["ai_nation"]
        self.player_allies = data.get("player_allies", [])
        self.ai_allies = data.get("ai_allies", [])
        self.player_has_air = data.get("player_air", True)
        self.ai_has_air = data.get("ai_air", False)
        self.max_turns = data.get("max_turns", 12)

        cols = data["map"]["cols"]
        rows = data["map"]["rows"]
        self.map = HexMap(cols, rows, hex_size=data["map"].get("hex_size", 22))
        self.victory_points = {}

        for tdata in data["map"]["terrain"]:
            q, r, terrain = tdata["q"], tdata["r"], tdata["t"]
            self.map.terrain[(q, r)] = terrain
            if tdata.get("vp", 0) > 0:
                self.victory_points[(q, r)] = {"value": tdata["vp"], "owner": None}

        self.units = {}
        self.unit_at_hex = {}
        uid = 0
        for udata in data["units"]:
            stats = get_unit_stats(udata["nation"], udata["type"])
            unit = Unit(uid, udata["nation"], udata["type"], stats,
                       (udata["q"], udata["r"]))
            self.units[uid] = unit
            self.unit_at_hex[(udata["q"], udata["r"])] = uid
            uid += 1

        self.turn_number = 0
        self.current_player = "player"
        self.phase = "movement"
        self.selected_unit = None
        self.combat_log = []

    def get_unit_at(self, hex_pos):
        return self.units.get(self.unit_at_hex.get(hex_pos, -1))

    def move_unit(self, unit_id, target_hex):
        unit = self.units[unit_id]
        old_pos = unit.hex_pos
        del self.unit_at_hex[old_pos]
        unit.hex_pos = (target_hex.q, target_hex.r)
        unit.moved_this_turn = True
        self.unit_at_hex[(target_hex.q, target_hex.r)] = unit_id

    def start_turn(self):
        self.turn_number += 1
        self.current_player = "player"
        self.phase = "movement"
        self.combat_log = []
        for u in self.units.values():
            u.reset_turn()

    def check_victory(self):
        p_vp = 0
        a_vp = 0
        for pos, vp_data in self.victory_points.items():
            unit = self.get_unit_at(pos)
            if unit:
                if self._is_player_side(unit.nation):
                    p_vp += vp_data["value"]
                elif self._is_ai_side(unit.nation):
                    a_vp += vp_data["value"]
        self.player_vp = p_vp
        self.ai_vp = a_vp

    def is_game_over(self):
        if self.turn_number >= self.max_turns:
            return True
        has_player = any(self._is_player_side(u.nation) and u.is_alive
                        for u in self.units.values())
        has_ai = any(self._is_ai_side(u.nation) and u.is_alive
                    for u in self.units.values())
        return not has_player or not has_ai
