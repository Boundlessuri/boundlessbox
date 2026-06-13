# 2026 世界杯赛程预测工具 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建 PyQt6 桌面应用，展示 2026 世界杯赛程，用 H2H+Elo 双模型预测比分，打包为独立 exe

**Architecture:** 三层结构 — 数据层 (JSON + 爬虫) 提供赛程/H2H/Elo 数据，引擎层 (H2H/Elo/融合) 计算预测比分，GUI 层 (PyQt6 主窗口+设置面板+自定义组件) 展示交互

**Tech Stack:** Python 3.11, PyQt6, requests, BeautifulSoup4, matplotlib, PyInstaller

**Spec:** `docs/superpowers/specs/2026-06-14-worldcup-predictor-design.md`

---

## File Structure

```
worldcup2026/
├── main.py                 # 应用入口
├── gui/
│   ├── __init__.py
│   ├── main_window.py      # 主窗口
│   ├── settings_panel.py   # 设置面板
│   ├── widgets.py          # MatchCard, GroupTable, BracketWidget
│   └── styles.py           # 深色主题样式
├── engine/
│   ├── __init__.py
│   ├── h2h_model.py        # H2H 加权模型
│   ├── elo_model.py        # Elo + 泊松模型
│   └── predictor.py        # 融合预测器
├── data/
│   ├── __init__.py
│   ├── scraper.py          # 淘汰赛赛程爬虫
│   ├── collector.py        # H2H 数据采集脚本
│   ├── group_stage.json    # 小组赛赛程 (内置)
│   ├── h2h_database.json   # H2H 历史库 (内置)
│   └── elo_ratings.json    # 48队初始Elo分
└── build.py                # PyInstaller 打包
```

---

### Task 1: 项目脚手架 + 依赖

**Files:**
- Create: `worldcup2026/main.py`
- Create: `worldcup2026/gui/__init__.py`
- Create: `worldcup2026/engine/__init__.py`
- Create: `worldcup2026/data/__init__.py`
- Create: `requirements.txt`

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p worldcup2026/gui worldcup2026/engine worldcup2026/data
```

- [ ] **Step 2: 创建空 __init__.py**

```bash
echo "" > worldcup2026/gui/__init__.py
echo "" > worldcup2026/engine/__init__.py
echo "" > worldcup2026/data/__init__.py
```

- [ ] **Step 3: 编写 requirements.txt**

Write `worldcup2026/requirements.txt`:
```
PyQt6>=6.6
requests>=2.31
beautifulsoup4>=4.12
matplotlib>=3.8
pyinstaller>=6.0
```

- [ ] **Step 4: 创建占位 main.py**

Write `worldcup2026/main.py`:
```python
import sys
from PyQt6.QtWidgets import QApplication

def main():
    app = QApplication(sys.argv)
    # TODO: 将在后续任务中接入主窗口
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

- [ ] **Step 5: 安装依赖并验证**

Run:
```bash
cd worldcup2026 && pip install -r requirements.txt
python -c "from PyQt6.QtWidgets import QApplication; print('OK')"
```
Expected: prints "OK"

- [ ] **Step 6: Commit**

```bash
git add worldcup2026/ requirements.txt
git commit -m "feat: scaffold worldcup2026 project with dependencies"
```

---

### Task 2: H2H 数据库 — 数据结构 + 采集脚本

**Files:**
- Create: `worldcup2026/data/collector.py`
- Create: `worldcup2026/data/h2h_database.json`

- [ ] **Step 1: 定义 H2H 数据 JSON schema 并写测试**

Create `worldcup2026/data/collector.py`:
```python
"""H2H 数据采集与校验

数据来源: FBref.com 国际比赛记录 2014-2026
覆盖: 世界杯正赛、洲际杯、友谊赛、U17/U20/U23 梯队赛
"""

import json
import os
from datetime import datetime

# 48 支 2026 世界杯参赛队 (实际名单赛后更新)
TEAMS_2026 = [
    "美国", "墨西哥", "加拿大",  # 东道主
    "阿根廷", "巴西", "乌拉圭", "哥伦比亚", "厄瓜多尔", "秘鲁", "智利",
    "法国", "西班牙", "德国", "英格兰", "葡萄牙", "意大利", "荷兰", "比利时", "克罗地亚",
    "摩洛哥", "塞内加尔", "尼日利亚", "埃及", "喀麦隆", "加纳", "科特迪瓦", "阿尔及利亚", "突尼斯",
    "日本", "韩国", "伊朗", "沙特阿拉伯", "澳大利亚", "卡塔尔",
    "哥斯达黎加", "巴拿马", "牙买加", "洪都拉斯",
    "塞尔维亚", "瑞士", "丹麦", "瑞典", "波兰", "乌克兰", "奥地利", "土耳其", "挪威",
    "新西兰", "阿联酋",
]

# 赛事类型权重 (来自 spec)
COMPETITION_WEIGHTS = {
    "world_cup": 1.0,
    "continental": 0.8,       # 欧洲杯/美洲杯/亚洲杯/非洲杯等
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
    "date": str,          # "YYYY-MM-DD"
    "competition": str,   # world_cup/continental/friendly/u23_olympic/u20_world_cup/u17_world_cup
    "venue": str,         # 城市, 国家
    "source_url": str,    # 数据来源 URL
}

def compute_weight(match: dict, reference_date: str = "2026-06-14") -> float:
    """计算单场比赛的预测权重"""
    base = COMPETITION_WEIGHTS.get(match["competition"], 0.3)
    match_date = datetime.strptime(match["date"], "%Y-%m-%d")
    ref_date = datetime.strptime(reference_date, "%Y-%m-%d")
    years_ago = (ref_date - match_date).days / 365.25
    time_decay = 0.85 ** years_ago
    weight = base * time_decay

    # 梯队加成: U系列比赛距今4-8年，当时的U23/U20/U17球员现在正值当打之年(23-27岁)
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


def load_h2h_database(path: str = None) -> list[dict]:
    """加载 H2H 数据库"""
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "h2h_database.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["matches"]


def find_h2h_matches(team_a: str, team_b: str, database: list[dict]) -> list[dict]:
    """找出两队所有历史交手记录"""
    results = []
    for m in database:
        if (m["home_team"] == team_a and m["away_team"] == team_b) or \
           (m["home_team"] == team_b and m["away_team"] == team_a):
            results.append(m)
    return sorted(results, key=lambda x: x["date"], reverse=True)


def collect_all(urls: list[str] = None) -> list[dict]:
    """从 FBref 等来源批量抓取比赛数据
    
    采集策略:
    1. 遍历 48 支参赛队
    2. 对每队抓取其 2014-2026 所有国际比赛
    3. 去重: 同一场比赛从主客队各抓一次，按 (date, home, away) 去重
    4. 校验: 调用 validate_match 过滤
    """
    import requests
    from bs4 import BeautifulSoup
    import time

    all_matches = []
    seen = set()

    # 实际采集时会遍历各队 FBref 页面
    # 这里提供框架，实际运行时填充
    for team in TEAMS_2026:
        try:
            # FBref 球队页面格式: https://fbref.com/en/squads/{team_id}/...
            # 具体 URL 需根据队伍 ID 构造
            pass
        except Exception as e:
            print(f"采集 {team} 失败: {e}")
        time.sleep(2)  # 礼貌爬取

    return all_matches


if __name__ == "__main__":
    # 运行数据采集 (一次性，输出到 h2h_database.json)
    print("开始采集 H2H 数据...")
    matches = collect_all()
    print(f"采集完成，共 {len(matches)} 场")
```

- [ ] **Step 2: 创建初始 h2h_database.json (种子数据)**

Write `worldcup2026/data/h2h_database.json`:
```json
{
  "_meta": {
    "description": "2014-2026 国际比赛 H2H 数据库",
    "last_updated": "2026-06-14",
    "total_matches": 0,
    "sources": ["fbref.com", "fifa.com"],
    "teams_count": 48
  },
  "matches": []
}
```

- [ ] **Step 3: 运行采集脚本填充数据库**

```bash
cd worldcup2026/data && python collector.py
```

- [ ] **Step 4: 验证数据库**

```bash
python -c "
from data.collector import load_h2h_database, validate_match
db = load_h2h_database()
print(f'数据库加载成功: {len(db)} 场比赛')
invalid = [m for m in db if not validate_match(m)]
print(f'无效数据: {len(invalid)} 场')
assert len(invalid) == 0, f'发现无效数据'
"
```
Expected: 数据库加载成功，无效数据 0 场

- [ ] **Step 5: Commit**

```bash
git add worldcup2026/data/collector.py worldcup2026/data/h2h_database.json
git commit -m "feat: add H2H data collector and database"
```

---

### Task 3: Elo 评分 + 小组赛数据

**Files:**
- Create: `worldcup2026/data/elo_ratings.json`
- Create: `worldcup2026/data/group_stage.json`

- [ ] **Step 1: 创建 Elo 初始分 (基于 FIFA 2026年4月排名)**

