import math

SQRT3 = math.sqrt(3)

class Hex:
    __slots__ = ('q', 'r')

    def __init__(self, q, r):
        self.q = q
        self.r = r

    def __eq__(self, other):
        return isinstance(other, Hex) and self.q == other.q and self.r == other.r

    def __hash__(self):
        return hash((self.q, self.r))

    def __repr__(self):
        return f"Hex({self.q},{self.r})"

    def neighbor(self, direction):
        """0=E,1=NE,2=NW,3=W,4=SW,5=SE"""
        offsets = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
        dq, dr = offsets[direction]
        return Hex(self.q + dq, self.r + dr)

    def neighbors(self):
        return [self.neighbor(d) for d in range(6)]

    def distance(self, other):
        dq = self.q - other.q
        dr = self.r - other.r
        return (abs(dq) + abs(dr) + abs(dq + dr)) // 2


class HexMap:
    def __init__(self, cols, rows, hex_size=22):
        self.cols = cols
        self.rows = rows
        self.hex_size = hex_size
        self.terrain = {}
        self.hexes = {}
        for q in range(cols):
            for r in range(rows):
                h = Hex(q, r)
                self.hexes[(q, r)] = h
                self.terrain[(q, r)] = 0  # plains default

    def in_bounds(self, hex_obj):
        return 0 <= hex_obj.q < self.cols and 0 <= hex_obj.r < self.rows

    def hex_to_pixel(self, hex_obj):
        s = self.hex_size
        x = s * (SQRT3 * hex_obj.q + SQRT3 / 2 * hex_obj.r)
        y = s * (1.5 * hex_obj.r)
        return (x, y)

    def pixel_to_hex(self, px, py):
        s = self.hex_size
        q = (SQRT3 / 3 * px - 1.0 / 3 * py) / s
        r = (2.0 / 3 * py) / s
        return self._hex_round(q, r)

    def _hex_round(self, q_frac, r_frac):
        s_frac = -q_frac - r_frac
        qi = round(q_frac)
        ri = round(r_frac)
        si = round(s_frac)
        q_diff = abs(qi - q_frac)
        r_diff = abs(ri - r_frac)
        s_diff = abs(si - s_frac)
        if q_diff > r_diff and q_diff > s_diff:
            qi = -ri - si
        elif r_diff > s_diff:
            ri = -qi - si
        return Hex(int(qi), int(ri))

    def hex_corners(self, hex_obj):
        s = self.hex_size
        cx, cy = self.hex_to_pixel(hex_obj)
        corners = []
        for i in range(6):
            angle = math.pi / 180 * (60 * i - 30)
            corners.append((cx + s * math.cos(angle), cy + s * math.sin(angle)))
        return corners

    def movement_cost(self, hex_obj):
        t = self.terrain.get((hex_obj.q, hex_obj.r), 0)
        from .terrain import Terrain, MOVEMENT_COST
        return MOVEMENT_COST.get(Terrain(t), 99)

    def defense_bonus(self, hex_obj):
        t = self.terrain.get((hex_obj.q, hex_obj.r), 0)
        from .terrain import Terrain, DEFENSE_BONUS
        return DEFENSE_BONUS.get(Terrain(t), 0)

    def is_passable(self, hex_obj):
        if not self.in_bounds(hex_obj):
            return False
        t = self.terrain.get((hex_obj.q, hex_obj.r), 0)
        return t not in (5, 6)  # not sea or river
