# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Progress ring reuse regressions. 进度环复用回归。"""

import os
from pathlib import Path
import re
import subprocess
import sys
import textwrap

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types

ROOT = Path(__file__).resolve().parents[2]
QML_ROOT = ROOT / "prismqml" / "PrismQML"
CANONICAL_RING = QML_ROOT / "controls" / "feedback" / "Progress" / "ProgressRing.qml"
LOADING_OVERLAY = QML_ROOT / "_internal" / "LoadingOverlay.qml"
LAZY_LOADING_HELPER = (
    QML_ROOT / "controls" / "navigation" / "_internal" / "LazyLoadingHelper.qml"
)
QML_PAGE = QML_ROOT / "controls" / "feedback" / "QMLPage.qml"
SPLASH_SCREEN = (
    QML_ROOT / "controls" / "feedback" / "SplashScreen" / "SplashScreen.qml"
)
RING_CONSUMERS = (
    LOADING_OVERLAY,
    QML_PAGE,
    QML_ROOT / "controls" / "buttons" / "Button" / "ButtonContent.qml",
    SPLASH_SCREEN,
    QML_ROOT / "controls" / "feedback" / "State" / "ResultState.qml",
    QML_ROOT / "controls" / "feedback" / "State" / "StateWidget.qml",
    QML_ROOT
    / "controls"
    / "feedback"
    / "Progress"
    / "_internal"
    / "ProgressRingImpl.qml",
)
NON_PROGRESS_ARC_SOURCES = {
    "_internal/ContentFrame.qml",
    "controls/data/Avatar/Avatar.qml",
    "controls/data/Chart/_internal/BoxplotChartContent.qml",
    "controls/data/Chart/_internal/PieChartContent.qml",
    "controls/data/Chart/_internal/RadarChartContent.qml",
    "controls/data/Chart/_internal/ScatterChartContent.qml",
    "controls/data/CircularGauge.qml",
    "controls/inputs/_internal/ImageCropperContent.qml",
}
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "progress-ring-reuse.qml"))
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property int pulseStyle: Enums.progress.indeterminate_style_pulse
    readonly property int fixedArcStyle: Enums.progress.indeterminate_style_fixed_arc
    readonly property int orbitDotStyle: Enums.progress.indeterminate_style_orbit_dot

    width: 800
    height: 600

    Button {
        objectName: "progressButton"
        width: 180
        height: 40
        text: "Working"
        feature: Enums.button.feature_progress_ring
        progress: 0.4
    }

    Progress {
        objectName: "unifiedProgress"
        x: 200
        type: Enums.progress.type_ring
        value: 35
    }

    ProgressRing {
        objectName: "blockingProgressRing"
        x: 420
        width: 48
        height: 48
        indeterminate: true
    }

    ResultState {
        objectName: "resultState"
        y: 80
        state: "loading"
    }

    StateWidget {
        objectName: "stateWidget"
        x: 320
        y: 80
        stateType: Enums.state.type_result
        severity: "loading"
    }

    SplashScreen {
        objectName: "splashScreen"
        showTitleBar: false
        enableShadow: false
    }
}
"""
RENDER_THREAD_PROBE_SOURCE = textwrap.dedent(
    '''
    import os
    import sys
    import time
    from pathlib import Path

    from scripts.test_process import prepare_automated_test_process

    prepare_automated_test_process()

    from PySide6.QtCore import QEventLoop, Qt, QTimer, QUrl
    from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
    from PySide6.QtWidgets import QApplication
    from prismqml import register_types


    def pump(milliseconds):
        loop = QEventLoop()
        QTimer.singleShot(milliseconds, loop.quit)
        loop.exec()


    root_dir = Path.cwd()
    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(root_dir / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    style_name = sys.argv[1]
    scene_source = b"""
        import QtQuick
        import PrismQML

        Window {
            width: 320
            height: 240
            visible: true

            ProgressRing {
                anchors.centerIn: parent
                width: 48
                height: 48
                indeterminate: true
                indeterminateStyle: Enums.progress.__STYLE__
            }
        }
        """.replace(b"__STYLE__", style_name.encode("ascii"))
    component.setData(
        scene_source,
        QUrl("inline:render-thread-progress-ring-probe.qml"),
    )
    for _ in range(100):
        if component.status() != QQmlComponent.Status.Loading:
            break
        pump(10)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert window is not None, [error.toString() for error in component.errors()]

    frame_times = []
    window.frameSwapped.connect(
        lambda: frame_times.append(time.perf_counter()),
        Qt.ConnectionType.DirectConnection,
    )
    pump(250)
    frame_times.clear()

    block_started = time.perf_counter()
    time.sleep(0.5)
    block_finished = time.perf_counter()
    blocked_frames = [
        timestamp
        for timestamp in frame_times
        if block_started <= timestamp <= block_finished
    ]
    frame_gaps = [
        later - earlier
        for earlier, later in zip(blocked_frames, blocked_frames[1:])
    ]
    assert len(blocked_frames) >= 5, blocked_frames
    assert max(frame_gaps) < 0.12, frame_gaps
    sys.stdout.write(f"BLOCKED_FRAMES={len(blocked_frames)}\\n")
    sys.stdout.flush()
    os._exit(0)
    '''
)


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    _pump()
    assert warnings == []
    return engine, component, root


def _standard_progress_rings(item: QObject) -> list[QObject]:
    return [
        child
        for child in item.findChildren(QObject)
        if child.metaObject().className().startswith("ProgressRing_")
    ]


def test_ring_consumers_delegate_to_canonical_progress_ring():
    forbidden = (
        "Canvas {",
        "RotationAnimation on rotation",
        "RotationAnimator on rotation",
        "BusyIndicator {",
    )
    for source_path in RING_CONSUMERS:
        source = source_path.read_text(encoding="utf-8")
        assert "ProgressRing {" in source, source_path
        for marker in forbidden:
            assert marker not in source, (source_path, marker)


def test_qml_page_and_splash_share_the_orbit_dot_visual_mode():
    """公开加载页与 SplashScreen 必须保持同款绕圈圆点动画。"""
    helper_source = LAZY_LOADING_HELPER.read_text(encoding="utf-8")
    assert "QMLPage {" in helper_source

    for source_path in (QML_PAGE, SPLASH_SCREEN):
        source = source_path.read_text(encoding="utf-8")
        assert (
            "indeterminateStyle: Enums.progress.indeterminate_style_orbit_dot"
            in source
        )
        assert "spinDuration: Enums.duration.splashProgressSpin" in source
        assert "indeterminateDotSize: control._progressDotSize" in source
        assert "indeterminateDotRadius: control._progressDotRadius" in source
        assert "indeterminateDotTopMargin: control._progressDotTopMargin" in source

    overlay_source = LOADING_OVERLAY.read_text(encoding="utf-8")
    assert "indeterminateStyle: Enums.progress.indeterminate_style_fixed_arc" in overlay_source
    assert "spinDuration: Enums.duration.scroll" in overlay_source


def test_all_non_progress_arc_painters_remain_explicitly_classified():
    arc_sources = {
        path.relative_to(QML_ROOT).as_posix()
        for path in QML_ROOT.rglob("*.qml")
        if "ctx.arc(" in path.read_text(encoding="utf-8") and path != CANONICAL_RING
    }
    assert arc_sources == NON_PROGRESS_ARC_SOURCES


def test_no_qt_busy_indicator_or_extra_rotating_ring_remains():
    sources = {
        path.relative_to(QML_ROOT).as_posix(): path.read_text(encoding="utf-8")
        for path in QML_ROOT.rglob("*.qml")
    }
    assert not {
        path
        for path, source in sources.items()
        if re.search(r"\bBusyIndicator\s*\{", source)
    }
    rotating_sources = {
        path
        for path, source in sources.items()
        if re.search(r"Rotation(?:Animation|Animator)\s+on\s+rotation", source)
    }
    assert rotating_sources == {
        "controls/feedback/Confetti.qml",
        "controls/feedback/Progress/_internal/IndeterminateArcImpl.qml",
    }


def test_progress_ring_repaint_handlers_do_not_allocate_connections(qapp):
    """Direct handlers preserve repainting without QQmlConnections. 直接处理器避免额外对象。"""
    source = CANONICAL_RING.read_text(encoding="utf-8")
    assert "onTrackColorChanged: _requestCanvasPaint()" in source
    assert "onProgressColorChanged: _requestCanvasPaint()" in source
    assert "Connections {" not in source

    engine, component, root = _create_scene()
    try:
        ring = root.findChild(QQuickItem, "blockingProgressRing")
        assert ring is not None
        assert not {
            child.metaObject().className()
            for child in ring.findChildren(QObject)
            if child.metaObject().className() == "QQmlConnections"
        }
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_progress_ring_creates_only_the_active_visual_branch(qapp):
    engine, component, root = _create_scene()
    try:
        ring = root.findChild(QQuickItem, "blockingProgressRing")
        assert ring is not None

        def child(name):
            return ring.findChild(QObject, name)

        # Pulse is the default indeterminate style: only the Shape branch exists.
        assert child("progressRingCanvas") is None
        assert child("progressRingSpinningArc") is not None
        assert child("progressRingOrbitingDot") is None

        ring.setProperty("indeterminateStyle", root.property("fixedArcStyle"))
        _pump(1)
        assert child("progressRingSpinningArc") is not None
        assert child("progressRingOrbitingDot") is None

        ring.setProperty("indeterminateStyle", root.property("orbitDotStyle"))
        _pump(1)
        assert child("progressRingSpinningArc") is None
        assert child("progressRingOrbitingDot") is not None

        ring.setProperty("indeterminate", False)
        _pump(1)
        assert child("progressRingCanvas") is not None
        assert child("progressRingIndeterminateArc") is None

        ring.setProperty("indeterminate", True)
        ring.setProperty("indeterminateStyle", root.property("pulseStyle"))
        _pump(1)
        assert child("progressRingCanvas") is None
        assert child("progressRingSpinningArc") is not None
        assert child("progressRingOrbitingDot") is None
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_indeterminate_ring_keeps_rendering_while_gui_thread_is_blocked():
    """同步页面创建占住 GUI 线程时，三种视觉模式都须持续交换帧。"""
    env = os.environ.copy()
    env.update(
        {
            "QSG_RENDER_LOOP": "threaded",
            "QSG_RHI_BACKEND": "software",
        }
    )
    styles = (
        "indeterminate_style_pulse",
        "indeterminate_style_fixed_arc",
        "indeterminate_style_orbit_dot",
    )
    for style_name in styles:
        result = subprocess.run(
            [sys.executable, "-c", RENDER_THREAD_PROBE_SOURCE, style_name],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            check=False,
        )
        output = result.stdout + result.stderr
        assert result.returncode == 0, (style_name, output)
        match = re.search(r"^BLOCKED_FRAMES=(\d+)$", output, re.MULTILINE)
        assert match is not None, (style_name, output)
        assert int(match.group(1)) >= 5, (style_name, output)


def test_public_consumers_create_the_standard_ring_at_runtime(qapp):
    engine, component, root = _create_scene()
    try:
        for object_name in (
            "progressButton",
            "unifiedProgress",
            "resultState",
            "stateWidget",
            "splashScreen",
        ):
            consumer = root.findChild(QQuickItem, object_name)
            assert consumer is not None, object_name
            rings = _standard_progress_rings(consumer)
            assert len(rings) == 1, (
                object_name,
                [ring.metaObject().className() for ring in rings],
            )
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)
