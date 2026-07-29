# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""DropZone geometry, state and drop routing contracts. DropZone 几何、状态与拖放合同。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMimeData,
    QPoint,
    QPointF,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "containers"
    / "DropZone.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "drop-zone-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"

    readonly property string effectiveDropText: zone.dropText
    readonly property bool zoneHovered: zone.hovered
    readonly property bool zoneDragActive: zone.dragActive
    readonly property real zoneImplicitWidth: zone.implicitWidth
    readonly property real zoneImplicitHeight: zone.implicitHeight

    width: 420
    height: 260
    visible: true

    DropZone {
        id: zone
        objectName: "zone"
        x: 20
        y: 20
        width: 260
        height: 140
        allowedExtensions: ["png", "jpg"]
        initialDir: "C:/drop-zone-test"
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 800) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 30
    return predicate()


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is accepted for accepted in allowed)
    ]


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
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow)
    zone = window.findChild(QQuickItem, "zone")
    _pump()
    return engine, component, window, zone, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


@pytest.fixture
def drop_zone_scene(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, zone, warnings = _create_scene()
    try:
        yield window, zone, warnings, windows_before
    finally:
        _dispose_scene(engine, component, window)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def _drop_files(window, paths):
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(path) for path in paths])
    position = QPoint(80, 80)
    enter = QDragEnterEvent(
        position,
        Qt.DropAction.CopyAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    QCoreApplication.sendEvent(window, enter)
    drop = QDropEvent(
        QPointF(position),
        Qt.DropAction.CopyAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    QCoreApplication.sendEvent(window, drop)
    _pump()


def test_drop_zone_size_text_and_hover(drop_zone_scene):
    window, zone, warnings, windows_before = drop_zone_scene
    assert window.property("zoneImplicitWidth") == pytest.approx(350)
    assert window.property("zoneImplicitHeight") == pytest.approx(140)
    assert "PNG, JPG" in window.property("effectiveDropText")
    assert not window.property("zoneHovered")
    QTest.mouseMove(window, QPoint(80, 80))
    assert _wait_for(lambda: window.property("zoneHovered"))
    QTest.mouseMove(window, QPoint(380, 220))
    assert _wait_for(lambda: not window.property("zoneHovered"))
    assert not window.property("zoneDragActive")
    buttons = [
        item
        for item in zone.findChildren(QQuickItem)
        if item.metaObject().className().startswith("ButtonCore")
    ]
    assert len(buttons) == 2
    assert sum(item.isVisible() for item in buttons) == 2
    zone.setProperty("folderMode", True)
    _pump()
    assert sum(item.isVisible() for item in buttons) == 1
    assert "PNG, JPG" not in window.property("effectiveDropText")
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_drop_zone_real_drop_routes_single_multiple_and_folder(drop_zone_scene):
    window, zone, warnings, windows_before = drop_zone_scene
    single = []
    multiple = []
    folders = []
    zone.fileSelected.connect(single.append)
    zone.filesSelected.connect(lambda files: multiple.append(_variant(files)))
    zone.folderSelected.connect(folders.append)
    first = str(ROOT / "tests" / "fixtures" / "first.png")
    second = str(ROOT / "tests" / "fixtures" / "second.jpg")

    _drop_files(window, [first, second])
    assert single == [first.replace("\\", "/")]
    zone.setProperty("multiple", True)
    _drop_files(window, [first, second])
    assert multiple == [[first.replace("\\", "/"), second.replace("\\", "/")]]
    zone.setProperty("multiple", False)
    zone.setProperty("folderMode", True)
    folder = str(ROOT / "tests" / "fixtures")
    _drop_files(window, [folder])
    assert folders == [folder.replace("\\", "/")]
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_drop_zone_source_follows_conventions():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert "hovered ? Enums.stateColor.borderStrong : Enums.stateColor.border)" in source
    assert "Enums.stateColor.borderSubtle" not in source
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
