# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Page-switch collapse timeline probe. 页面切换收紧时间线探针。

Samples the lazy page-switch collapse on every presented frame of a visible
D3D11 window. Unlike the window exit, this collapse ends at navBarHeight/2
rather than zero, so pacing is normalised over the distance actually travelled.
在真实可见 D3D11 窗口上逐帧采样懒加载页面切换收紧。与窗口退场不同, 此收紧终点
是 navBarHeight/2 而非零, 因此节奏按实际走过的距离归一。
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

from PySide6.QtCore import (  # noqa: E402
    QEventLoop,
    QMetaObject,
    QObject,
    QTimer,
    QUrl,
)
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent  # noqa: E402
from PySide6.QtQuick import (  # noqa: E402
    QQuickWindow,
    QSGRendererInterface,
)

import prismqml  # noqa: E402
from prismqml import register_types  # noqa: E402
from prismqml.python.core import configure_qml_environment  # noqa: E402

SCENE_PATH = ROOT / "scripts/manual/page-switch-collapse-probe.qml"
SCENE_SOURCE = """
import QtQuick
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/controls/navigation/_internal"

Window {
    id: root
    objectName: "probeWindow"

    property bool targetLoaded: false
    property int activatedCount: 0

    function beginSwitch() {
        lazyHelper.showLoadingAndSwitch(1)
    }
    function markTargetLoaded() {
        targetLoaded = true
    }

    // Matches the window-exit probe so radii are directly comparable.
    // 与窗口退场探针同尺寸, 便于半径直接对比。
    width: 900
    height: 640
    visible: true
    color: "#18202b"
    title: "Page Switch Collapse Probe"

    Item {
        id: pageHost
        anchors.fill: parent

        Loader {
            id: firstPage
            objectName: "firstPage"
            anchors.fill: parent
            sourceComponent: Rectangle { color: "#b3d9485f" }
        }

        Loader {
            id: secondPage
            objectName: "secondPage"
            anchors.fill: parent
            sourceComponent: Rectangle { color: "#3487eb" }
            active: false
            visible: false
            opacity: 0
        }
    }

    PageTransition {
        id: sharedPageTransition
        objectName: "lazyPageCircleTransition"
        anchors.fill: parent
        animationType: Enums.lazyAnimation.lazy_circle
    }

    LazyLoadingHelper {
        id: lazyHelper
        objectName: "lazyHelper"

        anchors.fill: parent
        loaders: [firstPage, secondPage]
        targetIndex: 1
        currentVisibleIndex: 0
        loadingText: ""
        pageTransition: sharedPageTransition
        loaderActivationDelay:
            Enums.lazyLoadingTransitionMetrics.coverDuration
            + Enums.lazyLoadingTransitionMetrics.loaderActivationHeadroom
        isPageLoadedFunc: function(index) {
            return index === 1 && root.targetLoaded
        }
        isPageLoadFailedFunc: function(index) { return false }
        pageLoadErrorFunc: function(index) { return "" }
        diagnosticFunc: function(stage, index, details) {}
        activateLoaderFunc: function(index) {
            if (index === 1) {
                root.activatedCount += 1
                secondPage.active = true
            }
        }
        onLoadingComplete: function(targetIndex, previousIndex) {
            firstPage.visible = false
            secondPage.visible = true
            secondPage.opacity = 1
        }
    }
}
""".encode("utf-8")


def _easing_value(name: str) -> int:
    from PySide6.QtCore import QEasingCurve

    return getattr(QEasingCurve.Type, name).value


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 3_000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


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

    transition = window.findChild(QObject, "lazyPageCircleTransition")
    if transition is None:
        raise RuntimeError("lazyPageCircleTransition not found")
    if duration_override > 0:
        transition.setProperty("coverDuration", duration_override)
    if easing_override >= 0:
        transition.setProperty("coverEasing", easing_override)
    applied_duration = int(transition.property("coverDuration"))
    applied_easing = int(transition.property("coverEasing"))

    screen = window.screen()
    refresh_rate = float(screen.refreshRate()) if screen else 0.0

    start = time.perf_counter()
    raw: list[tuple] = []

    def _sample() -> None:
        raw.append(
            (
                time.perf_counter(),
                transition.property("progress"),
                transition.property("revealRadiusPixels"),
                transition.property("collapsing"),
                transition.property("running"),
            )
        )

    window.frameSwapped.connect(_sample)

    assert QMetaObject.invokeMethod(window, "beginSwitch")
    # Sample only the collapse leg; stop once it hands off to the wait stage.
    # 只采样收紧段; 交接到等待阶段即停。
    _wait_for(
        lambda: bool(transition.property("collapsing")) is True, timeout_ms=1_000
    )
    _wait_for(
        lambda: bool(transition.property("collapsing")) is False
        and len(raw) > 2,
        timeout_ms=3_000,
    )
    # One extra frame so the endpoint (running already false) is captured.
    # 多收一帧, 让终点(running 已为 false)被采到。
    _pump(60)
    window.frameSwapped.disconnect(_sample)

    frames = [
        {
            "t": round((stamp - start) * 1000.0, 2),
            "progress": round(float(progress), 4),
            "radius": round(float(radius), 2),
            "collapsing": bool(collapsing),
            "running": bool(running),
        }
        for stamp, progress, radius, collapsing, running in raw
    ]
    # The endpoint frame reports running=false, so take the collapsing leg up to
    # and including the first progress==0 frame. 终点帧 running 已为 false, 因此
    # 取收紧段直到首个 progress==0 帧(含)。
    collapse_frames = []
    for frame in frames:
        if not frame["collapsing"]:
            continue
        collapse_frames.append(frame)
        if frame["progress"] == 0.0:
            break
    minimum_radius = float(transition.property("revealMinimumRadiusPixels"))
    report = {
        "graphics_api": actual_api_name,
        "screen_refresh_rate_hz": refresh_rate,
        "applied_cover_duration_ms": applied_duration,
        "applied_cover_easing": applied_easing,
        "applied_cover_easing_name": easing_name or "default",
        "minimum_radius_pixels": round(minimum_radius, 2),
        "collapse_frame_count": len(collapse_frames),
        "collapse_frames": collapse_frames,
        "warnings": warnings,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))

    window.close()
    _pump(120)
    del window
    del component
    engine.deleteLater()
    _pump(120)
    del engine
    app.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
