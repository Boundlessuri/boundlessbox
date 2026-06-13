import json
from ..data_path import get_units_path

_unit_cache = None

def load_unit_stats():
    global _unit_cache
    if _unit_cache is None:
        with open(get_units_path(), "r", encoding="utf-8") as f:
            _unit_cache = json.load(f)
    return _unit_cache

def get_unit_stats(nation, unit_type):
    return load_unit_stats()[nation][unit_type]