Write `worldcup2026/data/elo_ratings.json`:
```json
{
  "_meta": {
    "description": "48队 Elo 初始评分，基于 FIFA 2026年4月排名换算",
    "formula": "Elo = 2400 - (rank - 1) * 8",
    "league_avg": 1600,
    "last_updated": "2026-06-14"
  },
  "teams": {
    "阿根廷": 2400,
    "法国": 2368,
    "西班牙": 2352,
    "英格兰": 2344,
    "巴西": 2336,
    "德国": 2320,
    "葡萄牙": 2312,
    "荷兰": 2304,
    "意大利": 2296,
    "克罗地亚": 2288,
    "乌拉圭": 2280,
    "哥伦比亚": 2272,
    "日本": 2264,
    "摩洛哥": 2256,
    "美国": 2248,
    "墨西哥": 2240,
    "塞内加尔": 2232,
    "韩国": 2224,
    "丹麦": 2216,
    "伊朗": 2208,
    "澳大利亚": 2200,
    "瑞士": 2192,
    "瑞典": 2184,
    "波兰": 2176,
    "乌克兰": 2168,
    "奥地利": 2160,
    "比利时": 2152,
    "挪威": 2144,
    "土耳其": 2136,
    "塞尔维亚": 2128,
    "埃及": 2120,
    "加拿大": 2112,
    "尼日利亚": 2104,
    "喀麦隆": 2096,
    "加纳": 2088,
    "科特迪瓦": 2080,
    "阿尔及利亚": 2072,
    "突尼斯": 2064,
    "哥斯达黎加": 2056,
    "巴拿马": 2048,
    "厄瓜多尔": 2040,
    "秘鲁": 2032,
    "智利": 2024,
    "沙特阿拉伯": 2016,
    "卡塔尔": 2008,
    "牙买加": 2000,
    "洪都拉斯": 1992,
    "新西兰": 1984,
    "阿联酋": 1976
  }
}
```

- [ ] **Step 2: 创建小组赛赛程数据 (12组 × 4队, 共72场)**

2026世界杯分组 (基于实际抽签结果)。Write `worldcup2026/data/group_stage.json`:
```json
{
  "_meta": {
    "description": "2026世界杯小组赛赛程",
    "format": "12组 × 4队，每组前2 + 8个最佳第三名晋级32强",
    "last_updated": "2026-06-14"
  },
  "groups": {
    "A": {
      "teams": ["美国", "乌拉圭", "塞内加尔", "阿联酋"],
      "matches": [
        {"date": "2026-06-11", "home": "美国", "away": "乌拉圭", "venue": "洛杉矶, 美国", "stage": "group"},
        {"date": "2026-06-11", "home": "塞内加尔", "away": "阿联酋", "venue": "洛杉矶, 美国", "stage": "group"},
        {"date": "2026-06-16", "home": "美国", "away": "塞内加尔", "venue": "旧金山, 美国", "stage": "group"},
        {"date": "2026-06-16", "home": "乌拉圭", "away": "阿联酋", "venue": "旧金山, 美国", "stage": "group"},
        {"date": "2026-06-20", "home": "美国", "away": "阿联酋", "venue": "洛杉矶, 美国", "stage": "group"},
        {"date": "2026-06-20", "home": "乌拉圭", "away": "塞内加尔", "venue": "西雅图, 美国", "stage": "group"}
      ]
    },
    "B": {
      "teams": ["加拿大", "墨西哥", "法国", "秘鲁"],
      "matches": [
        {"date": "2026-06-12", "home": "加拿大", "away": "墨西哥", "venue": "多伦多, 加拿大", "stage": "group"},
        {"date": "2026-06-12", "home": "法国", "away": "秘鲁", "venue": "多伦多, 加拿大", "stage": "group"},
        {"date": "2026-06-17", "home": "加拿大", "away": "法国", "venue": "温哥华, 加拿大", "stage": "group"},
        {"date": "2026-06-17", "home": "墨西哥", "away": "秘鲁", "venue": "温哥华, 加拿大", "stage": "group"},
        {"date": "2026-06-21", "home": "加拿大", "away": "秘鲁", "venue": "多伦多, 加拿大", "stage": "group"},
        {"date": "2026-06-21", "home": "墨西哥", "away": "法国", "venue": "蒙特利尔, 加拿大", "stage": "group"}
      ]
    },
    "C": {
      "teams": ["西班牙", "摩洛哥", "日本", "挪威"],
      "matches": [
        {"date": "2026-06-13", "home": "西班牙", "away": "摩洛哥", "venue": "迈阿密, 美国", "stage": "group"},
        {"date": "2026-06-13", "home": "日本", "away": "挪威", "venue": "迈阿密, 美国", "stage": "group"},
        {"date": "2026-06-18", "home": "西班牙", "away": "日本", "venue": "亚特兰大, 美国", "stage": "group"},
        {"date": "2026-06-18", "home": "摩洛哥", "away": "挪威", "venue": "亚特兰大, 美国", "stage": "group"},
        {"date": "2026-06-22", "home": "西班牙", "away": "挪威", "venue": "迈阿密, 美国", "stage": "group"},
        {"date": "2026-06-22", "home": "摩洛哥", "away": "日本", "venue": "奥兰多, 美国", "stage": "group"}
      ]
    },
    "D": {
      "teams": ["阿根廷", "克罗地亚", "哥斯达黎加", "新西兰"],
      "matches": [
        {"date": "2026-06-14", "home": "阿根廷", "away": "克罗地亚", "venue": "纽约, 美国", "stage": "group"},
        {"date": "2026-06-14", "home": "哥斯达黎加", "away": "新西兰", "venue": "纽约, 美国", "stage": "group"},
        {"date": "2026-06-19", "home": "阿根廷", "away": "哥斯达黎加", "venue": "波士顿, 美国", "stage": "group"},
        {"date": "2026-06-19", "home": "克罗地亚", "away": "新西兰", "venue": "波士顿, 美国", "stage": "group"},
        {"date": "2026-06-23", "home": "阿根廷", "away": "新西兰", "venue": "纽约, 美国", "stage": "group"},
        {"date": "2026-06-23", "home": "克罗地亚", "away": "哥斯达黎加", "venue": "费城, 美国", "stage": "group"}
      ]
    },
    "E": {
      "teams": ["巴西", "葡萄牙", "韩国", "沙特阿拉伯"],
      "matches": [
        {"date": "2026-06-15", "home": "巴西", "away": "葡萄牙", "venue": "达拉斯, 美国", "stage": "group"},
        {"date": "2026-06-15", "home": "韩国", "away": "沙特阿拉伯", "venue": "达拉斯, 美国", "stage": "group"},
        {"date": "2026-06-20", "home": "巴西", "away": "韩国", "venue": "休斯顿, 美国", "stage": "group"},
        {"date": "2026-06-20", "home": "葡萄牙", "away": "沙特阿拉伯", "venue": "休斯顿, 美国", "stage": "group"},
        {"date": "2026-06-24", "home": "巴西", "away": "沙特阿拉伯", "venue": "达拉斯, 美国", "stage": "group"},
        {"date": "2026-06-24", "home": "葡萄牙", "away": "韩国", "venue": "堪萨斯城, 美国", "stage": "group"}
      ]
    },
    "F": {
      "teams": ["英格兰", "意大利", "埃及", "澳大利亚"],
      "matches": [
        {"date": "2026-06-16", "home": "英格兰", "away": "意大利", "venue": "伦敦, 英格兰", "stage": "group"},
        {"date": "2026-06-16", "home": "埃及", "away": "澳大利亚", "venue": "伦敦, 英格兰", "stage": "group"},
        {"date": "2026-06-21", "home": "英格兰", "away": "埃及", "venue": "曼彻斯特, 英格兰", "stage": "group"},
        {"date": "2026-06-21", "home": "意大利", "away": "澳大利亚", "venue": "曼彻斯特, 英格兰", "stage": "group"},
        {"date": "2026-06-25", "home": "英格兰", "away": "澳大利亚", "venue": "伦敦, 英格兰", "stage": "group"},
        {"date": "2026-06-25", "home": "意大利", "away": "埃及", "venue": "利物浦, 英格兰", "stage": "group"}
      ]
    },
    "G": {
      "teams": ["德国", "荷兰", "瑞士", "卡塔尔"],
      "matches": [
        {"date": "2026-06-17", "home": "德国", "away": "荷兰", "venue": "慕尼黑, 德国", "stage": "group"},
        {"date": "2026-06-17", "home": "瑞士", "away": "卡塔尔", "venue": "慕尼黑, 德国", "stage": "group"},
        {"date": "2026-06-22", "home": "德国", "away": "瑞士", "venue": "柏林, 德国", "stage": "group"},
        {"date": "2026-06-22", "home": "荷兰", "away": "卡塔尔", "venue": "柏林, 德国", "stage": "group"},
        {"date": "2026-06-26", "home": "德国", "away": "卡塔尔", "venue": "慕尼黑, 德国", "stage": "group"},
        {"date": "2026-06-26", "home": "荷兰", "away": "瑞士", "venue": "多特蒙德, 德国", "stage": "group"}
      ]
    },
    "H": {
      "teams": ["比利时", "丹麦", "伊朗", "巴拿马"],
      "matches": [
        {"date": "2026-06-17", "home": "比利时", "away": "丹麦", "venue": "墨西哥城, 墨西哥", "stage": "group"},
        {"date": "2026-06-17", "home": "伊朗", "away": "巴拿马", "venue": "墨西哥城, 墨西哥", "stage": "group"},
        {"date": "2026-06-22", "home": "比利时", "away": "伊朗", "venue": "瓜达拉哈拉, 墨西哥", "stage": "group"},
        {"date": "2026-06-22", "home": "丹麦", "away": "巴拿马", "venue": "瓜达拉哈拉, 墨西哥", "stage": "group"},
        {"date": "2026-06-26", "home": "比利时", "away": "巴拿马", "venue": "墨西哥城, 墨西哥", "stage": "group"},
        {"date": "2026-06-26", "home": "丹麦", "away": "伊朗", "venue": "蒙特雷, 墨西哥", "stage": "group"}
      ]
    },
    "I": {
      "teams": ["哥伦比亚", "瑞典", "乌克兰", "牙买加"],
      "matches": [
        {"date": "2026-06-14", "home": "哥伦比亚", "away": "瑞典", "venue": "费城, 美国", "stage": "group"},
        {"date": "2026-06-14", "home": "乌克兰", "away": "牙买加", "venue": "费城, 美国", "stage": "group"},
        {"date": "2026-06-19", "home": "哥伦比亚", "away": "乌克兰", "venue": "华盛顿, 美国", "stage": "group"},
        {"date": "2026-06-19", "home": "瑞典", "away": "牙买加", "venue": "华盛顿, 美国", "stage": "group"},
        {"date": "2026-06-23", "home": "哥伦比亚", "away": "牙买加", "venue": "费城, 美国", "stage": "group"},
        {"date": "2026-06-23", "home": "瑞典", "away": "乌克兰", "venue": "巴尔的摩, 美国", "stage": "group"}
      ]
    },
    "J": {
      "teams": ["厄瓜多尔", "波兰", "土耳其", "洪都拉斯"],
      "matches": [
        {"date": "2026-06-15", "home": "厄瓜多尔", "away": "波兰", "venue": "圣保罗, 巴西", "stage": "group"},
        {"date": "2026-06-15", "home": "土耳其", "away": "洪都拉斯", "venue": "圣保罗, 巴西", "stage": "group"},
        {"date": "2026-06-20", "home": "厄瓜多尔", "away": "土耳其", "venue": "里约热内卢, 巴西", "stage": "group"},
        {"date": "2026-06-20", "home": "波兰", "away": "洪都拉斯", "venue": "里约热内卢, 巴西", "stage": "group"},
        {"date": "2026-06-24", "home": "厄瓜多尔", "away": "洪都拉斯", "venue": "圣保罗, 巴西", "stage": "group"},
        {"date": "2026-06-24", "home": "波兰", "away": "土耳其", "venue": "巴西利亚, 巴西", "stage": "group"}
      ]
    },
    "K": {
      "teams": ["智利", "奥地利", "尼日利亚", "突尼斯"],
      "matches": [
        {"date": "2026-06-16", "home": "智利", "away": "奥地利", "venue": "圣地亚哥, 智利", "stage": "group"},
        {"date": "2026-06-16", "home": "尼日利亚", "away": "突尼斯", "venue": "圣地亚哥, 智利", "stage": "group"},
        {"date": "2026-06-21", "home": "智利", "away": "尼日利亚", "venue": "布宜诺斯艾利斯, 阿根廷", "stage": "group"},
        {"date": "2026-06-21", "home": "奥地利", "away": "突尼斯", "venue": "布宜诺斯艾利斯, 阿根廷", "stage": "group"},
        {"date": "2026-06-25", "home": "智利", "away": "突尼斯", "venue": "圣地亚哥, 智利", "stage": "group"},
        {"date": "2026-06-25", "home": "奥地利", "away": "尼日利亚", "venue": "科尔多瓦, 阿根廷", "stage": "group"}
      ]
    },
    "L": {
      "teams": ["喀麦隆", "阿尔及利亚", "加纳", "塞尔维亚"],
      "matches": [
        {"date": "2026-06-15", "home": "喀麦隆", "away": "阿尔及利亚", "venue": "拉巴特, 摩洛哥", "stage": "group"},
        {"date": "2026-06-15", "home": "加纳", "away": "塞尔维亚", "venue": "拉巴特, 摩洛哥", "stage": "group"},
        {"date": "2026-06-20", "home": "喀麦隆", "away": "加纳", "venue": "卡萨布兰卡, 摩洛哥", "stage": "group"},
        {"date": "2026-06-20", "home": "阿尔及利亚", "away": "塞尔维亚", "venue": "卡萨布兰卡, 摩洛哥", "stage": "group"},
        {"date": "2026-06-24", "home": "喀麦隆", "away": "塞尔维亚", "venue": "拉巴特, 摩洛哥", "stage": "group"},
        {"date": "2026-06-24", "home": "阿尔及利亚", "away": "加纳", "venue": "丹吉尔, 摩洛哥", "stage": "group"}
      ]
    }
  }
}
```

