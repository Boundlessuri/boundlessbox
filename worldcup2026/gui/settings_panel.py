"""设置面板"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton,
    QSlider, QCheckBox, QPushButton, QButtonGroup, QGroupBox,
    QDoubleSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal


class SettingsPanel(QDialog):
    settings_changed = pyqtSignal(dict)

    def __init__(self, current_settings=None, parent=None):
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
            "mode": "hybrid", "h2h_weight": 0.5, "time_decay": 0.85,
            "home_advantage": 1.15,
            "data_sources": {"world_cup": True, "continental": True, "friendly": True,
                             "u23_olympic": True, "u20_world_cup": True, "u17_world_cup": True}
        }
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

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
        if self.settings["mode"] == "h2h": self.radio_h2h.setChecked(True)
        elif self.settings["mode"] == "elo": self.radio_elo.setChecked(True)
        else: self.radio_hybrid.setChecked(True)
        layout.addWidget(mode_group)

        weight_group = QGroupBox("混合权重")
        weight_layout = QVBoxLayout(weight_group)
        slider_layout = QHBoxLayout()
        self.weight_slider = QSlider(Qt.Orientation.Horizontal)
        self.weight_slider.setRange(0, 100)
        self.weight_slider.setValue(int(self.settings["h2h_weight"] * 100))
        self.weight_label = QLabel(f"H2H {self.settings['h2h_weight']*100:.0f}% : {(1-self.settings['h2h_weight'])*100:.0f}% Elo")
        self.weight_label.setStyleSheet("color: #a0c0ff;")
        self.weight_slider.valueChanged.connect(
            lambda v: self.weight_label.setText(f"H2H {v:.0f}% : {100-v:.0f}% Elo"))
        slider_layout.addWidget(QLabel("H2H"))
        slider_layout.addWidget(self.weight_slider)
        slider_layout.addWidget(QLabel("Elo"))
        weight_layout.addWidget(self.weight_label)
        weight_layout.addLayout(slider_layout)
        layout.addWidget(weight_group)

        source_group = QGroupBox("数据源")
        source_layout = QVBoxLayout(source_group)
        self.source_checkboxes = {}
        for key, label in [
            ("world_cup", "世界杯正赛 (192场)"),
            ("continental", "洲际杯赛 (800场)"),
            ("friendly", "国际友谊赛 (1500场)"),
            ("u23_olympic", "U23 奥运系列 (200场)"),
            ("u20_world_cup", "U20 世界杯 (200场)"),
            ("u17_world_cup", "U17 世界杯 (300场)")
        ]:
            cb = QCheckBox(label)
            cb.setChecked(self.settings["data_sources"].get(key, True))
            self.source_checkboxes[key] = cb
            source_layout.addWidget(cb)
        layout.addWidget(source_group)

        param_group = QGroupBox("模型参数")
        param_layout = QVBoxLayout(param_group)
        for name, key, rng, step in [("时间衰减系数", "time_decay", (0.5, 1.0), 0.01),
                                       ("主场优势系数", "home_advantage", (1.0, 1.5), 0.05)]:
            row = QHBoxLayout()
            row.addWidget(QLabel(name))
            spin = QDoubleSpinBox()
            spin.setRange(*rng)
            spin.setSingleStep(step)
            spin.setValue(self.settings[key])
            spin.setStyleSheet("background: #16213e; color: #e0e0e0; border-radius: 4px; padding: 4px;")
            setattr(self, f"{key}_spin", spin)
            row.addWidget(spin)
            param_layout.addLayout(row)
        layout.addWidget(param_group)

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
        self.time_decay_spin.setValue(0.85)
        self.home_advantage_spin.setValue(1.15)

    def _save(self):
        if self.radio_h2h.isChecked(): mode = "h2h"
        elif self.radio_elo.isChecked(): mode = "elo"
        else: mode = "hybrid"
        self.settings["mode"] = mode
        self.settings["h2h_weight"] = self.weight_slider.value() / 100.0
        self.settings["time_decay"] = self.time_decay_spin.value()
        self.settings["home_advantage"] = self.home_advantage_spin.value()
        self.settings["data_sources"] = {k: cb.isChecked() for k, cb in self.source_checkboxes.items()}
        self.settings_changed.emit(self.settings)
        self.accept()
