"""Elo + 泊松分布预测模型"""

import json, math, os

LEAGUE_AVG_GOALS = 1.5
HOME_ADV_ELO = 100
K_FACTOR = 40

def load_elo_ratings(path=None):
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "..", "data", "elo_ratings.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["teams"]

def expected_result(elo_a, elo_b):
    return 1.0 / (1.0 + math.pow(10, (elo_b - elo_a) / 400))

def update_elo(elo_winner, elo_loser, goal_diff, is_draw=False):
    exp = expected_result(elo_winner, elo_loser)
    actual = 0.5 if is_draw else 1.0
    delta = K_FACTOR * (actual - exp)
    if not is_draw:
        delta += K_FACTOR * math.log2(goal_diff + 1) * 0.1
    return round(elo_winner + delta, 1), round(elo_loser - delta, 1)

def elo_to_expected_goals(elo_home, elo_away, venue_neutral=True):
    gamma = 0 if venue_neutral else HOME_ADV_ELO
    delta = elo_home - elo_away
    lambda_h = LEAGUE_AVG_GOALS * math.exp((delta - gamma) / 400)
    lambda_a = LEAGUE_AVG_GOALS * math.exp((-delta + gamma) / 400)
    return round(lambda_h, 3), round(lambda_a, 3)

def poisson_probability(lmbda, k):
    if lmbda <= 0:
        return 1.0 if k == 0 else 0.0
    return (lmbda ** k) * math.exp(-lmbda) / math.factorial(k)

def score_probabilities(lambda_h, lambda_a, max_goals=8):
    probs = []
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            p = poisson_probability(lambda_h, h) * poisson_probability(lambda_a, a)
            if p > 0.001:
                probs.append({"home": h, "away": a, "prob": round(p, 4)})
    probs.sort(key=lambda x: x["prob"], reverse=True)
    return probs[:10]

def elo_predict(home_team, away_team, venue_neutral=True):
    ratings = load_elo_ratings()
    elo_home = ratings.get(home_team, 2000)
    elo_away = ratings.get(away_team, 2000)
    lambda_h, lambda_a = elo_to_expected_goals(elo_home, elo_away, venue_neutral)
    top_probs = score_probabilities(lambda_h, lambda_a)
    expected_h = sum(p["home"] * p["prob"] for p in top_probs)
    expected_a = sum(p["away"] * p["prob"] for p in top_probs)
    total_prob = sum(p["prob"] for p in top_probs)
    if total_prob > 0:
        expected_h /= total_prob; expected_a /= total_prob
    return {"home_score": round(expected_h, 2), "away_score": round(expected_a, 2),
            "elo_home": elo_home, "elo_away": elo_away,
            "top_probs": top_probs, "model": "elo"}
