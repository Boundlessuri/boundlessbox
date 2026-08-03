"""GPU Peak Throughput Benchmark Engine.

OpenCL-based benchmark that measures FP32, FP16, and INT8 peak throughput
by scaling work-size until throughput plateaus.
"""

import sys
import time
import numpy as np
import pyopencl as cl
from PySide6.QtCore import QObject, Signal, QThread, Qt, QRectF, QSize
from PySide6.QtGui import QPainter, QColor, QFont, QLinearGradient
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QSizePolicy,
    QMainWindow, QHBoxLayout, QComboBox, QCheckBox, QPushButton,
    QLabel, QProgressBar, QMessageBox, QApplication, QGroupBox
)

# ---------------------------------------------------------------------------
# OpenCL kernel constants
# ---------------------------------------------------------------------------

KERNEL_FP32 = r"""
__kernel void bench_fp32(__global float *restrict a,
                          __global const float *restrict b,
                          const int iters) {
    int gid = get_global_id(0);
    float acc = a[gid];
    float mul = b[gid];
    for (int i = 0; i < iters; i++) {
        acc = fma(acc, mul, 1.0f);
    }
    a[gid] = acc;
}
"""

KERNEL_FP16 = r"""
#pragma OPENCL EXTENSION cl_khr_fp16 : enable
__kernel void bench_fp16(__global half *restrict a,
                          __global const half *restrict b,
                          const int iters) {
    int gid = get_global_id(0);
    half acc = a[gid];
    half mul = b[gid];
    half one = (half)1.0f;
    for (int i = 0; i < iters; i++) {
        acc = fma(acc, mul, one);
    }
    a[gid] = acc;
}
"""

KERNEL_INT8 = r"""
__kernel void bench_int8(__global int *restrict a,
                          __global const int *restrict b,
                          const int iters) {
    int gid = get_global_id(0);
    int acc = a[gid];
    int mul_packed = b[gid];
    for (int i = 0; i < iters; i++) {
        // char4 dot-product: each int holds 4 packed int8 values
        char4 va = as_char4(acc);
        char4 vb = as_char4(mul_packed);
        int dot = va.s0 * vb.s0 + va.s1 * vb.s1 + va.s2 * vb.s2 + va.s3 * vb.s3;
        acc += dot;
    }
    a[gid] = acc;
}
"""


# ---------------------------------------------------------------------------
# BenchmarkEngine
# ---------------------------------------------------------------------------

