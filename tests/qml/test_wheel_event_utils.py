# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""WheelEventUtils contracts. WheelEventUtils 归一化合同。"""

from pathlib import Path
import re

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QPoint,
    QPointF,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtGui import QGuiApplication, QWheelEvent
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickWindow

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
QML_ROOT = ROOT / "prismqml" / "PrismQML"
WHEEL_EVENT_UTILS_PATH = QML_ROOT / "WheelEventUtils.qml"
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "wheel-event-utils.qml"))
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    width: 120
    height: 120
    visible: true

    property real verticalValue: 0
    property real horizontalValue: 0
    property bool invertedValue: false

    MouseArea {
        anchors.fill: parent

        onWheel: (wheel) => {
            root.verticalValue = WheelEventUtils.verticalDelta(wheel)
            root.horizontalValue = WheelEventUtils.horizontalDelta(wheel)
            root.invertedValue = wheel.inverted
            wheel.accepted = true
        }
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _send_wheel(window: QQuickWindow, angle_delta: QPoint, inverted: bool):
    position = QPointF(window.width() / 2, window.height() / 2)
    event = QWheelEvent(
        position,
        QPointF(window.x() + position.x(), window.y() + position.y()),
        QPoint(0, 0),
        angle_delta,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        inverted,
    )
    assert QGuiApplication.sendEvent(window, event)
    return event


@pytest.fixture
def wheel_scene(qapp):
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    _pump()
    try:
        yield window, warnings
    finally:
        window.close()
        window.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()


def test_inverted_wheel_delta_is_normalized(wheel_scene):
    window, warnings = wheel_scene

    normal = _send_wheel(window, QPoint(120, -120), False)
    assert normal.isAccepted()
    assert window.property("verticalValue") == pytest.approx(-120)
    assert window.property("horizontalValue") == pytest.approx(120)
    assert window.property("invertedValue") is False

    inverted = _send_wheel(window, QPoint(-120, 120), True)
    assert inverted.isAccepted()
    assert window.property("verticalValue") == pytest.approx(-120)
    assert window.property("horizontalValue") == pytest.approx(120)
    assert window.property("invertedValue") is True
    assert warnings == []


def test_wheel_delta_reads_are_centralized():
    line_comment = re.compile(r"//[^\n]*")
    block_comment = re.compile(r"/\*.*?\*/", re.DOTALL)
    unnormalized_sources = []
    for source_path in QML_ROOT.rglob("*.qml"):
        if source_path == WHEEL_EVENT_UTILS_PATH:
            continue
        source = source_path.read_text(encoding="utf-8")
        code = line_comment.sub("", block_comment.sub("", source))
        if "angleDelta" in code:
            unnormalized_sources.append(source_path.relative_to(ROOT).as_posix())
    assert unnormalized_sources == []