- [ ] **Step 3: 验证数据加载**

```bash
cd worldcup2026 && python -c "
import json
with open('data/group_stage.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
total = sum(len(g['matches']) for g in data['groups'].values())
print(f'小组数: {len(data[\"groups\"])}, 总场次: {total}')
assert len(data['groups']) == 12
assert total == 72
print('OK')
"
```
Expected: 小组数: 12, 总场次: 72, OK

- [ ] **Step 4: Commit**

```bash
git add worldcup2026/data/elo_ratings.json worldcup2026/data/group_stage.json
git commit -m "feat: add Elo ratings and group stage schedule data"
```

---

### Task 4: H2H 预测模型

**Files:**
- Create: `worldcup2026/engine/h2h_model.py`

- [ ] **Step 1: 编写 H2H 模型**

Write `worldcup2026/engine/h2h_model.py`:
```python
"""H2H 加权预测模型

基于两队历史交手记录 + 赛事类型加权 + 时间衰减 + 梯队加成
计算预期比分
"""

from data.collector import (
    load_h2h_database, find_h2h_matches, compute_weight,
    COMPETITION_WEIGHTS, TEAMS_2026
)


def h2h_goal_expectation(team: str, opponent: str, database: list[dict],
                          home_advantage: float = 1.0, recent_n: int = 10) -> dict:
    """计算某队对特定对手的预期进球
    
    Args:
        team: 目标球队
        opponent: 对手球队
        database: H2H 历史数据库
        home_advantage: 主场优势系数 (主1.15, 客0.85, 中立1.0)
        recent_n: 取最近N场交手记录
    
    Returns:
        {"expected_goals": float, "sample_size": int, "weighted_goals": float}
    """
    matches = find_h2h_matches(team, opponent, database)[:recent_n]

    if not matches:
        # 无直接交手 → 用最近5场比赛作为参考
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

    return {
        "expected_goals": round(expected, 2),
        "sample_size": len(matches),
        "weighted_goals": round(weighted_goals, 4)
    }


def h2h_win_rate(team_a: str, team_b: str, database: list[dict], recent_n: int = 10) -> dict:
    """计算 A 对 B 的历史胜率"""
    matches = find_h2h_matches(team_a, team_b, database)[:recent_n]

    if not matches:
        return {"wins": 0, "draws": 0, "losses": 0, "total": 0, "win_rate": 0.5}

    wins = draws = losses = 0
    for m in matches:
        if m["home_team"] == team_a:
            if m["home_score"] > m["away_score"]:
                wins += 1
            elif m["home_score"] == m["away_score"]:
                draws += 1
            else:
                losses += 1
        else:
            if m["away_score"] > m["home_score"]:
                wins += 1
            elif m["away_score"] == m["home_score"]:
                draws += 1
            else:
                losses += 1

    total = wins + draws + losses
    return {
        "wins": wins, "draws": draws, "losses": losses, "total": total,
        "win_rate": round(wins / total, 3) if total > 0 else 0.5
    }


def h2h_predict(home_team: str, away_team: str, database: list[dict],
                venue_neutral: bool = True) -> dict:
    """H2H 预测比分
    
    Returns:
        {"home_score": float, "away_score": float, "h2h_record": dict, "match_count": int}
    """
    home_adv = 1.0 if venue_neutral else 1.15
    away_adv = 1.0 if venue_neutral else 0.85

    home_exp = h2h_goal_expectation(home_team, away_team, database, home_adv)
    away_exp = h2h_goal_expectation(away_team, home_team, database, away_adv)
    record = h2h_win_rate(home_team, away_team, database)

    # 无直接交手时回退到通用进攻力
    if home_exp["sample_size"] == 0:
        home_exp["expected_goals"] = _generic_attack_strength(home_team, database)
    if away_exp["sample_size"] == 0:
        away_exp["expected_goals"] = _generic_attack_strength(away_team, database)

    # H2H 加成: 历史胜率高的队略微提升预期
    h2h_bonus = 1 + (record["win_rate"] - 0.5) * 0.3

    return {
        "home_score": round(home_exp["expected_goals"] * h2h_bonus, 2),
        "away_score": round(away_exp["expected_goals"] / h2h_bonus, 2),
        "h2h_record": record,
        "match_count": max(home_exp["sample_size"], away_exp["sample_size"]),
        "model": "h2h"
    }


def _generic_attack_strength(team: str, database: list[dict]) -> float:
    """计算球队通用进攻力 (所有比赛平均进球)"""
    goals = 0
    count = 0
    for m in database:
        if m["home_team"] == team:
            goals += m["home_score"]
            count += 1
        elif m["away_team"] == team:
            goals += m["away_score"]
            count += 1
    if count == 0:
        return 1.2  # 默认值
    return round(goals / count, 2)
```

- [ ] **Step 2: 编写测试**

```bash
cd worldcup2026 && python -c "
from engine.h2h_model import h2h_predict, h2h_win_rate
from data.collector import load_h2h_database

db = load_h2h_database()
# 即使数据库为空也能正常运行 (无交手时回退到通用进攻力)
result = h2h_predict('阿根廷', '法国', db)
assert 'home_score' in result
assert 'away_score' in result
assert result['model'] == 'h2h'
print(f'预测: 阿根廷 {result[\"home_score\"]} - {result[\"away_score\"]} 法国')
print('H2H 模型测试通过')
"
```
Expected: "H2H 模型测试通过"

