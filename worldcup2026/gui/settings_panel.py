"""设置面板"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton,
    QSlider, QPushButton, QButtonGroup, QGroupBox,
    QDoubleSpinBox, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QMargins


SOURCE_LABELS = [
    ("world_cup", "世界杯正赛 (192场)"),
    ("continental", "洲际杯赛 (800场)"),
    ("friendly", "国际友谊赛 (1500场)"),
    ("u23_olympic", "U23 奥运系列 (200场)"),
    ("u20_world_cup", "U20 世界杯 (200场)"),
    ("u17_world_cup", "U17 世界杯 (300场)"),
]

PARAMS = [
    ("时间衰减系数", "time_decay", (0.5, 1.0), 0.01),
    ("主场优势系数", "home_advantage", (1.0, 1.5), 0.05),
]

DIALOG_STYLE = """
QDialog { background-color: #1a1a2e; }
QGroupBox { font-weight: bold; color: #fff; border: 1px solid #2a2a4a;
            border-radius: 8px; margin-top: 12px; padding-top: 20px; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 8px; }
QRadioButton { color: #ffffff; font-size: 14px; padding: 4px 0px; }
QRadioButton::indicator { width: 18px; height: 18px; border-radius: 9px;
                          border: 2px solid #555; background: #16213e; }
QRadioButton::indicator:checked { background: #e94560; border-color: #e94560; }
QListWidget { background-color: #0d1b36; border: 1px solid #2a2a4a;
              border-radius: 8px; padding: 4px; outline: none; }
QListWidget::item { color: #ffffff; padding: 8px 6px; border-bottom: 1px solid #1a2745; }
QListWidget::item:hover { background-color: #16213e; }
QLabel { color: #e0e0e0; font-size: 13px; }
QDoubleSpinBox { background: #16213e; color: #ffffff; font-size: 14px;
                 border-radius: 4px; padding: 4px 8px; border: 1px solid #555; }
"""


class SettingsPanel(QDialog):
    settings_changed = pyqtSignal(dict)

    def __init__(self, current_settings=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setFixedSize(440, 560)
        self.setStyleSheet(DIALOG_STYLE)
        self.settings = current_settings or {
            "mode": "hybrid", "h2h_weight": 0.5, "time_decay": 0.85,
            "home_advantage": 1.15,
            "data_sources": {"world_cup": True, "continental": True, "friendly": True,
                             "u23_olympic": True, "u20_world_cup": True, "u17_world_cup": True}
        }
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # --- 预测模式 ---
        mode_group = QGroupBox("预测模式")
        mode_layout = QVBoxLayout(mode_group)
        self.btn_group = QButtonGroup(self)
        self.radio_h2h = QRadioButton("仅 H2H 加权")
        self.radio_elo = QRadioButton("仅 Elo + 泊松")
        self.radio_hybrid = QRadioButton("混合模式")
        for btn in [self.radio_h2h, self.radio_elo, self.radio_hybrid]:
            self.btn_group.addButton(btn)
            mode_layout.addWidget(btn)
        if self.settings["mode"] == "h2h": self.radio_h2h.setChecked(True)
        elif self.settings["mode"] == "elo": self.radio_elo.setChecked(True)
        else: self.radio_hybrid.setChecked(True)
        layout.addWidget(mode_group)

        # --- 混合权重 ---
        weight_group = QGroupBox("混合权重")
        weight_layout = QVBoxLayout(weight_group)
        self.weight_label = QLabel(
            f"H2H {self.settings['h2h_weight']*100:.0f}% : {(1-self.settings['h2h_weight'])*100:.0f}% Elo"
        )
        self.weight_label.setStyleSheet("color: #ffd700; font-size: 14px; font-weight: bold;")
        weight_layout.addWidget(self.weight_label)
        slider_row = QHBoxLayout()
        self.weight_slider = QSlider(Qt.Orientation.Horizontal)
        self.weight_slider.setRange(0, 100)
        self.weight_slider.setValue(int(self.settings["h2h_weight"] * 100))
        self.weight_slider.valueChanged.connect(
            lambda v: self.weight_label.setText(f"H2H {v:.0f}% : {100-v:.0f}% Elo"))
        for text in ["H2H", "Elo"]:
            lbl = QLabel(text)
            lbl.setStyleSheet("color: #fff; font-size: 13px;")
            slider_row.addWidget(lbl)
            if text == "H2H":
                slider_row.addWidget(self.weight_slider)
        weight_layout.addLayout(slider_row)
        layout.addWidget(weight_group)

        # --- 数据源 (QListWidget with checkable items) ---
        source_group = QGroupBox("数据源")
        source_layout = QVBoxLayout(source_group)
        self.source_list = QListWidget()
        self.source_list.setMaximumHeight(180)
        self.source_items = {}
        for key, label in SOURCE_LABELS:
            item = QListWidgetItem(label)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            checked = self.settings["data_sources"].get(key, True)
            item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, key)
            item.setSizeHint(item.sizeHint().grownBy(QMargins(0, 6, 0, 6)))
            self.source_list.addItem(item)
            self.source_items[key] = item
        source_layout.addWidget(self.source_list)
        layout.addWidget(source_group)

        # --- 模型参数 ---
        param_group = QGroupBox("模型参数")
        param_layout = QVBoxLayout(param_group)
        for name, key, rng, step in PARAMS:
            row = QHBoxLayout()
            name_lbl = QLabel(name)
            name_lbl.setStyleSheet("color: #fff; font-size: 13px;")
            row.addWidget(name_lbl)
            spin = QDoubleSpinBox()
            spin.setRange(*rng)
            spin.setSingleStep(step)
            spin.setValue(self.settings[key])
            spin.setStyleSheet(
                "background: #16213e; color: #fff; font-size: 14px;"
                "border-radius: 4px; padding: 4px 8px; border: 1px solid #555;"
            )
            setattr(self, f"{key}_spin", spin)
            row.addWidget(spin)
            param_layout.addLayout(row)
        layout.addWidget(param_group)

        # --- 按钮 ---
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
        for item in self.source_items.values():
            item.setCheckState(Qt.CheckState.Checked)
        self.time_decay_spin.setValue(0.85)
        self.home_advantage_spin.setValue(1.15)

    def _save(self):
        if self.radio_h2h.isChecked(): self.settings["mode"] = "h2h"
        elif self.radio_elo.isChecked(): self.settings["mode"] = "elo"
        else: self.settings["mode"] = "hybrid"
        self.settings["h2h_weight"] = self.weight_slider.value() / 100.0
        self.settings["time_decay"] = self.time_decay_spin.value()
        self.settings["home_advantage"] = self.home_advantage_spin.value()
        self.settings["data_sources"] = {}
        for key, item in self.source_items.items():
            self.settings["data_sources"][key] = (
                item.checkState() == Qt.CheckState.Checked
            )
        self.settings_changed.emit(self.settings)
        self.accept()
