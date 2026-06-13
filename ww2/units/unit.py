class Unit:
    __slots__ = ('unit_id', 'nation', 'unit_type', 'attack', 'defense',
                 'movement', 'max_steps', 'current_steps', 'hex_pos',
                 'moved_this_turn', 'attacked_this_turn', 'name')

    def __init__(self, unit_id, nation, unit_type, stats, hex_pos):
        self.unit_id = unit_id
        self.nation = nation
        self.unit_type = unit_type
        self.name = stats["name"]
        self.attack = stats["attack"]
        self.defense = stats["defense"]
        self.movement = stats["movement"]
        self.max_steps = stats["steps"]
        self.current_steps = stats["steps"]
        self.hex_pos = hex_pos
        self.moved_this_turn = False
        self.attacked_this_turn = False

    @property
    def is_alive(self):
        return self.current_steps > 0

    @property
    def attack_power(self):
        return self.attack * self.current_steps // self.max_steps

    @property
    def defense_power(self):
        return self.defense * self.current_steps // self.max_steps

    @property
    def movement_points(self):
        return max(1, self.movement * self.current_steps // self.max_steps)

    def take_loss(self):
        self.current_steps -= 1

    def reset_turn(self):
        self.moved_this_turn = False
        self.attacked_this_turn = False

    def __repr__(self):
        return f"{self.nation}:{self.name}#{self.unit_id}@{self.hex_pos}"