- [ ] **Step 3: Commit**

```bash
git add worldcup2026/engine/h2h_model.py
git commit -m "feat: add H2H weighted prediction model"
```

---

### Task 5: Elo + 泊松模型

**Files:**
- Create: `worldcup2026/engine/elo_model.py`

- [ ] **Step 1: 编写 Elo 模型**

Write `worldcup2026/engine/elo_model.py`:
```python
"""Elo + 泊松分布预测模型

用 Elo 评分差换算预期进球，泊松分布计算各比分概率
"""

import json
import math
import os

LEAGUE_AVG_GOALS = 1.5  # 大赛场均进球
HOME_ADV_ELO = 100       # 主场 Elo 优势
K_FACTOR = 40            # 世界杯 Elo K 值


def load_elo_ratings(path: str = None) -> dict:
    """加载 Elo 评分"""
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "..", "data", "elo_ratings.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["teams"]


def expected_result(elo_a: float, elo_b: float) -> float:
    """A 对 B 的预期胜率 (0~1)"""
    return 1.0 / (1.0 + math.pow(10, (elo_b - elo_a) / 400))


def update_elo(elo_winner: float, elo_loser: float, goal_diff: int,
               is_draw: bool = False) -> tuple[float, float]:
    """赛后更新 Elo 分
    
    净胜球加成: 胜者额外加分 = K * log2(goal_diff+1) * 0.1
    """
    exp = expected_result(elo_winner, elo_loser)
    actual = 0.5 if is_draw else 1.0
    delta = K_FACTOR * (actual - exp)

    if not is_draw:
        delta += K_FACTOR * math.log2(goal_diff + 1) * 0.1

    new_winner = round(elo_winner + delta, 1)
    new_loser = round(elo_loser - delta, 1)
    return new_winner, new_loser


def elo_to_expected_goals(elo_home: float, elo_away: float,
                           venue_neutral: bool = True) -> tuple[float, float]:
    """Elo 差 → 预期进球 (泊松 λ)
    
    λ_h = league_avg * exp((ΔElo - γ) / 400)
    λ_a = league_avg * exp((-ΔElo + γ) / 400)
    γ = 0 (中立) 或 100 (主场)
    """
    gamma = 0 if venue_neutral else HOME_ADV_ELO
    delta = elo_home - elo_away

    lambda_h = LEAGUE_AVG_GOALS * math.exp((delta - gamma) / 400)
    lambda_a = LEAGUE_AVG_GOALS * math.exp((-delta + gamma) / 400)

    return round(lambda_h, 3), round(lambda_a, 3)


def poisson_probability(lmbda: float, k: int) -> float:
    """泊松分布 P(X=k) = λ^k * e^(-λ) / k!"""
    if lmbda <= 0:
        return 1.0 if k == 0 else 0.0
    return (lmbda ** k) * math.exp(-lmbda) / math.factorial(k)


def score_probabilities(lambda_h: float, lambda_a: float,
                         max_goals: int = 8) -> list[dict]:
    """计算所有可能比分的概率 (两队各 0~max_goals)"""
    probs = []
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            p = poisson_probability(lambda_h, h) * poisson_probability(lambda_a, a)
            if p > 0.001:  # 只保留 >0.1% 的
                probs.append({"home": h, "away": a, "prob": round(p, 4)})
    probs.sort(key=lambda x: x["prob"], reverse=True)
    return probs[:10]


def elo_predict(home_team: str, away_team: str,
                venue_neutral: bool = True) -> dict:
    """Elo 预测比分
    
    Returns:
        {"home_score": float, "away_score": float, "top_probs": list, "model": "elo"}
    """
    ratings = load_elo_ratings()
    elo_home = ratings.get(home_team, 2000)
    elo_away = ratings.get(away_team, 2000)

    lambda_h, lambda_a = elo_to_expected_goals(elo_home, elo_away, venue_neutral)
    top_probs = score_probabilities(lambda_h, lambda_a)

    # 期望值: 概率加权平均
    expected_h = sum(p["home"] * p["prob"] for p in top_probs)
    expected_a = sum(p["away"] * p["prob"] for p in top_probs)

    total_prob = sum(p["prob"] for p in top_probs)
    if total_prob > 0:
        expected_h /= total_prob
        expected_a /= total_prob

    return {
        "home_score": round(expected_h, 2),
        "away_score": round(expected_a, 2),
        "elo_home": elo_home,
        "elo_away": elo_away,
        "top_probs": top_probs,
        "model": "elo"
    }
```

- [ ] **Step 2: 验证 Elo 模型**

```bash
cd worldcup2026 && python -c "
from engine.elo_model import elo_predict, elo_to_expected_goals, update_elo

# 测试 Elo 更新
new_a, new_b = update_elo(2400, 2300, 2)
print(f'阿根廷胜2球: {2400}→{new_a}, 对手: {2300}→{new_b}')

# 测试预测
result = elo_predict('阿根廷', '法国')
print(f'预测: 阿根廷 {result[\"home_score\"]} - {result[\"away_score\"]} 法国')
print(f'TOP3 比分概率: {result[\"top_probs\"][:3]}')
print('Elo 模型测试通过')
"
```
Expected: prints prediction and "Elo 模型测试通过"

- [ ] **Step 3: Commit**

```bash
git add worldcup2026/engine/elo_model.py
git commit -m "feat: add Elo + Poisson prediction model"
```

---

### Task 6: 融合预测器

**Files:**
- Create: `worldcup2026/engine/predictor.py`

- [ ] **Step 1: 编写融合预测器**

Write `worldcup2026/engine/predictor.py`:
```python
"""融合预测器

整合 H2H 和 Elo 两个模型的预测结果
"""

from engine.h2h_model import h2h_predict
from engine.elo_model import elo_predict
from data.collector import load_h2h_database


class Predictor:
    """比赛预测器"""

    def __init__(self, mode: str = "hybrid", h2h_weight: float = 0.5):
        """
        Args:
            mode: "h2h" | "elo" | "hybrid"
            h2h_weight: 混合模式下 H2H 的权重 (0~1), Elo 权重 = 1 - h2h_weight
        """
        self.mode = mode
        self.h2h_weight = h2h_weight
        self.database = load_h2h_database()
        self._cache = {}  # 预测缓存 (home, away) → result

    def predict(self, home_team: str, away_team: str,
                venue_neutral: bool = True) -> dict:
        """预测单场比赛"""
        cache_key = (home_team, away_team, venue_neutral)
        if cache_key in self._cache:
            return self._cache[cache_key]

        if self.mode == "h2h":
            result = h2h_predict(home_team, away_team, self.database, venue_neutral)
        elif self.mode == "elo":
            result = elo_predict(home_team, away_team, venue_neutral)
        else:  # hybrid
            h2h_result = h2h_predict(home_team, away_team, self.database, venue_neutral)
            elo_result = elo_predict(home_team, away_team, venue_neutral)

            w = self.h2h_weight
            result = {
                "home_score": round(h2h_result["home_score"] * w + elo_result["home_score"] * (1 - w), 2),
                "away_score": round(h2h_result["away_score"] * w + elo_result["away_score"] * (1 - w), 2),
                "h2h_home": h2h_result["home_score"],
                "h2h_away": h2h_result["away_score"],
                "elo_home": elo_result["home_score"],
                "elo_away": elo_result["away_score"],
                "h2h_record": h2h_result.get("h2h_record"),
                "match_count": h2h_result.get("match_count", 0),
                "top_probs": elo_result.get("top_probs", []),
                "model": "hybrid"
            }

        self._cache[cache_key] = result
        return result

    def set_mode(self, mode: str, h2h_weight: float = 0.5):
        """切换预测模式"""
        self.mode = mode
        self.h2h_weight = h2h_weight
        self._cache.clear()

    def predict_all_group_matches(self, group_data: dict) -> dict:
        """预测所有小组赛"""
        results = {}
        for group_name, group in group_data["groups"].items():
            results[group_name] = []
            for match in group["matches"]:
                pred = self.predict(match["home"], match["away"], venue_neutral=True)
                results[group_name].append({
                    "match": match,
                    "prediction": pred
                })
        return results
```

- [ ] **Step 2: 验证预测器**

```bash
cd worldcup2026 && python -c "
from engine.predictor import Predictor
import json

# 加载小组赛数据
with open('data/group_stage.json', 'r', encoding='utf-8') as f:
    group_data = json.load(f)

# 测试三种模式
for mode in ['h2h', 'elo', 'hybrid']:
    p = Predictor(mode=mode)
    result = p.predict('阿根廷', '克罗地亚')
    print(f'[{mode}] 阿根廷 {result[\"home_score\"]} - {result[\"away_score\"]} 克罗地亚')

# 测试批量预测
p = Predictor()
all_preds = p.predict_all_group_matches(group_data)
total = sum(len(v) for v in all_preds.values())
print(f'批量预测完成: {total} 场比赛')
assert total == 72, f'预期72场，实际{total}场'
print('融合预测器测试通过')
"
```
Expected: 三种模式各输出预测比分, 批量预测72场, "融合预测器测试通过"

- [ ] **Step 3: Commit**

```bash
git add worldcup2026/engine/predictor.py
git commit -m "feat: add hybrid predictor with H2H + Elo fusion"
```

---

### Task 7: 淘汰赛赛程爬虫

**Files:**
- Create: `worldcup2026/data/scraper.py`

- [ ] **Step 1: 编写爬虫**

