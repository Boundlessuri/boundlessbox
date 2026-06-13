"""H2H 加权预测模型"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data.collector import (
    load_h2h_database, find_h2h_matches, compute_weight,
    COMPETITION_WEIGHTS
)

def h2h_goal_expectation(team, opponent, database, home_advantage=1.0, recent_n=10):
    matches = find_h2h_matches(team, opponent, database)[:recent_n]
    if not matches:
        return {"expected_goals": None, "sample_size": 0, "weighted_goals": 0}
    total_weight = 0
    weighted_goals = 0
    for m in matches:
        w = compute_weight(m)
        total_weight += w
        if m["home_team"] == team:
            weighted_goals += m["home_score"] * w
        else:
            weighted_goals += m["away_score"] * w
    if total_weight == 0:
        return {"expected_goals": 0, "sample_size": len(matches), "weighted_goals": 0}
    expected = (weighted_goals / total_weight) * home_advantage
    return {"expected_goals": round(expected, 2), "sample_size": len(matches), "weighted_goals": round(weighted_goals, 4)}

def h2h_win_rate(team_a, team_b, database, recent_n=10):
    matches = find_h2h_matches(team_a, team_b, database)[:recent_n]
    if not matches:
        return {"wins": 0, "draws": 0, "losses": 0, "total": 0, "win_rate": 0.5}
    wins = draws = losses = 0
    for m in matches:
        if m["home_team"] == team_a:
            if m["home_score"] > m["away_score"]: wins += 1
            elif m["home_score"] == m["away_score"]: draws += 1
            else: losses += 1
        else:
            if m["away_score"] > m["home_score"]: wins += 1
            elif m["away_score"] == m["home_score"]: draws += 1
            else: losses += 1
    total = wins + draws + losses
    return {"wins": wins, "draws": draws, "losses": losses, "total": total,
            "win_rate": round(wins / total, 3) if total > 0 else 0.5}

def _generic_attack_strength(team, database):
    goals = 0
    count = 0
    for m in database:
        if m["home_team"] == team:
            goals += m["home_score"]; count += 1
        elif m["away_team"] == team:
            goals += m["away_score"]; count += 1
    if count == 0:
        return 1.2
    return round(goals / count, 2)

def h2h_predict(home_team, away_team, database, venue_neutral=True):
    home_adv = 1.0 if venue_neutral else 1.15
    away_adv = 1.0 if venue_neutral else 0.85
    home_exp = h2h_goal_expectation(home_team, away_team, database, home_adv)
    away_exp = h2h_goal_expectation(away_team, home_team, database, away_adv)
    record = h2h_win_rate(home_team, away_team, database)
    if home_exp["sample_size"] == 0:
        home_exp["expected_goals"] = _generic_attack_strength(home_team, database)
    if away_exp["sample_size"] == 0:
        away_exp["expected_goals"] = _generic_attack_strength(away_team, database)
    h2h_bonus = 1 + (record["win_rate"] - 0.5) * 0.3
    return {"home_score": round(home_exp["expected_goals"] * h2h_bonus, 2),
            "away_score": round(away_exp["expected_goals"] / max(h2h_bonus, 0.01), 2),
            "h2h_record": record,
            "match_count": max(home_exp["sample_size"], away_exp["sample_size"]),
            "model": "h2h"}
