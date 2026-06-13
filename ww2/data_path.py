import os
import sys


def get_data_dir():
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "ww2", "data")
    else:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def get_scenario_path(name):
    return os.path.join(get_data_dir(), "scenarios", f"{name}.json")


def get_units_path():
    return os.path.join(get_data_dir(), "units.json")