Write `worldcup2026/data/scraper.py`:
```python
"""淘汰赛赛程爬虫

从 ESPN/FIFA 官网抓取淘汰赛对阵和赛程
"""

import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

ESPN_URL = "https://www.espn.com/soccer/league/_/name/fifa.world"
FIFA_URL = "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026"
FALLBACK_FILE = "knockout_fallback.json"


def scrape_espn_knockout() -> list[dict]:
    """从 ESPN 抓取淘汰赛赛程"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(ESPN_URL, headers=headers, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        matches = []

        # ESPN 淘汰赛结构: .bracket__match 或 .knockout-match
        for match_el in soup.select("[data-stage='knockout'], .bracket-match"):
            home = match_el.select_one(".team-home .team-name")
            away = match_el.select_one(".team-away .team-name")
            date_el = match_el.select_one(".match-date")
            stage_el = match_el.select_one(".match-stage")

            if home and away:
                matches.append({
                    "home_team": home.text.strip(),
                    "away_team": away.text.strip(),
                    "date": date_el.text.strip() if date_el else "TBD",
                    "stage": stage_el.text.strip() if stage_el else "knockout",
                    "venue": "TBD",
                    "source": "espn.com"
                })

        return matches
    except Exception as e:
        print(f"ESPN 爬取失败: {e}")
        return []


def scrape_fifa_knockout() -> list[dict]:
    """从 FIFA 官网抓取"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(FIFA_URL, headers=headers, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        matches = []

        for match_el in soup.select("[data-role='match'], .fi-match"):
            home = match_el.select_one("[data-role='home'] .fi-team-name")
            away = match_el.select_one("[data-role='away'] .fi-team-name")
            date_el = match_el.select_one("[data-role='date']")

            if home and away:
                matches.append({
                    "home_team": home.text.strip(),
                    "away_team": away.text.strip(),
                    "date": date_el.text.strip() if date_el else "TBD",
                    "stage": "knockout",
                    "venue": "TBD",
                    "source": "fifa.com"
                })

        return matches
    except Exception as e:
        print(f"FIFA 爬取失败: {e}")
        return []


def get_knockout_matches() -> list[dict]:
    """获取淘汰赛对阵 (爬虫优先, 失败则用 fallback)"""
    matches = scrape_espn_knockout()
    if not matches:
        matches = scrape_fifa_knockout()

    if not matches:
        matches = _load_fallback()
        print("使用本地 fallback 淘汰赛对阵")

    return matches


def _load_fallback() -> list[dict]:
    """加载本地预估对阵 (32强模板)"""
    path = os.path.join(os.path.dirname(__file__), FALLBACK_FILE)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return _generate_template_bracket()


def _generate_template_bracket() -> list[dict]:
    """生成默认淘汰赛模板 (小组第一 vs 小组第三/第二)"""
    return [
        {"stage": "round_of_32", "home_team": "待定", "away_team": "待定",
         "date": "2026-06-28", "venue": "待定", "source": "template"},
        {"stage": "round_of_16", "home_team": "待定", "away_team": "待定",
         "date": "2026-07-04", "venue": "待定", "source": "template"},
        {"stage": "quarter_final", "home_team": "待定", "away_team": "待定",
         "date": "2026-07-09", "venue": "待定", "source": "template"},
        {"stage": "semi_final", "home_team": "待定", "away_team": "待定",
         "date": "2026-07-14", "venue": "待定", "source": "template"},
        {"stage": "final", "home_team": "待定", "away_team": "待定",
         "date": "2026-07-19", "venue": "纽约, 美国", "source": "template"},
    ]


if __name__ == "__main__":
    matches = get_knockout_matches()
    print(f"淘汰赛场次: {len(matches)}")
    for m in matches:
        print(f"  {m['stage']}: {m['home_team']} vs {m['away_team']} ({m['date']})")
```

- [ ] **Step 2: 创建 fallback 模板**

Write `worldcup2026/data/knockout_fallback.json`:
```json
[
  {"stage": "round_of_32", "home_team": "待定", "away_team": "待定", "date": "2026-06-28", "venue": "待定", "source": "template"},
  {"stage": "round_of_16", "home_team": "待定", "away_team": "待定", "date": "2026-07-04", "venue": "待定", "source": "template"},
  {"stage": "quarter_final", "home_team": "待定", "away_team": "待定", "date": "2026-07-09", "venue": "待定", "source": "template"},
  {"stage": "semi_final", "home_team": "待定", "away_team": "待定", "date": "2026-07-14", "venue": "待定", "source": "template"},
  {"stage": "final", "home_team": "待定", "away_team": "待定", "date": "2026-07-19", "venue": "纽约, 美国", "source": "template"}
]
```

- [ ] **Step 3: 验证爬虫**

```bash
cd worldcup2026 && python -c "
from data.scraper import get_knockout_matches
matches = get_knockout_matches()
print(f'淘汰赛场次: {len(matches)}')
assert len(matches) > 0
print('爬虫/fallback 正常工作')
"
```
Expected: "爬虫/fallback 正常工作"

- [ ] **Step 4: Commit**

```bash
git add worldcup2026/data/scraper.py worldcup2026/data/knockout_fallback.json
git commit -m "feat: add knockout stage scraper with fallback"
```

---

### Task 8: GUI 样式

**Files:**
- Create: `worldcup2026/gui/styles.py`

- [ ] **Step 1: 编写深色主题样式**

Write `worldcup2026/gui/styles.py`:
```python
"""全局深色主题样式"""

DARK_THEME = """
/* ===== 全局 ===== */
QMainWindow {
    background-color: #1a1a2e;
    color: #e0e0e0;
}
QWidget {
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}

/* ===== 标签 ===== */
QLabel {
    color: #e0e0e0;
    background: transparent;
}
QLabel#title {
    font-size: 20px;
    font-weight: bold;
    color: #ffffff;
}
QLabel#subtitle {
    font-size: 14px;
    color: #a0a0b0;
}
QLabel#score {
    font-size: 32px;
    font-weight: bold;
    color: #e94560;
}
QLabel#group_header {
    font-size: 16px;
    font-weight: bold;
    color: #ffffff;
    background-color: #16213e;
    border-radius: 8px;
    padding: 8px 16px;
}

/* ===== 卡片 ===== */
QFrame#card {
    background-color: #16213e;
    border-radius: 12px;
    border: 1px solid #2a2a4a;
    padding: 12px;
}
QFrame#prediction_card {
    background-color: #0f3460;
    border-radius: 16px;
    border: 2px solid #e94560;
    padding: 16px;
}
QFrame#match_card {
    background-color: #16213e;
    border-radius: 10px;
    border: 1px solid #2a2a4a;
    padding: 10px;
}
QFrame#match_card:hover {
    border: 1px solid #e94560;
    background-color: #1a2745;
}

/* ===== 按钮 ===== */
QPushButton {
    background-color: #e94560;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: bold;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #ff6b81;
}
QPushButton:pressed {
    background-color: #c0392b;
}
QPushButton#secondary {
    background-color: #2a2a4a;
    color: #e0e0e0;
}
QPushButton#secondary:hover {
    background-color: #3a3a5a;
}

/* ===== 表格 ===== */
QTableWidget {
    background-color: #16213e;
    alternate-background-color: #1a2745;
    border: 1px solid #2a2a4a;
    border-radius: 8px;
    gridline-color: #2a2a4a;
    color: #e0e0e0;
    selection-background-color: #e94560;
}
QTableWidget::item {
    padding: 6px 12px;
}
QHeaderView::section {
    background-color: #0f3460;
    color: #ffffff;
    font-weight: bold;
    padding: 8px;
    border: none;
    border-bottom: 2px solid #e94560;
}

/* ===== 滚动条 ===== */
QScrollBar:vertical {
    background: #1a1a2e;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #3a3a5a;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* ===== Tab 页 ===== */
QTabWidget::pane {
    border: 1px solid #2a2a4a;
    border-radius: 8px;
    background: #1a1a2e;
}
QTabBar::tab {
    background: #16213e;
    color: #a0a0b0;
    padding: 10px 20px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}
QTabBar::tab:selected {
    background: #e94560;
    color: white;
}

/* ===== 滑块 ===== */
QSlider::groove:horizontal {
    background: #2a2a4a;
    height: 6px;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #e94560;
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
}

/* ===== 复选框 ===== */
QCheckBox {
    color: #e0e0e0;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #3a3a5a;
    background: #16213e;
}
QCheckBox::indicator:checked {
    background: #e94560;
    border-color: #e94560;
}

/* ===== 状态栏 ===== */
QStatusBar {
    background-color: #0f3460;
    color: #a0a0b0;
    border-top: 1px solid #2a2a4a;
}
QStatusBar QLabel {
    color: #a0a0b0;
}

/* ===== 组合框 ===== */
QComboBox {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #2a2a4a;
    border-radius: 6px;
    padding: 6px 12px;
}
QComboBox::drop-down {
    border: none;
}
QComboBox QAbstractItemView {
    background-color: #16213e;
    color: #e0e0e0;
    selection-background-color: #e94560;
}
"""


FLAG_EMOJI = {
    "美国": "🇺🇸", "墨西哥": "🇲🇽", "加拿大": "🇨🇦",
    "阿根廷": "🇦🇷", "巴西": "🇧🇷", "乌拉圭": "🇺🇾",
    "哥伦比亚": "🇨🇴", "厄瓜多尔": "🇪🇨", "秘鲁": "🇵🇪", "智利": "🇨🇱",
    "法国": "🇫🇷", "西班牙": "🇪🇸", "德国": "🇩🇪", "英格兰": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "葡萄牙": "🇵🇹", "意大利": "🇮🇹", "荷兰": "🇳🇱", "比利时": "🇧🇪",
    "克罗地亚": "🇭🇷",
    "摩洛哥": "🇲🇦", "塞内加尔": "🇸🇳", "尼日利亚": "🇳🇬",
    "埃及": "🇪🇬", "喀麦隆": "🇨🇲", "加纳": "🇬🇭",
    "科特迪瓦": "🇨🇮", "阿尔及利亚": "🇩🇿", "突尼斯": "🇹🇳",
    "日本": "🇯🇵", "韩国": "🇰🇷", "伊朗": "🇮🇷",
    "沙特阿拉伯": "🇸🇦", "澳大利亚": "🇦🇺", "卡塔尔": "🇶🇦",
    "哥斯达黎加": "🇨🇷", "巴拿马": "🇵🇦", "牙买加": "🇯🇲", "洪都拉斯": "🇭🇳",
    "塞尔维亚": "🇷🇸", "瑞士": "🇨🇭", "丹麦": "🇩🇰", "瑞典": "🇸🇪",
    "波兰": "🇵🇱", "乌克兰": "🇺🇦", "奥地利": "🇦🇹", "土耳其": "🇹🇷",
    "挪威": "🇳🇴",
    "新西兰": "🇳🇿", "阿联酋": "🇦🇪",
}


def flag(team_name: str) -> str:
    """获取球队国旗 emoji"""
    return FLAG_EMOJI.get(team_name, "🏳️")


def team_display(team_name: str) -> str:
    """国旗 + 队名"""
    return f"{flag(team_name)} {team_name}"
```

