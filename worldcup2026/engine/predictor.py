"""融合预测器 — H2H + Elo"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from engine.h2h_model import h2h_predict
from engine.elo_model import elo_predict
from data.collector import load_h2h_database

class Predictor:
    def __init__(self, mode="hybrid", h2h_weight=0.5):
        self.mode = mode
        self.h2h_weight = h2h_weight
        self.database = load_h2h_database()
        self._cache = {}

    def predict(self, home_team, away_team, venue_neutral=True):
        cache_key = (home_team, away_team, venue_neutral)
        if cache_key in self._cache:
            return self._cache[cache_key]

        if self.mode == "h2h":
            result = h2h_predict(home_team, away_team, self.database, venue_neutral)
        elif self.mode == "elo":
            result = elo_predict(home_team, away_team, venue_neutral)
        else:
            h2h_result = h2h_predict(home_team, away_team, self.database, venue_neutral)
            elo_result = elo_predict(home_team, away_team, venue_neutral)
            w = self.h2h_weight
            result = {
                "home_score": round(h2h_result["home_score"] * w + elo_result["home_score"] * (1 - w), 2),
                "away_score": round(h2h_result["away_score"] * w + elo_result["away_score"] * (1 - w), 2),
                "h2h_home": h2h_result["home_score"], "h2h_away": h2h_result["away_score"],
                "elo_home": elo_result["home_score"], "elo_away": elo_result["away_score"],
                "h2h_record": h2h_result.get("h2h_record"),
                "match_count": h2h_result.get("match_count", 0),
                "top_probs": elo_result.get("top_probs", []),
                "model": "hybrid"
            }

        self._cache[cache_key] = result
        return result

    def set_mode(self, mode, h2h_weight=0.5):
        self.mode = mode
        self.h2h_weight = h2h_weight
        self._cache.clear()

    def predict_all_group_matches(self, group_data):
        results = {}
        for group_name, group in group_data["groups"].items():
            results[group_name] = []
            for match in group["matches"]:
                pred = self.predict(match["home"], match["away"], venue_neutral=True)
                results[group_name].append({"match": match, "prediction": pred})
        return results
