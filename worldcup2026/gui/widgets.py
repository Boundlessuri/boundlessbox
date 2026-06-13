"""自定义 PyQt6 组件: MatchCard, GroupTable, BracketWidget, PredictionDetail"""

from PyQt6.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QHBoxLayout,
    QWidget, QScrollArea, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal
from gui.styles import flag, team_display


class MatchCard(QFrame):
    clicked = pyqtSignal(dict)

    def __init__(self, home_team, away_team, date, venue, prediction=None, parent=None):
        super().__init__(parent)
        self.setObjectName("match_card")
        self.home_team = home_team
        self.away_team = away_team
        self.prediction = prediction
        self._setup_ui(date, venue)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _setup_ui(self, date, venue):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        info = QLabel(f"{date}  {venue}")
        info.setObjectName("subtitle")
        info.setStyleSheet("font-size: 11px;")
        layout.addWidget(info)
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
        self.score_lbl = QLabel("")
        if self.prediction:
            self.score_lbl.setText(f"预测 {self.prediction['home_score']} - {self.prediction['away_score']}")
            self.score_lbl.setStyleSheet("font-size: 16px; color: #ffd700;")
        else:
            self.score_lbl.setStyleSheet("font-size: 14px; color: #666;")
        self.score_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.score_lbl)

    def update_prediction(self, prediction):
        self.prediction = prediction
        if prediction:
            self.score_lbl.setText(f"预测 {prediction['home_score']} - {prediction['away_score']}")
            self.score_lbl.setStyleSheet("font-size: 16px; color: #ffd700;")

    def mousePressEvent(self, event):
        self.clicked.emit({
            "home_team": self.home_team, "away_team": self.away_team,
            "prediction": self.prediction
        })
        super().mousePressEvent(event)


class GroupTable(QWidget):
    match_clicked = pyqtSignal(dict)

    def __init__(self, group_name, teams, matches, predictions=None, parent=None):
        super().__init__(parent)
        self.group_name = group_name
        self.teams = teams
        self.matches = matches
        self.predictions = predictions or []
        self.match_cards = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        header = QLabel(f"{self.group_name}组")
        header.setObjectName("group_header")
        layout.addWidget(header)
        teams_str = "  |  ".join(team_display(t) for t in self.teams)
        teams_lbl = QLabel(teams_str)
        teams_lbl.setStyleSheet("font-size: 12px; padding: 4px 8px;")
        layout.addWidget(teams_lbl)
        for i, match in enumerate(self.matches):
            pred = self.predictions[i] if i < len(self.predictions) else None
            card = MatchCard(match["home"], match["away"], match["date"],
                             match.get("venue", ""), pred)
            card.clicked.connect(self.match_clicked.emit)
            self.match_cards.append(card)
            layout.addWidget(card)
        layout.addStretch()

    def update_predictions(self, predictions):
        self.predictions = predictions
        for i, card in enumerate(self.match_cards):
            if i < len(predictions):
                card.update_prediction(predictions[i])


class BracketWidget(QWidget):
    match_clicked = pyqtSignal(dict)

    STAGES = [
        ("32强", "round_of_32"),
        ("16强", "round_of_16"),
        ("8强", "quarter_final"),
        ("4强", "semi_final"),
        ("决赛", "final"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.knockout_matches = []
        self._setup_ui()

    def _setup_ui(self):
        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(12)

    def update_matches(self, matches, predictions=None):
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.knockout_matches = matches
        for stage_name, stage_key in self.STAGES:
            stage_widget = QWidget()
            stage_layout = QVBoxLayout(stage_widget)
            stage_layout.setSpacing(4)
            lbl = QLabel(stage_name)
            lbl.setObjectName("group_header")
            lbl.setStyleSheet("font-size: 13px;")
            stage_layout.addWidget(lbl)
            stage_matches = [m for m in matches if m.get("stage") == stage_key]
            if not stage_matches:
                placeholder = QLabel("待定")
                placeholder.setStyleSheet("color: #666; padding: 8px;")
                stage_layout.addWidget(placeholder)
            else:
                for m in stage_matches:
                    text = f"{flag(m['home_team'])} {m['home_team']}\n  vs\n{flag(m['away_team'])} {m['away_team']}"
                    ml = QLabel(text)
                    ml.setStyleSheet("background: #16213e; border-radius: 6px; padding: 8px; font-size: 10px;")
                    stage_layout.addWidget(ml)
            stage_layout.addStretch()
            self.layout.addWidget(stage_widget)


class PredictionDetail(QFrame):
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

    def show_prediction(self, data):
        home = data["home_team"]
        away = data["away_team"]
        pred = data.get("prediction", {})
        self.title_lbl.setText(f"{team_display(home)}  vs  {team_display(away)}")
        self.title_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #fff;")
        if pred.get("model") == "hybrid":
            self.h2h_lbl.setText(f"H2H 预测: {pred.get('h2h_home', '-')} - {pred.get('h2h_away', '-')}")
            self.h2h_lbl.setStyleSheet("font-size: 14px; color: #a0c0ff;")
            self.elo_lbl.setText(f"Elo 预测: {pred.get('elo_home', '-')} - {pred.get('elo_away', '-')}")
            self.elo_lbl.setStyleSheet("font-size: 14px; color: #a0c0ff;")
            self.fusion_lbl.setText(f"★ 融合: {pred['home_score']} - {pred['away_score']}")
            self.fusion_lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffd700;")
        else:
            self.h2h_lbl.setText("")
            self.elo_lbl.setText("")
            self.fusion_lbl.setText(f"预测: {pred.get('home_score', '-')} - {pred.get('away_score', '-')}")
            self.fusion_lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffd700;")
        record = pred.get("h2h_record")
        if record and record.get("total", 0) > 0:
            self.record_lbl.setText(f"历史交手: {record['total']}场  {home} {record['wins']}胜{record['draws']}平{record['losses']}负")
            self.detail_btn.setVisible(True)
        else:
            self.record_lbl.setText("两队近12年无交手记录")
            self.detail_btn.setVisible(False)