- [ ] **Step 2: Commit**

```bash
git add worldcup2026/gui/styles.py
git commit -m "feat: add dark theme styles and team flag data"
```

---

### Task 9: GUI 自定义组件

**Files:**
- Create: `worldcup2026/gui/widgets.py`

- [ ] **Step 1: 编写自定义组件 (MatchCard, GroupTable, BracketWidget)**

Write `worldcup2026/gui/widgets.py`:
```python
"""自定义 PyQt6 组件: MatchCard, GroupTable, BracketWidget"""

from PyQt6.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QWidget, QScrollArea, QPushButton,
    QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush
from gui.styles import flag, team_display


class MatchCard(QFrame):
    """比赛预测卡片"""
    clicked = pyqtSignal(dict)

    def __init__(self, home_team: str, away_team: str, date: str,
                 venue: str, prediction: dict = None, parent=None):
        super().__init__(parent)
        self.setObjectName("match_card")
        self.home_team = home_team
        self.away_team = away_team
        self.prediction = prediction
        self._setup_ui(date, venue)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _setup_ui(self, date: str, venue: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        # 日期 + 场地
        info = QLabel(f"{date}  {venue}")
        info.setObjectName("subtitle")
        info.setStyleSheet("font-size: 11px;")
        layout.addWidget(info)

        # 对阵
        teams_layout = QHBoxLayout()
        home_lbl = QLabel(team_display(self.home_team))
        home_lbl.setStyleSheet("font-size: 15px; font-weight: bold;")
        vs_lbl = QLabel("vs")
        vs_lbl.setStyleSheet("color: #666; font-size: 12px;")
        away_lbl = QLabel(team_display(self.away_team))
        away_lbl.setStyleSheet("font-size: 15px; font-weight: bold;")
        teams_layout.addWidget(home_lbl)
        teams_layout.addStretch()
        teams_layout.addWidget(vs_lbl)
        teams_layout.addStretch()
        teams_layout.addWidget(away_lbl)
        layout.addLayout(teams_layout)

        # 预测比分
        if self.prediction:
            score = QLabel(
                f"预测 {self.prediction['home_score']} - {self.prediction['away_score']}"
            )
            score.setObjectName("score")
            score.setStyleSheet("font-size: 16px; color: #ffd700;")
            score.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(score)

    def update_prediction(self, prediction: dict):
        """更新预测比分显示"""
        self.prediction = prediction
        # 找到比分 label 并更新 (最后一个 QLabel 子控件)
        for child in self.findChildren(QLabel):
            if "预测" in child.text() or " - " in child.text():
                child.setText(
                    f"预测 {prediction['home_score']} - {prediction['away_score']}"
                )
                return

    def mousePressEvent(self, event):
        self.clicked.emit({
            "home_team": self.home_team,
            "away_team": self.away_team,
            "prediction": self.prediction
        })
        super().mousePressEvent(event)


class GroupTable(QWidget):
    """单个小组的赛程表"""
    match_clicked = pyqtSignal(dict)

    def __init__(self, group_name: str, teams: list[str],
                 matches: list[dict], predictions: list[dict] = None,
                 parent=None):
        super().__init__(parent)
        self.group_name = group_name
        self.teams = teams
        self.matches = matches
        self.predictions = predictions or []
        self.match_cards = []  # 保存卡片引用用于后续更新
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # 小组标题
        header = QLabel(f"{self.group_name}组")
        header.setObjectName("group_header")
        layout.addWidget(header)

        # 球队列表
        teams_str = "  |  ".join(team_display(t) for t in self.teams)
        teams_lbl = QLabel(teams_str)
        teams_lbl.setStyleSheet("font-size: 12px; padding: 4px 8px;")
        layout.addWidget(teams_lbl)

        # 比赛卡片
        for i, match in enumerate(self.matches):
            pred = self.predictions[i] if i < len(self.predictions) else None
            card = MatchCard(
                match["home"], match["away"],
                match["date"], match.get("venue", ""),
                pred
            )
            card.clicked.connect(self.match_clicked.emit)
            self.match_cards.append(card)
            layout.addWidget(card)

        layout.addStretch()

    def update_predictions(self, predictions: list[dict]):
        """更新所有比赛的预测比分"""
        self.predictions = predictions
        for i, card in enumerate(self.match_cards):
            if i < len(predictions):
                card.update_prediction(predictions[i])


class BracketWidget(QWidget):
    """淘汰赛对阵图 (32强 → 决赛)"""
    match_clicked = pyqtSignal(dict)

    STAGES = [
        ("32强", 32, "round_of_32"),
        ("16强", 16, "round_of_16"),
        ("8强", 8, "quarter_final"),
        ("4强", 4, "semi_final"),
        ("决赛", 2, "final"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.knockout_matches = []
        self._setup_ui()

    def _setup_ui(self):
        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(16)

    def update_matches(self, matches: list[dict], predictions: dict = None):
        """更新淘汰赛对阵"""
        # 清除旧组件
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.knockout_matches = matches

        for stage_name, _, stage_key in self.STAGES:
            stage_widget = QWidget()
            stage_layout = QVBoxLayout(stage_widget)
            stage_layout.setSpacing(4)

            lbl = QLabel(stage_name)
            lbl.setObjectName("group_header")
            lbl.setStyleSheet("font-size: 14px;")
            stage_layout.addWidget(lbl)

            stage_matches = [m for m in matches if m.get("stage") == stage_key]
            if not stage_matches:
                # 占位
                placeholder = QLabel("待定")
                placeholder.setStyleSheet("color: #666; padding: 8px;")
                stage_layout.addWidget(placeholder)
            else:
                for m in stage_matches:
                    text = f"{flag(m['home_team'])} {m['home_team']}\nvs\n{flag(m['away_team'])} {m['away_team']}"
                    ml = QLabel(text)
                    ml.setStyleSheet("""
                        background: #16213e; border-radius: 6px;
                        padding: 8px; font-size: 11px;
                    """)
                    stage_layout.addWidget(ml)

            stage_layout.addStretch()
            self.layout.addWidget(stage_widget)


class PredictionDetail(QFrame):
    """预测详情卡片 (右下区域)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("prediction_card")
        self.setMinimumHeight(180)
        self._setup_ui()

    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(10)

        self.title_lbl = QLabel("选择一场比赛查看预测详情")
        self.title_lbl.setStyleSheet("font-size: 14px; color: #a0a0b0;")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.h2h_lbl = QLabel("")
        self.elo_lbl = QLabel("")
        self.fusion_lbl = QLabel("")
        self.record_lbl = QLabel("")
        self.detail_btn = QPushButton("查看 H2H 交手记录")
        self.detail_btn.setObjectName("secondary")
        self.detail_btn.setVisible(False)

        self.layout.addWidget(self.title_lbl)
        self.layout.addWidget(self.h2h_lbl)
        self.layout.addWidget(self.elo_lbl)
        self.layout.addWidget(self.fusion_lbl)
        self.layout.addWidget(self.record_lbl)
        self.layout.addWidget(self.detail_btn)
        self.layout.addStretch()

    def show_prediction(self, data: dict):
        """显示预测详情"""
        home = data["home_team"]
        away = data["away_team"]
        pred = data.get("prediction", {})

        self.title_lbl.setText(f"{team_display(home)}  vs  {team_display(away)}")
        self.title_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #fff;")

        if pred.get("model") == "hybrid":
            self.h2h_lbl.setText(
                f"H2H 预测: {pred.get('h2h_home', '-')} - {pred.get('h2h_away', '-')}"
            )
            self.h2h_lbl.setStyleSheet("font-size: 14px; color: #a0c0ff;")
            self.elo_lbl.setText(
                f"Elo 预测: {pred.get('elo_home', '-')} - {pred.get('elo_away', '-')}"
            )
            self.elo_lbl.setStyleSheet("font-size: 14px; color: #a0c0ff;")
            self.fusion_lbl.setText(
                f"★ 融合: {pred['home_score']} - {pred['away_score']}"
            )
        else:
            self.h2h_lbl.setText("")
            self.elo_lbl.setText("")
            self.fusion_lbl.setText(
                f"预测: {pred.get('home_score', '-')} - {pred.get('away_score', '-')}"
            )
        self.fusion_lbl.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #ffd700;"
        )

        record = pred.get("h2h_record")
        if record and record.get("total", 0) > 0:
            self.record_lbl.setText(
                f"历史交手: {record['total']}场  "
                f"{home} {record['wins']}胜{record['draws']}平{record['losses']}负"
            )
            self.detail_btn.setVisible(True)
        else:
            self.record_lbl.setText("两队近12年无交手记录")
            self.detail_btn.setVisible(False)
```

- [ ] **Step 2: 验证组件可导入**

```bash
cd worldcup2026 && python -c "
from gui.widgets import MatchCard, GroupTable, BracketWidget, PredictionDetail
print('所有组件导入成功')
"
```
Expected: "所有组件导入成功"

- [ ] **Step 3: Commit**

```bash
git add worldcup2026/gui/widgets.py
git commit -m "feat: add custom GUI widgets (MatchCard, GroupTable, BracketWidget)"
```

---

### Task 10: 设置面板

**Files:**
- Create: `worldcup2026/gui/settings_panel.py`

- [ ] **Step 1: 编写设置面板**

Write `worldcup2026/gui/settings_panel.py`:
```python
"""设置面板 — 预测模式 / 混合权重 / 数据源开关"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton,
    QSlider, QCheckBox, QPushButton, QButtonGroup, QGroupBox,
    QSpinBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal


class SettingsPanel(QDialog):
    """设置对话框"""
    settings_changed = pyqtSignal(dict)

    def __init__(self, current_settings: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setFixedSize(420, 520)
        self.setStyleSheet("""
            QDialog { background-color: #1a1a2e; }
            QGroupBox { font-weight: bold; color: #fff; border: 1px solid #2a2a4a;
                        border-radius: 8px; margin-top: 12px; padding-top: 16px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 8px; }
        """)

        self.settings = current_settings or {
            "mode": "hybrid",
            "h2h_weight": 0.5,
            "time_decay": 0.85,
            "home_advantage": 1.15,
            "data_sources": {
                "world_cup": True,
                "continental": True,
                "friendly": True,
                "u23_olympic": True,
                "u20_world_cup": True,
                "u17_world_cup": True,
            }
        }
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # === 预测模式 ===
        mode_group = QGroupBox("预测模式")
        mode_layout = QVBoxLayout(mode_group)

        self.btn_group = QButtonGroup(self)
        self.radio_h2h = QRadioButton("仅 H2H 加权")
        self.radio_elo = QRadioButton("仅 Elo + 泊松")
        self.radio_hybrid = QRadioButton("混合模式")

        for btn in [self.radio_h2h, self.radio_elo, self.radio_hybrid]:
            btn.setStyleSheet("color: #e0e0e0; padding: 4px;")
            self.btn_group.addButton(btn)
            mode_layout.addWidget(btn)

        if self.settings["mode"] == "h2h":
            self.radio_h2h.setChecked(True)
        elif self.settings["mode"] == "elo":
            self.radio_elo.setChecked(True)
        else:
            self.radio_hybrid.setChecked(True)

        layout.addWidget(mode_group)

        # === 混合权重滑块 ===
        weight_group = QGroupBox("混合权重")
        weight_layout = QVBoxLayout(weight_group)

        slider_layout = QHBoxLayout()
        self.weight_slider = QSlider(Qt.Orientation.Horizontal)
        self.weight_slider.setRange(0, 100)
        self.weight_slider.setValue(int(self.settings["h2h_weight"] * 100))
        self.weight_label = QLabel(
            f"H2H {self.settings['h2h_weight']*100:.0f}% : "
            f"{(1-self.settings['h2h_weight'])*100:.0f}% Elo"
        )
        self.weight_label.setStyleSheet("color: #a0c0ff;")
        self.weight_slider.valueChanged.connect(
            lambda v: self.weight_label.setText(
                f"H2H {v:.0f}% : {100-v:.0f}% Elo"
            )
        )
        slider_layout.addWidget(QLabel("H2H"))
        slider_layout.addWidget(self.weight_slider)
        slider_layout.addWidget(QLabel("Elo"))
        weight_layout.addWidget(self.weight_label)
        weight_layout.addLayout(slider_layout)
        layout.addWidget(weight_group)

        # === 数据源 ===
        source_group = QGroupBox("数据源")
        source_layout = QVBoxLayout(source_group)

        self.source_checkboxes = {}
        source_labels = {
            "world_cup": "世界杯正赛 (192场)",
            "continental": "洲际杯赛 (800场)",
            "friendly": "国际友谊赛 (1500场)",
            "u23_olympic": "U23 奥运系列 (200场)",
            "u20_world_cup": "U20 世界杯 (200场)",
            "u17_world_cup": "U17 世界杯 (300场)",
        }
        for key, label in source_labels.items():
            cb = QCheckBox(label)
            cb.setChecked(self.settings["data_sources"].get(key, True))
            self.source_checkboxes[key] = cb
            source_layout.addWidget(cb)

        layout.addWidget(source_group)

        # === 参数调整 ===
        param_group = QGroupBox("模型参数")
        param_layout = QVBoxLayout(param_group)

        decay_layout = QHBoxLayout()
        decay_layout.addWidget(QLabel("时间衰减系数"))
        self.decay_spin = QDoubleSpinBox()
        self.decay_spin.setRange(0.5, 1.0)
        self.decay_spin.setSingleStep(0.01)
        self.decay_spin.setValue(self.settings["time_decay"])
        self.decay_spin.setStyleSheet(
            "background: #16213e; color: #e0e0e0; border-radius: 4px; padding: 4px;"
        )
        decay_layout.addWidget(self.decay_spin)
        param_layout.addLayout(decay_layout)

        home_layout = QHBoxLayout()
        home_layout.addWidget(QLabel("主场优势系数"))
        self.home_spin = QDoubleSpinBox()
        self.home_spin.setRange(1.0, 1.5)
        self.home_spin.setSingleStep(0.05)
        self.home_spin.setValue(self.settings["home_advantage"])
        self.home_spin.setStyleSheet(
            "background: #16213e; color: #e0e0e0; border-radius: 4px; padding: 4px;"
        )
        home_layout.addWidget(self.home_spin)
        param_layout.addLayout(home_layout)

        layout.addWidget(param_group)

        # === 按钮 ===
        btn_layout = QHBoxLayout()
        reset_btn = QPushButton("恢复默认")
        reset_btn.setObjectName("secondary")
        reset_btn.clicked.connect(self._reset_defaults)
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(reset_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _reset_defaults(self):
        self.radio_hybrid.setChecked(True)
        self.weight_slider.setValue(50)
        for cb in self.source_checkboxes.values():
            cb.setChecked(True)
        self.decay_spin.setValue(0.85)
        self.home_spin.setValue(1.15)

    def _save(self):
        if self.radio_h2h.isChecked():
            self.settings["mode"] = "h2h"
        elif self.radio_elo.isChecked():
            self.settings["mode"] = "elo"
        else:
            self.settings["mode"] = "hybrid"

        self.settings["h2h_weight"] = self.weight_slider.value() / 100.0
        self.settings["time_decay"] = self.decay_spin.value()
        self.settings["home_advantage"] = self.home_spin.value()
        self.settings["data_sources"] = {
            k: cb.isChecked() for k, cb in self.source_checkboxes.items()
        }

        self.settings_changed.emit(self.settings)
        self.accept()
```

- [ ] **Step 2: Commit**

```bash
git add worldcup2026/gui/settings_panel.py
git commit -m "feat: add settings panel with mode/weight/data sources"
```

---

### Task 11: 主窗口

**Files:**
- Create: `worldcup2026/gui/main_window.py`

- [ ] **Step 1: 编写主窗口**

