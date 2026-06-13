import random

RESULT_NAMES = {
    "DE": "防御方被歼灭",
    "DR": "防御方撤退",
    "EX": "双方各损一步",
    "AR": "进攻方撤退",
    "AE": "进攻方被歼灭",
}

NATION_NAMES = {
    "germany": "德国",
    "ussr": "苏联",
    "usa": "美国",
    "uk": "英国",
    "france": "法国",
    "japan": "日本",
    "china": "中国",
}


def resolve_combat(attacker, defender, terrain_bonus, encirclement_bonus=0):
    raw_ratio = attacker.attack_power / max(1, defender.defense_power + terrain_bonus)
    roll = random.randint(1, 6)
    roll += encirclement_bonus
    roll = max(1, min(6, roll))

    if raw_ratio >= 3.0:
        if roll >= 3:
            return ("DE", 0, defender.current_steps, False)
        else:
            return ("DR", 0, 0, True)
    elif raw_ratio >= 2.0:
        if roll >= 5:
            return ("DE", 0, defender.current_steps, False)
        elif roll >= 2:
            return ("DR", 0, 0, True)
        else:
            return ("EX", 1, 1, False)
    elif raw_ratio >= 1.0:
        if roll >= 5:
            return ("DR", 0, 0, True)
        elif roll >= 2:
            return ("EX", 1, 1, False)
        else:
            return ("AR", 0, 0, True)
    elif raw_ratio >= 0.5:
        if roll >= 5:
            return ("EX", 1, 1, False)
        elif roll >= 2:
            return ("AR", 0, 0, True)
        else:
            return ("AE", attacker.current_steps, 0, False)
    else:
        if roll >= 5:
            return ("AR", 0, 0, True)
        else:
            return ("AE", attacker.current_steps, 0, False)
