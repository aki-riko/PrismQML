# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Progress ring reuse regressions. 进度环复用回归。"""

from pathlib import Path
import re

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types

ROOT = Path(__file__).resolve().parents[2]
QML_ROOT = ROOT / "prismqml" / "PrismQML"
CANONICAL_RING = QML_ROOT / "controls" / "feedback" / "Progress" / "ProgressRing.qml"
RING_CONSUMERS = (
    QML_ROOT / "_internal" / "LoadingOverlay.qml",
    QML_ROOT / "controls" / "navigation" / "_internal" / "LazyLoadingHelper.qml",
    QML_ROOT / "controls" / "buttons" / "Button" / "ButtonContent.qml",
    QML_ROOT / "controls" / "feedback" / "SplashScreen" / "SplashScreen.qml",
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
    assert rotating_sources == {"controls/feedback/Confetti.qml"}


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
