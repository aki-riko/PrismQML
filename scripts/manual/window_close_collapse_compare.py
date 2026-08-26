# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Compare close collapse candidates on the real display. 真实屏幕上对比关闭收紧候选。

Runs window_close_collapse_probe once per candidate and reports how evenly the
radius is distributed across the frames the display actually presented.
每个候选运行一次探针, 报告半径在真实上屏帧之间的分布是否均匀。
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "scripts/manual/window_close_collapse_probe.py"
CANDIDATES = (
    (0, ""),
    (300, "InOutCubic"),
    (420, "InOutCubic"),
    (420, "OutCubic"),
    (480, "InOutCubic"),
    (480, "InOutQuad"),
)


def _parse_candidates(argv: list[str]) -> tuple[tuple[int, str], ...]:
    """Parse duration:easing pairs, defaulting to the built-in sweep.
    解析 duration:easing 对, 缺省用内置候选集。"""
    if not argv:
        return CANDIDATES
    parsed = []
    for token in argv:
        duration, _, easing = token.partition(":")
        parsed.append((int(duration), easing))
    return tuple(parsed)


def _run(duration: int, easing: str) -> dict:
    command = [sys.executable, str(PROBE)]
    if duration:
        command.append(str(duration))
        if easing:
            command.append(easing)
    completed = subprocess.run(
        command, cwd=str(ROOT), capture_output=True, text=True, timeout=180
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"probe failed for {duration}/{easing}: {completed.stderr[-2000:]}"
        )
    text = completed.stdout
    return json.loads(text[text.index("{"): text.rindex("}") + 1])


def main() -> int:
    candidates = _parse_candidates(sys.argv[1:])
    print(
        f"{'duration':>8} {'easing':>11} {'frames':>6} {'maxStep%':>9} "
        f"{'halfAt%':>8} {'steps (% of full radius)'}"
    )
    for duration, easing in candidates:
        report = _run(duration, easing)
        frames = report["dissolving_frames"]
        radii = [frame["radius"] for frame in frames]
        if not radii:
            print(f"{duration:>8} {easing or 'default':>11}   no dissolving frames")
            continue
        full = max(radii)
        steps = [
            round((earlier - later) / full * 100.0, 1)
            for earlier, later in zip(radii, radii[1:])
        ]
        # Fraction of the animation elapsed before radius first drops below half.
        # 半径首次低于一半时, 动画已经过去的时间比例。
        total_time = frames[-1]["t"] - frames[0]["t"]
        half_at = next(
            (
                round((frame["t"] - frames[0]["t"]) / total_time * 100.0)
                for frame in frames
                if frame["radius"] <= full / 2
            ),
            None,
        )
        print(
            f"{report['applied_cover_duration_ms']:>8} "
            f"{report['applied_cover_easing_name']:>11} "
            f"{len(frames):>6} {max(steps) if steps else 0:>9} "
            f"{str(half_at) + '%':>8} {steps}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
