# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""ProgressBar branch lifecycle regressions. ProgressBar 分支生命周期回归。"""

from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "progress-bar-lifecycle.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root

    property bool initialIndeterminate: false

    width: 360
    height: 100
    visible: true

    ProgressBar {
        objectName: "progressBar"
        anchors.centerIn: parent
        width: 300
        height: Enums.spacing.xs
        value: 42
        indeterminate: root.initialIndeterminate
    }
}
"""


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
    ]


def _indeterminate_implementations(progress_bar: QQuickItem) -> list[QObject]:
    return [
        obj
        for obj in progress_bar.findChildren(QObject)
        if obj.metaObject().className().startswith("IndeterminateBarImpl")
    ]


def _dispose_scene(engine, component, window) -> None:
    window.setVisible(False)
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def test_progress_bar_creates_indeterminate_branch_only_while_needed(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
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
    progress_bar = window.findChild(QQuickItem, "progressBar")
    assert progress_bar is not None
    QCoreApplication.processEvents()

    try:
        assert _indeterminate_implementations(progress_bar) == []

        window.setProperty("initialIndeterminate", True)
        QCoreApplication.processEvents()
        implementations = _indeterminate_implementations(progress_bar)
        assert len(implementations) == 1
        animations = [
            obj
            for obj in implementations[0].findChildren(QObject)
            if obj.metaObject().className() == "QQuickSequentialAnimation"
        ]
        assert len(animations) == 1
        assert animations[0].property("running") is True

        window.setProperty("initialIndeterminate", False)
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()
        assert _indeterminate_implementations(progress_bar) == []
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []
