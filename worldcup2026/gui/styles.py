"""全局深色主题样式 + 国旗映射"""

DARK_THEME = """
QMainWindow { background-color: #1a1a2e; color: #e0e0e0; }
QWidget { background-color: #1a1a2e; color: #e0e0e0; font-family: "Microsoft YaHei", "Segoe UI", sans-serif; font-size: 13px; }
QLabel { color: #e0e0e0; background: transparent; }
QLabel#title { font-size: 20px; font-weight: bold; color: #ffffff; }
QLabel#subtitle { font-size: 14px; color: #a0a0b0; }
QLabel#score { font-size: 32px; font-weight: bold; color: #e94560; }
QLabel#group_header { font-size: 16px; font-weight: bold; color: #ffffff; background-color: #16213e; border-radius: 8px; padding: 8px 16px; }
QFrame#card { background-color: #16213e; border-radius: 12px; border: 1px solid #2a2a4a; padding: 12px; }
QFrame#prediction_card { background-color: #0f3460; border-radius: 16px; border: 2px solid #e94560; padding: 16px; }
QFrame#match_card { background-color: #16213e; border-radius: 10px; border: 1px solid #2a2a4a; padding: 10px; }
QFrame#match_card:hover { border: 1px solid #e94560; background-color: #1a2745; }
QPushButton { background-color: #e94560; color: white; border: none; border-radius: 8px; padding: 8px 20px; font-weight: bold; font-size: 13px; }
QPushButton:hover { background-color: #ff6b81; }
QPushButton:pressed { background-color: #c0392b; }
QPushButton#secondary { background-color: #2a2a4a; color: #e0e0e0; }
QPushButton#secondary:hover { background-color: #3a3a5a; }
QTableWidget { background-color: #16213e; alternate-background-color: #1a2745; border: 1px solid #2a2a4a; border-radius: 8px; gridline-color: #2a2a4a; color: #e0e0e0; selection-background-color: #e94560; }
QTableWidget::item { padding: 6px 12px; }
QHeaderView::section { background-color: #0f3460; color: #ffffff; font-weight: bold; padding: 8px; border: none; border-bottom: 2px solid #e94560; }
QScrollBar:vertical { background: #1a1a2e; width: 8px; border-radius: 4px; }
QScrollBar::handle:vertical { background: #3a3a5a; border-radius: 4px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QTabWidget::pane { border: 1px solid #2a2a4a; border-radius: 8px; background: #1a1a2e; }
QTabBar::tab { background: #16213e; color: #a0a0b0; padding: 10px 20px; border-top-left-radius: 8px; border-top-right-radius: 8px; }
QTabBar::tab:selected { background: #e94560; color: white; }
QSlider::groove:horizontal { background: #2a2a4a; height: 6px; border-radius: 3px; }
QSlider::handle:horizontal { background: #e94560; width: 18px; height: 18px; margin: -6px 0; border-radius: 9px; }
QCheckBox { color: #e0e0e0; spacing: 8px; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 2px solid #3a3a5a; background: #16213e; }
QCheckBox::indicator:checked { background: #e94560; border-color: #e94560; }
QStatusBar { background-color: #0f3460; color: #a0a0b0; border-top: 1px solid #2a2a4a; }
QStatusBar QLabel { color: #a0a0b0; }
QComboBox { background-color: #16213e; color: #e0e0e0; border: 1px solid #2a2a4a; border-radius: 6px; padding: 6px 12px; }
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView { background-color: #16213e; color: #e0e0e0; selection-background-color: #e94560; }
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

def flag(team_name):
    return FLAG_EMOJI.get(team_name, "🏳️")

def team_display(team_name):
    return f"{flag(team_name)} {team_name}"