class BenchmarkEngine(QObject):
    """Measures GPU peak throughput across FP32, FP16, and INT8 precisions.

    Uses progressive work-size doubling until throughput plateaus, then
    reports the median of the last 3 rounds near the peak.
    """

    progress = Signal(str, str, float)   # precision, status, gflops
    finished = Signal(dict)              # {precision: peak_gflops}
    error = Signal(str)                  # error message
    device_info = Signal(str)            # human-readable device info

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cancel = False

    def cancel(self):
        """Request cancellation of the running benchmark."""
        self._cancel = True

    @staticmethod
    def list_devices():
        """Return [(platform_name, device_name, platform_idx, device_idx), ...]"""
        devices = []
        for pi, platform in enumerate(cl.get_platforms()):
            for di, device in enumerate(platform.get_devices()):
                devices.append((platform.name, device.name, pi, di))
        return devices

    @staticmethod
    def check_fp16_support(platform_idx, device_idx):
        """Return True if cl_khr_fp16 extension is available."""
        try:
            platform = cl.get_platforms()[platform_idx]
            device = platform.get_devices()[device_idx]
            return "cl_khr_fp16" in device.extensions
        except Exception:
            return False

    def run_benchmark(self, platform_idx, device_idx, precisions):
        """Main entry point — called from worker thread via signal/slot."""
        self._cancel = False
        try:
            platform = cl.get_platforms()[platform_idx]
            device = platform.get_devices()[device_idx]
            ctx = cl.Context([device])
            queue = cl.CommandQueue(
                ctx, properties=cl.command_queue_properties.PROFILING_ENABLE
            )
        except Exception as e:
            self.error.emit(f"Failed to open device: {e}")
            self.finished.emit({})
            return

        self.device_info.emit(f"{platform.name} - {device.name}")

        kernels = {
            "FP32": KERNEL_FP32,
            "FP16": KERNEL_FP16,
            "INT8": KERNEL_INT8,
        }

        results = {}
        for precision in precisions:
            if self._cancel:
                break
            try:
                peak = self._bench_precision(ctx, queue, kernels[precision], precision)
                results[precision] = peak
            except cl.RuntimeError as e:
                self.error.emit(f"{precision} kernel failed: {e}")
                results[precision] = 0.0
            except Exception as e:
                self.error.emit(f"{precision} benchmark error: {e}")
                results[precision] = 0.0

        self.finished.emit(results)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _bench_precision(self, ctx, queue, kernel_src, precision):
        """Scale work-size up until throughput plateaus, return peak GFLOPS."""
        # Build program
        try:
            prg = cl.Program(ctx, kernel_src)
            prg.build()
        except cl.RuntimeError:
            build_log = "unknown"
            try:
                build_log = prg.get_build_info(
                    ctx.devices[0], cl.program_build_info.LOG
                )
            except Exception:
                pass
            raise cl.RuntimeError(f"Build error:\n{build_log}")

        kernel_name = f"bench_{precision.lower()}"
        kernel = getattr(prg, kernel_name)

        # Find peak by scaling
        work_sizes = [
            1024, 2048, 4096, 8192, 16384, 32768,
            65536, 131072, 262144, 524288, 1048576,
        ]
        peak_tp = 0.0
        peak_rounds = []  # last N rounds near peak

        for ws in work_sizes:
            if self._cancel:
                break
            try:
                tp = self._run_timed_round(queue, kernel, ws, precision)
            except cl.RuntimeError:
                # Work size too large for device, stop scaling
                break

            if tp > peak_tp:
                peak_tp = tp
                peak_rounds = [tp]
            elif peak_tp > 0:
                peak_rounds.append(tp)

            self.progress.emit(precision, f"{precision} work_size={ws}", tp)

            # If we've had 3 rounds all below 95% of peak, we found the peak
            if len(peak_rounds) >= 4:
                recent_max = max(peak_rounds[-3:])
                if recent_max < peak_tp * 0.95:
                    break

        # Median of peak-area rounds
        if peak_rounds:
            peak_rounds.sort()
            median = peak_rounds[len(peak_rounds) // 2]
            self.progress.emit(precision, f"{precision} peak", median)
            return round(median, 2)
        return round(peak_tp, 2)

    def _run_timed_round(self, queue, kernel, work_size, precision):
        """Run one timed round, return sustained GFLOPS."""
        dtype = np.int32 if precision == "INT8" else np.float32
        a = (
            np.random.randn(work_size).astype(dtype)
            if precision != "INT8"
            else np.random.randint(-128, 128, size=work_size, dtype=np.int32)
        )
        b = (
            np.random.randn(work_size).astype(dtype)
            if precision != "INT8"
            else np.random.randint(-128, 128, size=work_size, dtype=np.int32)
        )

        mf = cl.mem_flags
        a_buf = cl.Buffer(queue.context, mf.READ_WRITE | mf.COPY_HOST_PTR, hostbuf=a)
        b_buf = cl.Buffer(queue.context, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=b)

        # Auto-tune iterations so kernel runs 10-50ms
        iters = 100
        kernel(queue, (work_size,), None, a_buf, b_buf, np.int32(iters))
        queue.finish()

        t_start = time.perf_counter()
        kernel(queue, (work_size,), None, a_buf, b_buf, np.int32(iters))
        queue.finish()
        elapsed = time.perf_counter() - t_start

        # Adjust iters if elapsed outside 10-50ms
        target_ms = 25
        if elapsed > 0:
            factor = (target_ms / 1000.0) / elapsed
            iters = max(100, int(iters * factor))
            iters = min(iters, 1000000)
            # Always re-measure with adjusted iters so elapsed matches iters
            t_start = time.perf_counter()
            kernel(queue, (work_size,), None, a_buf, b_buf, np.int32(iters))
            queue.finish()
            elapsed = time.perf_counter() - t_start

        # Ops per work-item per iteration
        if precision == "INT8":
            ops_per_item_per_iter = 8  # 4 muls + 4 adds via char4 dot
        else:
            ops_per_item_per_iter = 1  # 1 FMA -> 2 FLOP, but we count FLOP
        flop_per_iter = 2 if precision != "INT8" else 8

        total_flops = float(work_size) * iters * flop_per_iter
        gflops = total_flops / elapsed / 1e9

        return gflops


# ---------------------------------------------------------------------------
# BarChartWidget
# ---------------------------------------------------------------------------

class BarChartWidget(QWidget):
    """Horizontal bar chart showing benchmark results."""

    # Color per precision
    COLORS = {
        "FP32": QColor("#4CAF50"),
        "FP16": QColor("#2196F3"),
        "INT8": QColor("#FF9800"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._results = {}
        self.setMinimumSize(400, 180)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_results(self, results):
        """Set the results dict and trigger repaint."""
        self._results = dict(results)
        self.update()

    def minimumSizeHint(self):
        """Return the minimum size hint for layout."""
        return QSize(400, 200)

    def paintEvent(self, event):
        if not self._results:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        bar_h = 36
        gap = 16
        top_margin = 20
        label_width = 60
        value_width = 160
        chart_left = label_width + 10
        chart_right = w - value_width - 20
        chart_width = chart_right - chart_left

        # Find max for scaling
        max_val = max(self._results.values()) if self._results else 1.0
        max_val = max_val * 1.05 if max_val > 0 else 1.0  # 5% headroom

        # Title
        font_title = QFont()
        font_title.setPointSize(12)
        font_title.setBold(True)
        painter.setFont(font_title)
        painter.setPen(QColor("#e0e0e0"))
        painter.drawText(QRectF(0, 4, w, 22), Qt.AlignCenter, "GPU Peak Throughput Benchmark")

        font_label = QFont()
        font_label.setPointSize(10)
        font_value = QFont()
        font_value.setPointSize(10)
        font_value.setBold(True)

        painter.setFont(font_label)

        items = list(self._results.items())
        # Sort by value descending for visual clarity
        items.sort(key=lambda x: x[1], reverse=True)

        for i, (precision, gflops) in enumerate(items):
            y = top_margin + i * (bar_h + gap)

            # Precision label
            painter.setPen(QColor("#cccccc"))
            painter.drawText(QRectF(0, y, label_width, bar_h),
                             Qt.AlignRight | Qt.AlignVCenter, precision)

            # Bar background
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(60, 60, 60))
            painter.drawRoundedRect(QRectF(chart_left, y + 4, chart_width, bar_h - 8), 4, 4)

            # Bar fill with gradient
            bar_w = int(chart_width * (gflops / max_val))
            color = self.COLORS.get(precision, QColor("#888888"))
            grad = QLinearGradient(chart_left, 0, chart_left + bar_w, 0)
            grad.setColorAt(0.0, color.lighter(120))
            grad.setColorAt(1.0, color)

            painter.setBrush(grad)
            painter.drawRoundedRect(QRectF(chart_left, y + 4, bar_w, bar_h - 8), 4, 4)

            # Value text after bar
            painter.setPen(QColor("#ffffff"))
            painter.setFont(font_value)
            unit = "GOPS" if precision == "INT8" else "GFLOPS"
            painter.drawText(QRectF(chart_right + 10, y, value_width - 10, bar_h),
                             Qt.AlignLeft | Qt.AlignVCenter,
                             f"{gflops:,.1f} {unit}")

        painter.end()


# ---------------------------------------------------------------------------
# MainWindow
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    """Full application window for the GPU Peak Throughput Benchmark."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("GPU Peak Throughput Benchmark")
        self.setMinimumSize(640, 480)
        self.resize(700, 520)
        self._engine = None
        self._thread = None

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 12, 16, 16)

        # --- Device selector ---
        dev_group = QGroupBox("Device")
        dev_layout = QHBoxLayout(dev_group)
        self._combo = QComboBox()
        self._combo.setMinimumWidth(300)
        dev_layout.addWidget(self._combo)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_devices)
        dev_layout.addWidget(refresh_btn)
        dev_layout.addStretch()
        layout.addWidget(dev_group)

        # --- Precision checkboxes ---
        prec_group = QGroupBox("Precisions to Test")
        prec_layout = QHBoxLayout(prec_group)
        self._cb_fp32 = QCheckBox("FP32")
        self._cb_fp32.setChecked(True)
        self._cb_fp16 = QCheckBox("FP16")
        self._cb_fp16.setChecked(True)
        self._cb_int8 = QCheckBox("INT8")
        self._cb_int8.setChecked(True)
        prec_layout.addWidget(self._cb_fp32)
        prec_layout.addWidget(self._cb_fp16)
        prec_layout.addWidget(self._cb_int8)
        prec_layout.addStretch()
        layout.addWidget(prec_group)

        # --- Progress ---
        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet("color: #aaa;")
        layout.addWidget(self._status_label)
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)  # indeterminate by default
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        # --- Buttons ---
        btn_layout = QHBoxLayout()
        self._start_btn = QPushButton("Start Benchmark")
        self._start_btn.setMinimumHeight(36)
        self._start_btn.clicked.connect(self._start_benchmark)
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.clicked.connect(self._cancel_benchmark)
        btn_layout.addWidget(self._start_btn)
        btn_layout.addWidget(self._cancel_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # --- Bar chart ---
        self._chart = BarChartWidget()
        layout.addWidget(self._chart, stretch=1)

        # Apply dark theme
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #2b2b2b;
                color: #e0e0e0;
                font-size: 13px;
            }
            QGroupBox {
                border: 1px solid #555;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 14px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }
            QComboBox {
                background: #3c3c3c;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QCheckBox {
                spacing: 6px;
            }
            QPushButton {
                background: #3c3c3c;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px 16px;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #4a4a4a;
            }
            QPushButton:pressed {
                background: #555;
            }
            QPushButton:disabled {
                color: #666;
            }
            QProgressBar {
                border: 1px solid #555;
                border-radius: 4px;
                text-align: center;
                background: #3c3c3c;
            }
            QProgressBar::chunk {
                background: #2196F3;
                border-radius: 3px;
            }
        """)

        # Populate devices on startup
        self._refresh_devices()

    def _refresh_devices(self):
        self._combo.clear()
        try:
            devices = BenchmarkEngine.list_devices()
            if not devices:
                self._combo.addItem("No OpenCL devices found")
                return
            for plat_name, dev_name, pi, di in devices:
                self._combo.addItem(f"[{plat_name}] {dev_name}", (pi, di))
            # Check FP16 support on first device
            if devices:
                pi0, di0 = devices[0][2], devices[0][3]
                has_fp16 = BenchmarkEngine.check_fp16_support(pi0, di0)
                if not has_fp16:
                    self._cb_fp16.setChecked(False)
                    self._cb_fp16.setEnabled(False)
                    self._cb_fp16.setToolTip("Device does not support cl_khr_fp16")
                else:
                    self._cb_fp16.setEnabled(True)
                    self._cb_fp16.setChecked(True)
                    self._cb_fp16.setToolTip("")
        except Exception as e:
            self._combo.addItem(f"Error: {e}")

    def _start_benchmark(self):
        idx = self._combo.currentData()
        if idx is None:
            QMessageBox.warning(self, "No Device", "Select a device first.")
            return
        pi, di = idx

        precisions = []
        if self._cb_fp32.isChecked():
            precisions.append("FP32")
        if self._cb_fp16.isChecked():
            precisions.append("FP16")
        if self._cb_int8.isChecked():
            precisions.append("INT8")
        if not precisions:
            QMessageBox.warning(self, "No Precision", "Select at least one precision.")
            return

        self._start_btn.setEnabled(False)
        self._cancel_btn.setEnabled(True)
        self._progress.setVisible(True)
        self._progress.setRange(0, 0)  # indeterminate
        self._status_label.setText("Starting...")

        # Setup worker thread
        self._thread = QThread()
        self._engine = BenchmarkEngine()
        self._engine.moveToThread(self._thread)

        self._engine.progress.connect(self._on_progress)
        self._engine.finished.connect(self._on_finished)
        self._engine.error.connect(self._on_error)
        self._thread.started.connect(
            lambda: self._engine.run_benchmark(pi, di, precisions)
        )
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _on_progress(self, precision, status, gflops):
        unit = "GOPS" if precision == "INT8" else "GFLOPS"
        self._status_label.setText(f"[{precision}] {status}: {gflops:,.1f} {unit}")

    def _on_finished(self, results):
        self._start_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)
        self._progress.setVisible(False)
        if results:
            self._status_label.setText("Benchmark complete")
            self._chart.set_results(results)
        else:
            self._status_label.setText("No results (cancelled)")
        if self._thread:
            self._thread.quit()
            self._thread.wait()
            self._thread = None
            self._engine = None

    def _on_error(self, msg):
        self._status_label.setText(f"Error: {msg}")
        QMessageBox.critical(self, "Benchmark Error", msg)

    def _cancel_benchmark(self):
        if self._engine:
            self._engine.cancel()
        self._cancel_btn.setEnabled(False)
        self._status_label.setText("Cancelling...")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("GPU Benchmark")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
