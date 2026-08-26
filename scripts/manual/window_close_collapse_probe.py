# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Main-window close collapse timeline probe. 主窗口关闭收紧时间线探针。

Samples the real close PageTransition on every presented frame of a visible
D3D11 window, then reports the last progress/radius actually shown before the
HWND disappears. 在真实可见 D3D11 窗口上逐帧采样关闭过渡, 报告 HWND 消失前
最后真正上屏的 progress/radius。
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Keep bytecode under the shared artifact root before importing the package.
# 导入项目包前把字节码缓存集中到统一产物根目录。
_CACHE_PATH = Path(
    os.environ.get("PRISM_ARTIFACT_ROOT", str(ROOT / ".artifacts"))
) / "python" / "pycache"
os.environ["PYTHONPYCACHEPREFIX"] = str(_CACHE_PATH)
sys.pycache_prefix = str(_CACHE_PATH)

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent  # noqa: E402
from PySide6.QtQuick import (  # noqa: E402
    QQuickWindow,
    QSGRendererInterface,
)

import prismqml  # noqa: E402
from prismqml import register_types  # noqa: E402
from prismqml.python.core import configure_qml_environment  # noqa: E402

SCENE_PATH = ROOT / "scripts/manual/window-close-collapse-probe.qml"
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

WindowsCore {
    id: root
    objectName: "probeWindow"

    property int probeCoverDuration: 0
    property int probeCoverEasing: -1

    width: 900
    height: 640
    visible: true
    windowTitle: "Close Collapse Probe"

    Rectangle {
        anchors.fill: parent
        color: Enums.accentColor

        Text {
            anchors.centerIn: parent
            text: "close collapse probe"
            font.family: Enums.fontFamily
            font.pixelSize: Enums.typography.display
            color: Enums.accentForeground
        }
    }
}
"""
# Qt Easing enum values, read from QEasingCurve rather than assumed.
# Qt Easing 枚举取值, 由 QEasingCurve 读出而非猜测。
def _easing_value(name: str) -> int:
    from PySide6.QtCore import QEasingCurve

    return getattr(QEasingCurve.Type, name).value


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def main() -> int:
    duration_override = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    easing_name = sys.argv[2] if len(sys.argv) > 2 else ""
    easing_override = _easing_value(easing_name) if easing_name else -1

    package_path = Path(prismqml.__file__).resolve()
    package_path.relative_to(ROOT)

    configure_qml_environment(True)
    QQuickWindow.setGraphicsApi(QSGRendererInterface.GraphicsApi.Direct3D11)
    app = QGuiApplication(sys.argv)

    engine = QQmlApplicationEngine()
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    engine.addImportPath(str(ROOT / "prismqml"))

    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, QUrl.fromLocalFile(str(SCENE_PATH)))
    while component.status() == QQmlComponent.Status.Loading:
        _pump()
    if component.status() != QQmlComponent.Status.Ready:
        raise RuntimeError(
            "; ".join(error.toString() for error in component.errors())
        )
    window = component.create(engine.rootContext())
    if not isinstance(window, QQuickWindow):
        raise RuntimeError("probe window creation failed")

    window.show()
    window.requestActivate()
    _pump(600)

    actual_api = window.rendererInterface().graphicsApi()
    actual_api_name = getattr(actual_api, "name", str(actual_api))
    if actual_api_name != "Direct3D11":
        raise RuntimeError(f"probe requires Direct3D11; actual={actual_api_name}")

    transition = window.findChild(QObject, "windowClosePageTransition")
    if transition is None:
        raise RuntimeError("windowClosePageTransition not found")
    if duration_override > 0:
        transition.setProperty("coverDuration", duration_override)
    if easing_override >= 0:
        transition.setProperty("coverEasing", easing_override)
    applied_duration = int(transition.property("coverDuration"))
    applied_easing = int(transition.property("coverEasing"))

    screen = window.screen()
    refresh_rate = float(screen.refreshRate()) if screen else 0.0

    # Idle baseline: continuous repaint with no collapse, minimal sampling.
    # 空载基线: 仅连续重绘, 不做收紧, 采样开销最小。
    baseline: list[float] = []

    def _baseline_tick() -> None:
        baseline.append(time.perf_counter())
        window.requestUpdate()

    baseline_connection = window.frameSwapped.connect(_baseline_tick)
    window.requestUpdate()
    _pump(700)
    window.frameSwapped.disconnect(baseline_connection)
    baseline_intervals = [
        round((later - earlier) * 1000.0, 2)
        for earlier, later in zip(baseline, baseline[1:])
    ]
    _pump(120)

    start = time.perf_counter()
    # Raw cheap samples during the collapse; formatting happens afterwards.
    # 收紧期间只做极轻量原始采样, 事后再格式化。
    raw: list[tuple] = []
    events: list[dict] = []

    def _stamp() -> float:
        return round((time.perf_counter() - start) * 1000.0, 2)

    def _sample_swapped() -> None:
        raw.append(
            (
                "frameSwapped",
                time.perf_counter(),
                transition.property("progress"),
                transition.property("revealRadiusPixels"),
                transition.property("_dissolving"),
                window.isVisible(),
            )
        )

    def _sample_after() -> None:
        raw.append(
            (
                "afterFrameEnd",
                time.perf_counter(),
                transition.property("progress"),
                transition.property("revealRadiusPixels"),
                transition.property("_dissolving"),
                window.isVisible(),
            )
        )

    window.frameSwapped.connect(_sample_swapped)
    window.afterFrameEnd.connect(_sample_after)
    transition.collapseStarted.connect(
        lambda: events.append({"event": "collapseStarted", "t": _stamp()})
    )
    transition.collapseFinished.connect(
        lambda: events.append(
            {
                "event": "collapseFinished",
                "t": _stamp(),
                "progress": round(float(transition.property("progress")), 4),
            }
        )
    )
    window.visibleChanged.connect(
        lambda: events.append(
            {
                "event": "visibleChanged",
                "t": _stamp(),
                "visible": bool(window.isVisible()),
                "progress": round(float(transition.property("progress")), 4),
                "radius": round(
                    float(transition.property("revealRadiusPixels")), 2
                ),
            }
        )
    )

    events.append({"event": "close() issued", "t": _stamp()})
    accepted = window.close()
    events.append({"event": "close() returned", "t": _stamp(), "value": accepted})

    deadline = time.perf_counter() + 3.0
    while time.perf_counter() < deadline and window.isVisible():
        _pump(4)
    _pump(120)

    frames = [
        {
            "kind": kind,
            "t": round((stamp - start) * 1000.0, 2),
            "progress": round(float(progress), 4),
            "radius": round(float(radius), 2),
            "dissolving": bool(dissolving),
            "visible": bool(visible),
        }
        for kind, stamp, progress, radius, dissolving, visible in raw
    ]
    presented = [frame for frame in frames if frame["kind"] == "frameSwapped"]
    dissolving_frames = [frame for frame in presented if frame["dissolving"]]
    last_visible = [frame for frame in presented if frame["visible"]]
    collapse_intervals = [
        round(later["t"] - earlier["t"], 2)
        for earlier, later in zip(dissolving_frames, dissolving_frames[1:])
    ]
    baseline_sorted = sorted(baseline_intervals)
    report = {
        "graphics_api": actual_api_name,
        "screen_refresh_rate_hz": refresh_rate,
        "applied_cover_duration_ms": applied_duration,
        "applied_cover_easing": applied_easing,
        "applied_cover_easing_name": easing_name or "default",
        "idle_baseline_frame_count": len(baseline_intervals),
        "idle_baseline_median_ms": (
            baseline_sorted[len(baseline_sorted) // 2] if baseline_sorted else None
        ),
        "collapse_frame_intervals_ms": collapse_intervals,
        "presented_frame_count": len(presented),
        "dissolving_frame_count": len(dissolving_frames),
        "events": events,
        "dissolving_frames": dissolving_frames,
        "last_presented_visible_frame": last_visible[-1] if last_visible else None,
        "min_presented_progress_while_visible": (
            min(frame["progress"] for frame in last_visible)
            if last_visible
            else None
        ),
        "min_presented_radius_while_visible": (
            min(frame["radius"] for frame in last_visible) if last_visible else None
        ),
        "warnings": warnings,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

    window.deleteLater()
    component.deleteLater()
    engine.deleteLater()
    _pump()
    del app
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
