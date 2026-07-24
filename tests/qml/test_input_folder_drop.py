# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""InputCore opt-in folder drop contracts. 输入基类可选文件夹拖放合同。"""

from pathlib import Path

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QDir,
    QEvent,
    QEventLoop,
    QFileInfo,
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

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "input-folder-drop.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 420
    height: 280
    visible: true

    LineEdit {
        objectName: "defaultControl"
        x: 40
        y: 20
        text: "default"
    }

    LineEdit {
        objectName: "enabledControl"
        x: 40
        y: 80
        text: "initial"
        folderDropEnabled: true
    }

    LineEdit {
        objectName: "readOnlyControl"
        x: 40
        y: 140
        text: "locked"
        readOnly: true
        folderDropEnabled: true
    }

    LineEdit {
        objectName: "disabledControl"
        x: 40
        y: 200
        text: "disabled"
        enabled: false
        folderDropEnabled: true
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


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
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    controls = {
        name: window.findChild(QQuickItem, name)
        for name in (
            "defaultControl",
            "enabledControl",
            "readOnlyControl",
            "disabledControl",
        )
    }
    assert all(controls.values())
    _pump()
    return engine, component, window, controls, warnings


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
def folder_drop_scene(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_scene()
    try:
        yield window, controls, warnings, windows_before
    finally:
        _dispose_scene(engine, component, window)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def _drop_urls(window: QQuickWindow, control: QQuickItem, urls: list[QUrl]):
    mime = QMimeData()
    mime.setUrls(urls)
    center = control.mapToItem(
        window.contentItem(), QPointF(control.width() / 2, control.height() / 2)
    )
    position = QPoint(round(center.x()), round(center.y()))
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
    return enter.isAccepted(), drop.isAccepted()


def test_folder_drop_is_disabled_by_default_and_respects_control_state(
    folder_drop_scene, tmp_path: Path
) -> None:
    window, controls, warnings, windows_before = folder_drop_scene
    folder = tmp_path / "state-folder"
    folder.mkdir()
    folder_url = QUrl.fromLocalFile(str(folder))

    assert not controls["defaultControl"].property("folderDropEnabled")
    for name, expected in (
        ("defaultControl", "default"),
        ("readOnlyControl", "locked"),
        ("disabledControl", "disabled"),
    ):
        accepted = _drop_urls(window, controls[name], [folder_url])
        assert accepted == (False, False)
        assert controls[name].property("text") == expected

    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_folder_drop_accepts_one_real_local_directory(
    folder_drop_scene, tmp_path: Path
) -> None:
    window, controls, warnings, windows_before = folder_drop_scene
    control = controls["enabledControl"]
    folder = tmp_path / "拖 放#百分%"
    folder.mkdir()
    emitted = []
    control.folderDropped.connect(emitted.append)

    accepted = _drop_urls(window, control, [QUrl.fromLocalFile(str(folder))])

    expected = QDir.cleanPath(QFileInfo(str(folder)).absoluteFilePath())
    assert accepted == (True, True)
    assert control.property("text") == expected
    assert emitted == [expected]
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_folder_drop_rejects_files_missing_remote_network_and_multiple_urls(
    folder_drop_scene, tmp_path: Path
) -> None:
    window, controls, warnings, windows_before = folder_drop_scene
    control = controls["enabledControl"]
    regular_file = tmp_path / "not-a-folder.txt"
    regular_file.write_text("fixture", encoding="utf-8")
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()

    candidates = [
        [QUrl.fromLocalFile(str(regular_file))],
        [QUrl.fromLocalFile(str(tmp_path / "missing"))],
        [QUrl("https://example.com/folder")],
        [QUrl("file://server/share")],
        [QUrl.fromLocalFile(str(first)), QUrl.fromLocalFile(str(second))],
    ]
    for urls in candidates:
        control.setProperty("text", "initial")
        accepted = _drop_urls(window, control, urls)
        assert accepted == (False, False)
        assert control.property("text") == "initial"

    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []
