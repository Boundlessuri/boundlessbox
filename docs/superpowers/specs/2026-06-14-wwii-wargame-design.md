# WWII Wargame Design Spec

## Overview
Turn-based hex-grid operational wargame. 7 nations, division/corps scale, 4 historical scenarios. Single-player vs AI.

## Tech Stack
- Python 3 + pygame + PyInstaller (single .exe, <150MB)

## Nations & Units
| Nation | Level | Trait |
|--------|-------|-------|
| Germany | Division | Strong armor, late-war supply penalty |
| USSR | Corps | Numerous but weaker per-unit |
| USA | Division | Balanced, strong artillery/air |
| UK | Division | Solid infantry, average armor |
| France | Division | 1940 equipment deficit, defensive |
| Japan | Division | Tenacious infantry, weak armor |
| China | Corps | Large numbers, poor equipment, guerrilla |

## Core Mechanics
- Hex grid map, IGO-UGO turns (move then combat)
- 4 scenarios: France 1940, Barbarossa 1941, Normandy 1944, Pacific 1942
- Unit stats: movement points, attack, defense, morale
- Terrain: forest/city defense bonus, river movement penalty, road bonus
- Supply: units trace to supply source (map edge or city) within N hexes
- Weather: clear/rain/snow affecting movement and air support

## Combat
- Attack-defense ratio determines result: destroy/retreat/hold/counterattack
- 1d6 + modifiers (terrain, encirclement, air, commander)
- Encirclement: adjacent friendly units add combat bonus

## Architecture
- `ww2/` root package
  - `main.py` — entry, game loop
  - `game/` — Game, Turn, state machine
  - `map/` — hex grid, terrain, pathfinding
  - `units/` — unit types, stats, combat resolution
  - `ai/` — simple AI (defend objectives, attack weak units)
  - `ui/` — pygame rendering, input handling
  - `data/` — scenario JSONs, unit stats, map data
  - `build.py` — PyInstaller build script

## Scenarios (embedded JSON)
1. **France 1940** — Germany vs France/UK, 20x15 hex map
2. **Barbarossa 1941** — Germany vs USSR, 30x25 hex map
3. **Normandy 1944** — USA/UK vs Germany, 20x20 hex map
4. **Pacific 1942** — Japan vs USA/China, 25x20 hex map

## Size Budget
- Python + pygame + PyInstaller base: ~30MB
- Graphics (hex tiles, unit counters, UI): ~10MB
- Audio (simple sound effects): ~5MB
- Total target: <150MB (well under 800MB limit)

## Scope Limits (YAGNI)
- NO multiplayer/networking
- NO scenario editor
- NO campaign mode (linked scenarios)
- NO historical commanders with portraits
- NO animation beyond simple movement
- NO fog of war (keeps AI simpler)
- NO research/production (fixed OOB per scenario)
