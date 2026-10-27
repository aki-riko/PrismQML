# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Device-pixel-ratio gate for physical-pixel contracts. 设备像素比门禁。

The default `--qt-platform offscreen` runner uses a device pixel ratio of 1.0, where
every physical-pixel snap is an identity and coordinate scaling is a no-op. That
systematically hides a whole class of defects. Three real ones were found this way:
a 150px overshoot budget reached the screen as 152.67px, `syncPosition` rewrote an
adopted 75 into 75.3333, and a wheel hit test missed its target entirely. All three
passed offscreen and failed on a real 1.5 dpr window.

This gate re-runs the physical-pixel files with a guaranteed fractional device pixel
ratio so those contracts are exercised without depending on the host display. It is
additive: the offscreen suite keeps running unchanged.
默认 `--qt-platform offscreen` 运行器的设备像素比恒为 1.0, 此时所有物理像素对齐都是
恒等操作、坐标缩放也是空操作, 这会系统性地掩盖一整类缺陷。本轮就以此找到了三个真实
缺陷: 150px 越界预算以 152.67px 上屏、`syncPosition` 把采纳的 75 改写成 75.3333、
滚轮命中坐标完全偏离目标。三者都在 offscreen 通过, 在真实 1.5 设备像素比窗口上失败。

本门禁以保证非整数设备像素比的方式重跑物理像素相关文件, 使这些合同无需依赖宿主显示器
即可被覆盖。它是增量门禁: offscreen 套件照旧运行。
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# QT_SCALE_FACTOR multiplies the host ratio; it is not an absolute ratio. Verified on
# a 1.5 dpr desktop: unset gives 1.5, setting 1.5 gives 2.25. The gate therefore needs
# only "some factor that cannot land back on 1.0", and 1.5 satisfies that on every
# integer or fractional host ratio.
# QT_SCALE_FACTOR 是宿主比例的乘数, 不是绝对比例。在 1.5 设备像素比的桌面上实测: 未设置
# 时得到 1.5, 设为 1.5 时得到 2.25。因此门禁只需要"不可能落回 1.0 的某个因子", 而 1.5
# 对任何整数或小数宿主比例都满足。
DEFAULT_SCALE_FACTOR = "1.5"

# Files whose contracts are expressed in physical pixels, dpr-scaled coordinates, or
# fractional-pixel snapping. Each either reads devicePixelRatio or drives a code path
# that snaps to the physical grid.
# 合同以物理像素、按 dpr 缩放的坐标或小数像素对齐表达的文件。它们要么读取
# devicePixelRatio, 要么驱动会向物理网格对齐的代码路径。
PHYSICAL_PIXEL_FILES = (
    "tests/qml/test_scroll_bar_conventions.py",
    "tests/qml/test_smooth_scroll_physical_pixels.py",
    "tests/qml/test_border_physical_pixels.py",
    "tests/qml/test_line_chart_fractional_dpi_repaint.py",
    "tests/qml/test_dpi_manager_contract.py",
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scale-factor",
        default=DEFAULT_SCALE_FACTOR,
        help="QT_SCALE_FACTOR 乘数; 必须非正整数以避免落回 1.0",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=900.0,
        help="子进程超时秒数",
    )
    return parser


def _is_safe_factor(value: str) -> bool:
    """A factor is usable when it cannot multiply a host ratio back onto 1.0."""
    try:
        factor = float(value)
    except ValueError:
        return False
    if factor <= 0:
        return False
    # A factor of exactly 1.0 leaves the host ratio untouched, so a 1.0 host stays
    # blind. Anything else guarantees a fractional result on a 1.0 host.
    # 恰好为 1.0 的因子不改变宿主比例, 1.0 宿主仍然盲; 其余取值在 1.0 宿主上必然得到小数。
    return factor != 1.0


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if not _is_safe_factor(args.scale_factor):
        print(
            "[dpr-gate] refusing scale factor "
            f"{args.scale_factor}: it would leave a 1.0 host at 1.0 and hide "
            "physical-pixel defects"
        )
        return 2

    missing = [name for name in PHYSICAL_PIXEL_FILES if not (ROOT / name).is_file()]
    if missing:
        print("[dpr-gate] missing physical-pixel files:")
        for name in missing:
            print(f"  {name}")
        return 2

    from scripts.test_process import run_child  # noqa: PLC0415

    command = [
        sys.executable,
        "-X",
        "utf8",
        "-m",
        "pytest",
        *PHYSICAL_PIXEL_FILES,
        "-q",
        "--full-suite",
    ]
    print(
        f"[dpr-gate] scale_factor={args.scale_factor} "
        f"files={len(PHYSICAL_PIXEL_FILES)} "
        "(offscreen suite unchanged 默认套件不变)"
    )
    # The environment is process-wide on purpose: run_child gives no env hook, and
    # this script owns the whole process it is about to spawn.
    # 环境变量是本进程级的: run_child 不提供 env 参数, 而本脚本独占它即将派生的进程。
    os.environ["QT_SCALE_FACTOR"] = args.scale_factor
    return run_child(command, timeout=args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
