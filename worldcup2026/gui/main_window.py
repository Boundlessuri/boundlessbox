"""主窗口 — 赛程 + 淘汰赛对阵图 + 预测详情"""

import json, os, sys
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QLabel, QScrollArea, QPushButton, QTabWidget, QStatusBar,
    QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction

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
        self._load_data()
        self.predictor = Predictor(mode="hybrid", h2h_weight=0.5)
        self.settings = {"mode": "hybrid", "h2h_weight": 0.5, "time_decay": 0.85,
                         "home_advantage": 1.15,
                         "data_sources": {"world_cup": True, "continental": True, "friendly": True,
                                          "u23_olympic": True, "u20_world_cup": True, "u17_world_cup": True}}
        self._setup_ui()
        self._setup_menu()
        self._setup_statusbar()
        QTimer.singleShot(200, self._compute_all_predictions)

    def _data_path(self, filename):
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

        title_bar = QHBoxLayout()
        title = QLabel("🏆 2026 世界杯 · 美加墨")
        title.setObjectName("title")
        title_bar.addWidget(title)
        title_bar.addStretch()
        self.settings_btn = QPushButton("⚙ 设置")
        self.settings_btn.setObjectName("secondary")
        self.settings_btn.clicked.connect(self._open_settings)
        title_bar.addWidget(self.settings_btn)
        self.refresh_btn = QPushButton("🔄 更新淘汰赛")
        self.refresh_btn.setObjectName("secondary")
        self.refresh_btn.clicked.connect(self._refresh_knockout)
        title_bar.addWidget(self.refresh_btn)
        root.addLayout(title_bar)

        splitter = QSplitter(Qt.Orientation.Horizontal)

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

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(8, 0, 0, 0)
        bracket_scroll = QScrollArea()
        bracket_scroll.setWidgetResizable(True)
        bracket_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.bracket = BracketWidget()
        bracket_scroll.setWidget(self.bracket)
        self.bracket.update_matches(self.knockout_matches)
        right_layout.addWidget(bracket_scroll, 3)
        self.prediction_detail = PredictionDetail()
        right_layout.addWidget(self.prediction_detail, 2)
        splitter.addWidget(right_widget)
        splitter.setSizes([720, 520])
        root.addWidget(splitter)

    def _setup_menu(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("QMenuBar { background: #0f3460; color: #e0e0e0; } QMenuBar::item:selected { background: #e94560; }")
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
        self.status_bar.showMessage("数据更新于 2026-06-14 | 淘汰赛: 已加载 | 48/48 队")

    def _compute_all_predictions(self):
        try:
            for group_name, group in self.group_data["groups"].items():
                table = self.group_tables[group_name]
                predictions = []
                for match in group["matches"]:
                    pred = self.predictor.predict(match["home"], match["away"])
                    predictions.append(pred)
                table.update_predictions(predictions)
            self.status_bar.showMessage(f"预测计算完成 | {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"预测计算失败: {e}")

    def _on_match_clicked(self, data):
        home = data["home_team"]
        away = data["away_team"]
        if "prediction" not in data or data["prediction"] is None:
            data["prediction"] = self.predictor.predict(home, away)
        self.prediction_detail.show_prediction(data)

    def _open_settings(self):
        dialog = SettingsPanel(self.settings, self)
        dialog.settings_changed.connect(self._apply_settings)
        dialog.exec()

    def _apply_settings(self, new_settings):
        self.settings = new_settings
        self.predictor.set_mode(new_settings["mode"], new_settings["h2h_weight"])
        self._compute_all_predictions()

    def _refresh_knockout(self):
        try:
            self.knockout_matches = get_knockout_matches()
            self.bracket.update_matches(self.knockout_matches)
            self.status_bar.showMessage("淘汰赛数据已更新 ✓")
        except Exception as e:
            QMessageBox.warning(self, "更新失败", f"无法获取淘汰赛数据:\n{e}")
            self.status_bar.showMessage("淘汰赛数据更新失败，使用缓存")
