# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Breadcrumb timer lifecycle regressions. 面包屑计时器生命周期回归。"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QObject,
    QTimer,
    QUrl,
)
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(
    os.environ.get("PRISMQML_TEST_ROOT", Path(__file__).resolve().parents[2])
).resolve()
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "navigation"
    / "Breadcrumb.qml"
)
TIMER_SOURCE_PATH = SOURCE_PATH.parent / "_internal" / "BreadcrumbStageTimer.qml"
WINDOWS_PIXEL_HASHES = (
    "20257205ddc48958c27222783f84ca71b1ca963a49b4fd5e8a20d760b8e0e8f7",
    "7248519f0fd6ac793cebdab3f130234fb98b118927e324043852aa76abca2951",
    "3cfb5e5e32b4cf8e6372de66b0b10ef7bcea61d71b05907e5fec49557b1dccc1",
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "breadcrumb-timer-lifecycle.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root

    readonly property int breadcrumbCount: breadcrumb.count
    readonly property int breadcrumbCurrentIndex: breadcrumb.currentIndex
    readonly property int collapsedCount: breadcrumb._newlyCollapsedIndices.length
    readonly property int shownCount: breadcrumb._newlyShownIndices.length
    readonly property bool shiftLeftActive: breadcrumb._shiftLeftActive
    readonly property bool shiftRightActive: breadcrumb._shiftRightActive

    function addOverflowItem() {
        breadcrumb.addItem("overflow", "Overflow", "")
    }

    function trimToThirdItem() {
        breadcrumb.setCurrentIndex(2)
    }

    width: 760
    height: 140
    visible: true
    color: Enums.backgroundColor

    Breadcrumb {
        id: breadcrumb
        objectName: "breadcrumb"
        x: 30
        y: 40
        width: 700
        maxVisibleItems: 5
        showIcons: false
        animated: true

        Component.onCompleted: {
            addItem("root", "Root", "")
            addItem("workspace", "Workspace", "")
            addItem("project", "Project", "")
            addItem("source", "Source", "")
            addItem("leaf", "Leaf", "")
        }
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2_000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _root_timers(breadcrumb: QQuickItem) -> list[QObject]:
    timers = {}
    for child in breadcrumb.findChildren(QObject):
        if (
            child.metaObject().className() == "QQmlTimer"
            and child.parent() is breadcrumb
        ):
            timers[shiboken6.getCppPointer(child)[0]] = child
    for property_name in (
        "_removeTimer",
        "_collapseTimer",
        "_showTimer",
    ):
        if breadcrumb.metaObject().indexOfProperty(property_name) < 0:
            continue
        timer = breadcrumb.property(property_name)
        if timer is not None:
            timers[shiboken6.getCppPointer(timer)[0]] = timer
    return list(timers.values())


def _image_hash(image: QImage) -> str:
    normalized = image.convertToFormat(QImage.Format.Format_RGBA8888)
    return hashlib.sha256(bytes(normalized.bits())).hexdigest()


def _stable_hash(window: QQuickWindow) -> str:
    previous = ""
    stable_count = 0
    for _ in range(30):
        _pump(80)
        image = window.grabWindow()
        assert not image.isNull()
        current = _image_hash(image)
        stable_count = stable_count + 1 if current == previous else 1
        if stable_count >= 3:
            return current
        previous = current
    raise AssertionError("Breadcrumb pixels did not stabilize")


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
    ]


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    engine.addImportPath(str(ROOT / "prismqml"))
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert _wait_for(lambda: component.status() != QQmlComponent.Status.Loading)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    breadcrumb = window.findChild(QQuickItem, "breadcrumb")
    assert breadcrumb is not None
    assert _wait_for(window.isExposed)
    return engine, component, window, breadcrumb, warnings


def _dispose_scene(qapp, engine, component, window) -> None:
    window.close()
    for obj in (window, component, engine):
        if obj is not None and shiboken6.isValid(obj):
            obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def test_breadcrumb_timer_animation_and_pixel_lifecycle(qapp):
    """Collapse and restore timers must preserve independent animation stages.

    折叠与恢复计时器必须保持独立动画阶段。
    """
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, breadcrumb, warnings = _create_scene()
    try:
        assert _wait_for(lambda: window.property("breadcrumbCount") == 5)
        _pump(1_000)
        initial_timers = _root_timers(breadcrumb)
        initial_objects = len(breadcrumb.findChildren(QObject))
        initial_hash = _stable_hash(window)

        assert QMetaObject.invokeMethod(window, "addOverflowItem")
        collapse_timers = _root_timers(breadcrumb)
        collapse_timer = breadcrumb.property("_collapseTimer")
        assert collapse_timer is not None
        assert collapse_timer.objectName() == "breadcrumbStageTimer"
        assert collapse_timer.parent() is breadcrumb
        assert collapse_timer.property("timerInterval") == collapse_timer.property(
            "interval"
        )
        assert collapse_timer.property("repeat") is False
        assert window.property("collapsedCount") == 2
        assert window.property("shiftLeftActive")
        assert _wait_for(lambda: not window.property("shiftLeftActive"))
        collapsed_timers = _root_timers(breadcrumb)
        collapsed_objects = len(breadcrumb.findChildren(QObject))
        collapsed_hash = _stable_hash(window)

        assert QMetaObject.invokeMethod(window, "trimToThirdItem")
        restore_timers = _root_timers(breadcrumb)
        remove_timer = breadcrumb.property("_removeTimer")
        show_timer = breadcrumb.property("_showTimer")
        assert remove_timer is not None
        assert show_timer is not None
        assert remove_timer is not show_timer
        for stage_timer in (remove_timer, show_timer):
            assert stage_timer.objectName() == "breadcrumbStageTimer"
            assert stage_timer.parent() is breadcrumb
        assert window.property("shownCount") == 2
        assert window.property("shiftRightActive")
        assert _wait_for(lambda: window.property("breadcrumbCount") == 3)
        assert _wait_for(lambda: not window.property("shiftRightActive"))
        settled_timers = _root_timers(breadcrumb)
        settled_objects = len(breadcrumb.findChildren(QObject))
        settled_hash = _stable_hash(window)

        print(
            "BREADCRUMB_TIMER",
            f"timers={len(initial_timers)}/{len(collapse_timers)}/"
            f"{len(collapsed_timers)}/{len(restore_timers)}/"
            f"{len(settled_timers)}",
            f"objects={initial_objects}/{collapsed_objects}/{settled_objects}",
            f"hashes={initial_hash}/{collapsed_hash}/{settled_hash}",
        )

        assert len(initial_timers) == 0
        assert len(collapse_timers) == 1
        assert len(collapsed_timers) == 0
        assert len(restore_timers) == 2
        assert len(settled_timers) == 0
        assert (initial_objects, collapsed_objects, settled_objects) == (
            10,
            10,
            10,
        )
        pixel_hashes = (initial_hash, collapsed_hash, settled_hash)
        if os.name == "nt":
            assert pixel_hashes == WINDOWS_PIXEL_HASHES
        else:
            assert len(set(pixel_hashes)) == 3
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(qapp, engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_breadcrumb_source_creates_stage_timers_on_demand():
    """Each animation stage creates an independent timer only while needed.

    每个动画阶段仅在需要时创建独立计时器。
    """
    source = SOURCE_PATH.read_text(encoding="utf-8")
    timer_source = TIMER_SOURCE_PATH.read_text(encoding="utf-8")
    assert "id: removeTimer" not in source
    assert "id: collapseToEllipsisTimer" not in source
    assert "id: showFromEllipsisTimer" not in source
    assert "id: stageTimerComponent" in source
    assert "stageTimerComponent.createObject(" in source
    assert "_restartRemoveTimer()" in source
    assert "_restartCollapseTimer()" in source
    assert "_restartShowTimer()" in source
    assert "BreadcrumbStageTimer {}" in source
    assert "releaseCallback(stageTimer)" in timer_source
    assert "destroy()" in timer_source
