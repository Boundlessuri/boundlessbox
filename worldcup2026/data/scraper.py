"""淘汰赛赛程爬虫 — ESPN/FIFA 双源 + fallback"""

import json, os, requests
from bs4 import BeautifulSoup

ESPN_URL = "https://www.espn.com/soccer/league/_/name/fifa.world"
FIFA_URL = "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026"
FALLBACK_FILE = "knockout_fallback.json"

def _headers():
    return {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def scrape_espn_knockout():
    try:
        resp = requests.get(ESPN_URL, headers=_headers(), timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        matches = []
        for el in soup.select("[data-stage='knockout'], .bracket-match, .knockout-match"):
            home = el.select_one(".team-home .team-name, [data-home] .team-name")
            away = el.select_one(".team-away .team-name, [data-away] .team-name")
            date_el = el.select_one(".match-date, .date")
            stage_el = el.select_one(".match-stage, .stage")
            if home and away:
                matches.append({"home_team": home.text.strip(), "away_team": away.text.strip(),
                                "date": date_el.text.strip() if date_el else "TBD",
                                "stage": stage_el.text.strip() if stage_el else "knockout",
                                "venue": "TBD", "source": "espn.com"})
        return matches
    except Exception as e:
        print(f"ESPN爬取失败: {e}")
        return []

def scrape_fifa_knockout():
    try:
        resp = requests.get(FIFA_URL, headers=_headers(), timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        matches = []
        for el in soup.select("[data-role='match'], .fi-match, .match-card"):
            home = el.select_one("[data-role='home'] .fi-team-name, .home-team")
            away = el.select_one("[data-role='away'] .fi-team-name, .away-team")
            date_el = el.select_one("[data-role='date'], .match-date")
            if home and away:
                matches.append({"home_team": home.text.strip(), "away_team": away.text.strip(),
                                "date": date_el.text.strip() if date_el else "TBD",
                                "stage": "knockout", "venue": "TBD", "source": "fifa.com"})
        return matches
    except Exception as e:
        print(f"FIFA爬取失败: {e}")
        return []

def get_knockout_matches():
    matches = scrape_espn_knockout()
    if not matches:
        matches = scrape_fifa_knockout()
    if not matches:
        path = os.path.join(os.path.dirname(__file__), FALLBACK_FILE)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return [
            {"stage":"round_of_32","home_team":"待定","away_team":"待定","date":"2026-06-28","venue":"待定","source":"template"},
            {"stage":"round_of_16","home_team":"待定","away_team":"待定","date":"2026-07-04","venue":"待定","source":"template"},
            {"stage":"quarter_final","home_team":"待定","away_team":"待定","date":"2026-07-09","venue":"待定","source":"template"},
            {"stage":"semi_final","home_team":"待定","away_team":"待定","date":"2026-07-14","venue":"待定","source":"template"},
            {"stage":"final","home_team":"待定","away_team":"待定","date":"2026-07-19","venue":"纽约","source":"template"}
        ]
    return matches

if __name__ == "__main__":
    matches = get_knockout_matches()
    print(f"淘汰赛场次: {len(matches)}")
    for m in matches:
        print(f"  {m['stage']}: {m['home_team']} vs {m['away_team']} ({m['date']})")
