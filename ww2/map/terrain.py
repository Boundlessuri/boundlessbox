from enum import Enum

class Terrain(Enum):
    PLAINS = 0
    FOREST = 1
    HILLS = 2
    MOUNTAIN = 3
    CITY = 4
    SEA = 5
    RIVER = 6

MOVEMENT_COST = {
    Terrain.PLAINS: 1,
    Terrain.FOREST: 2,
    Terrain.HILLS: 2,
    Terrain.MOUNTAIN: 3,
    Terrain.CITY: 1,
    Terrain.SEA: 99,
    Terrain.RIVER: 99,
}

DEFENSE_BONUS = {
    Terrain.PLAINS: 0,
    Terrain.FOREST: 1,
    Terrain.HILLS: 2,
    Terrain.MOUNTAIN: 3,
    Terrain.CITY: 3,
    Terrain.SEA: 0,
    Terrain.RIVER: 0,
}

TERRAIN_COLORS = {
    Terrain.PLAINS: (180, 200, 140),
    Terrain.FOREST: (60, 120, 50),
    Terrain.HILLS: (160, 140, 100),
    Terrain.MOUNTAIN: (130, 120, 110),
    Terrain.CITY: (180, 160, 140),
    Terrain.SEA: (50, 80, 180),
    Terrain.RIVER: (70, 120, 200),
}
