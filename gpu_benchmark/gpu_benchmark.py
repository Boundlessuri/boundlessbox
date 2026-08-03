"""GPU Peak Throughput Benchmark Engine.

OpenCL-based benchmark that measures FP32, FP16, and INT8 peak throughput
by scaling work-size until throughput plateaus.
"""

import sys
import time
import numpy as np
import pyopencl as cl
from PySide6.QtCore import QObject, Signal, QThread

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
                build_log = prg.get_build_info(ctx.devices[0]).build_log
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

            if factor > 1.5 or factor < 0.67:
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