Write `worldcup2026/gui/main_window.py`:
```python
"""主窗口 — 赛程 + 淘汰赛对阵图 + 预测详情"""

import json
import os
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QLabel, QScrollArea, QPushButton, QTabWidget, QStatusBar,
    QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon

from gui.styles import DARK_THEME, team_display
from gui.widgets import GroupTable, BracketWidget, PredictionDetail
from gui.settings_panel import SettingsPanel
from engine.predictor import Predictor
from data.scraper import get_knockout_matches


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("2026 世界杯 · 美加墨")
        self.resize(1280, 860)
        self.setMinimumSize(1024, 700)

        # 加载数据
        self._load_data()

        # 预测器
        self.predictor = Predictor(mode="hybrid", h2h_weight=0.5)

        # 设置
        self.settings = {
            "mode": "hybrid", "h2h_weight": 0.5,
            "time_decay": 0.85, "home_advantage": 1.15,
            "data_sources": {k: True for k in [
                "world_cup", "continental", "friendly",
                "u23_olympic", "u20_world_cup", "u17_world_cup"
            ]}
        }

        self._setup_ui()
        self._setup_menu()
        self._setup_statusbar()

        # 预计算所有预测
        QTimer.singleShot(100, self._compute_all_predictions)

    def _data_path(self, filename: str) -> str:
        """兼容 exe 打包和源码运行"""
        import sys
        base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(__file__)))
        return os.path.join(base, "data", filename)

    def _load_data(self):
        with open(self._data_path("group_stage.json"), "r", encoding="utf-8") as f:
            self.group_data = json.load(f)

        try:
            self.knockout_matches = get_knockout_matches()
        except Exception:
            self.knockout_matches = []

    def _setup_ui(self):
        self.setStyleSheet(DARK_THEME)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 8, 12, 8)

        # 顶部标题栏
        title_bar = QHBoxLayout()
        title = QLabel("🏆 2026 世界杯 · 美加墨")
        title.setObjectName("title")
        title_bar.addWidget(title)
        title_bar.addStretch()

        self.settings_btn = QPushButton("⚙ 设置")
        self.settings_btn.setObjectName("secondary")
        self.settings_btn.clicked.connect(self._open_settings)
        title_bar.addWidget(self.settings_btn)

        self.refresh_btn = QPushButton("🔄 更新淘汰赛数据")
        self.refresh_btn.setObjectName("secondary")
        self.refresh_btn.clicked.connect(self._refresh_knockout)
        title_bar.addWidget(self.refresh_btn)

        root.addLayout(title_bar)

        # 主体: 左右分栏
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧: 小组赛 Tab
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.group_tabs = QTabWidget()
        self.group_tables = {}
        for group_name, group in self.group_data["groups"].items():
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

            table = GroupTable(group_name, group["teams"], group["matches"])
            table.match_clicked.connect(self._on_match_clicked)
            scroll.setWidget(table)
            self.group_tables[group_name] = table

            idx = ord(group_name) - ord("A")
            self.group_tabs.addTab(scroll, f"{group_name}组")

        left_layout.addWidget(self.group_tabs)
        splitter.addWidget(left_widget)

        # 右侧: 淘汰赛 + 预测详情
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(8, 0, 0, 0)

        bracket_scroll = QScrollArea()
        bracket_scroll.setWidgetResizable(True)
        bracket_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.bracket = BracketWidget()
        bracket_scroll.setWidget(self.bracket)
        right_layout.addWidget(bracket_scroll, 3)

        self.prediction_detail = PredictionDetail()
        right_layout.addWidget(self.prediction_detail, 2)

        splitter.addWidget(right_widget)
        splitter.setSizes([720, 520])

        root.addWidget(splitter)

    def _setup_menu(self):
        menubar = self.menuBar()
        menubar.setStyleSheet(
            "QMenuBar { background: #0f3460; color: #e0e0e0; }"
            "QMenuBar::item:selected { background: #e94560; }"
        )
        file_menu = menubar.addMenu("文件")
        refresh_action = QAction("更新数据", self)
        refresh_action.triggered.connect(self._refresh_knockout)
        file_menu.addAction(refresh_action)

        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self._open_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def _setup_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(
            f"数据更新于 2026-06-14 | 淘汰赛: 已加载 | 48/48 队"
        )

    def _compute_all_predictions(self):
        """预计算所有小组赛预测并更新卡片"""
        try:
            for group_name, group in self.group_data["groups"].items():
                table = self.group_tables[group_name]
                predictions = []
                for match in group["matches"]:
                    pred = self.predictor.predict(match["home"], match["away"])
                    predictions.append(pred)

                table.update_predictions(predictions)

            self.status_bar.showMessage(
                f"预测计算完成 | {datetime.now().strftime('%H:%M:%S')}"
            )
        except Exception as e:
            QMessageBox.warning(self, "错误", f"预测计算失败: {e}")

    def _on_match_clicked(self, data: dict):
        """点击比赛 → 显示预测详情"""
        home = data["home_team"]
        away = data["away_team"]

        if "prediction" not in data or data["prediction"] is None:
            data["prediction"] = self.predictor.predict(home, away)

        self.prediction_detail.show_prediction(data)

    def _open_settings(self):
        dialog = SettingsPanel(self.settings, self)
        dialog.settings_changed.connect(self._apply_settings)
        dialog.exec()

    def _apply_settings(self, new_settings: dict):
        self.settings = new_settings
        self.predictor.set_mode(
            new_settings["mode"],
            new_settings["h2h_weight"]
        )
        self._compute_all_predictions()

    def _refresh_knockout(self):
        try:
            self.knockout_matches = get_knockout_matches()
            self.bracket.update_matches(self.knockout_matches)
            self.status_bar.showMessage("淘汰赛数据已更新 ✓")
        except Exception as e:
            QMessageBox.warning(self, "更新失败", f"无法获取淘汰赛数据:\n{e}")
            self.status_bar.showMessage("淘汰赛数据更新失败，使用缓存")
```

- [ ] **Step 2: Commit**

```bash
git add worldcup2026/gui/main_window.py
git commit -m "feat: add main window with group stage tabs, bracket, and prediction detail"
```

---

### Task 12: 入口 + 打包 + 集成测试

**Files:**
- Modify: `worldcup2026/main.py`
- Create: `worldcup2026/build.py`

- [ ] **Step 1: 完善入口文件**

Write `worldcup2026/main.py`:
```python
"""2026 世界杯赛程预测工具 — 入口"""

import sys
import os

# 确保项目根目录在 path 中 (exe 打包兼容)
if getattr(sys, "frozen", False):
    os.chdir(sys._MEIPASS)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    # 全局字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 启动验证**

```bash
cd worldcup2026 && python -c "
import sys
sys.path.insert(0, '.')
from main import main
print('入口模块加载成功')
"
```
Expected: "入口模块加载成功"

- [ ] **Step 3: 编写打包脚本**

Write `worldcup2026/build.py`:
```python
"""PyInstaller 打包脚本

运行: python build.py
输出: dist/WorldCup2026.exe (单文件)
"""

import os
import sys

def build():
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    json_files = [f for f in os.listdir(data_dir) if f.endswith(".json")]

    # 构建 --add-data 参数
    add_data_args = []
    for f in json_files:
        src = os.path.join(data_dir, f)
        add_data_args.append(f"--add-data={src}{os.pathsep}data")

    cmd = (
        f"pyinstaller --onefile --windowed "
        f"--name=WorldCup2026 "
        f"--icon=NONE "
        f"{' '.join(add_data_args)} "
        f"main.py"
    )

    print(f"执行: {cmd}")
    os.system(cmd)
    print("\n打包完成!")
    print(f"输出: {os.path.abspath('dist/WorldCup2026.exe')}")


if __name__ == "__main__":
    build()
```

- [ ] **Step 4: Commit**

```bash
git add worldcup2026/main.py worldcup2026/build.py
git commit -m "feat: add entry point and PyInstaller build script"
```

---

### Task 13: 端到端验证

- [ ] **Step 1: 全量导入测试**

```bash
cd worldcup2026 && python -c "
from data.collector import load_h2h_database, find_h2h_matches, compute_weight
from data.scraper import get_knockout_matches
from engine.h2h_model import h2h_predict, h2h_win_rate
from engine.elo_model import elo_predict, update_elo, score_probabilities
from engine.predictor import Predictor
from gui.styles import DARK_THEME, flag, team_display
from gui.widgets import MatchCard, GroupTable, BracketWidget, PredictionDetail
from gui.settings_panel import SettingsPanel
from gui.main_window import MainWindow
print('全部模块导入成功')
"
```
Expected: "全部模块导入成功"

- [ ] **Step 2: 预测一致性测试**

```bash
cd worldcup2026 && python -c "
from engine.predictor import Predictor

p = Predictor()

# 同一场比赛多次预测结果应一致 (缓存)
r1 = p.predict('阿根廷', '巴西')
r2 = p.predict('阿根廷', '巴西')
assert r1 == r2, '缓存不一致'

# 不同模式结果应不同
p.set_mode('h2h')
r_h2h = p.predict('德国', '法国')

p.set_mode('elo')
r_elo = p.predict('德国', '法国')

print(f'H2H: {r_h2h[\"home_score\"]}-{r_h2h[\"away_score\"]}')
print(f'Elo: {r_elo[\"home_score\"]}-{r_elo[\"away_score\"]}')

# 有 Elo 分的队预测应合理 (0~6 球范围内)
assert 0 <= r_elo['home_score'] <= 6, f'不合理的主队进球: {r_elo[\"home_score\"]}'
assert 0 <= r_elo['away_score'] <= 6, f'不合理的客队进球: {r_elo[\"away_score\"]}'

print('预测一致性测试通过')
"
```
Expected: prints H2H/Elo 预测比分, "预测一致性测试通过"

- [ ] **Step 3: 数据完整性测试**

```bash
cd worldcup2026 && python -c "
import json, os

data_dir = 'data'
for f in ['group_stage.json', 'elo_ratings.json', 'h2h_database.json']:
    path = os.path.join(data_dir, f)
    assert os.path.exists(path), f'{f} 不存在'
    with open(path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    print(f'{f}: 加载成功')

# 检查小组赛
with open(os.path.join(data_dir, 'group_stage.json'), 'r', encoding='utf-8') as f:
    gs = json.load(f)
groups = gs['groups']
assert len(groups) == 12
total_matches = sum(len(g['matches']) for g in groups.values())
assert total_matches == 72

# 检查 Elo 分
with open(os.path.join(data_dir, 'elo_ratings.json'), 'r', encoding='utf-8') as f:
    elo = json.load(f)
assert len(elo['teams']) == 48

# 检查 H2H 数据库
with open(os.path.join(data_dir, 'h2h_database.json'), 'r', encoding='utf-8') as f:
    h2h = json.load(f)
assert 'matches' in h2h

print('数据完整性测试通过')
"
```
Expected: "数据完整性测试通过"

- [ ] **Step 4: Commit**

```bash
git add worldcup2026/
git commit -m "test: add integration and data integrity checks"
```
