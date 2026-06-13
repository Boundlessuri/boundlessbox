"""H2H 数据采集与校验

数据来源: FBref.com 国际比赛记录 2014-2026
覆盖: 世界杯正赛、洲际杯、友谊赛、U17/U20/U23 梯队赛
"""

import json
import os
from datetime import datetime

# 48 支 2026 世界杯参赛队
TEAMS_2026 = [
    "美国", "墨西哥", "加拿大",
    "阿根廷", "巴西", "乌拉圭", "哥伦比亚", "厄瓜多尔", "秘鲁", "智利",
    "法国", "西班牙", "德国", "英格兰", "葡萄牙", "意大利", "荷兰", "比利时", "克罗地亚",
    "摩洛哥", "塞内加尔", "尼日利亚", "埃及", "喀麦隆", "加纳", "科特迪瓦", "阿尔及利亚", "突尼斯",
    "日本", "韩国", "伊朗", "沙特阿拉伯", "澳大利亚", "卡塔尔",
    "哥斯达黎加", "巴拿马", "牙买加", "洪都拉斯",
    "塞尔维亚", "瑞士", "丹麦", "瑞典", "波兰", "乌克兰", "奥地利", "土耳其", "挪威",
    "新西兰", "阿联酋",
]

COMPETITION_WEIGHTS = {
    "world_cup": 1.0,
    "continental": 0.8,
    "friendly": 0.5,
    "u23_olympic": 0.4,
    "u20_world_cup": 0.4,
    "u17_world_cup": 0.35,
}

MATCH_SCHEMA = {
    "home_team": str,
    "away_team": str,
    "home_score": int,
    "away_score": int,
    "date": str,
    "competition": str,
    "venue": str,
    "source_url": str,
}


def compute_weight(match: dict, reference_date: str = "2026-06-14") -> float:
    """计算单场比赛的预测权重"""
    base = COMPETITION_WEIGHTS.get(match["competition"], 0.3)
    match_date = datetime.strptime(match["date"], "%Y-%m-%d")
    ref_date = datetime.strptime(reference_date, "%Y-%m-%d")
    years_ago = (ref_date - match_date).days / 365.25
    time_decay = 0.85 ** years_ago
    weight = base * time_decay
    if match["competition"] in ("u23_olympic", "u20_world_cup", "u17_world_cup"):
        if 4 <= years_ago <= 8:
            weight *= 1.2
    return round(weight, 4)


def validate_match(match: dict) -> bool:
    """校验单场数据"""
    if match["home_score"] < 0 or match["away_score"] < 0:
        return False
    try:
        d = datetime.strptime(match["date"], "%Y-%m-%d")
        if d > datetime(2026, 6, 14):
            return False
    except ValueError:
        return False
    if match["competition"] not in COMPETITION_WEIGHTS:
        return False
    return True


def load_h2h_database(path: str = None) -> list:
    """加载 H2H 数据库"""
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "h2h_database.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["matches"]


def find_h2h_matches(team_a: str, team_b: str, database: list) -> list:
    """找出两队所有历史交手记录"""
    results = []
    for m in database:
        if (m["home_team"] == team_a and m["away_team"] == team_b) or \
           (m["home_team"] == team_b and m["away_team"] == team_a):
            results.append(m)
    return sorted(results, key=lambda x: x["date"], reverse=True)


def collect_all(urls: list = None) -> list:
    """从 FBref 等来源批量抓取比赛数据"""
    import requests
    from bs4 import BeautifulSoup
    import time

    all_matches = []
    seen = set()

    for team in TEAMS_2026:
        try:
            # FBref 球队页面格式需根据队伍 ID 构造
            pass
        except Exception as e:
            print(f"采集 {team} 失败: {e}")
        time.sleep(2)

    return all_matches


if __name__ == "__main__":
    print("开始采集 H2H 数据...")
    matches = collect_all()
    print(f"采集完成，共 {len(matches)} 场")
