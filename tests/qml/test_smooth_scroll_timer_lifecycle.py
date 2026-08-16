# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SmoothScrollHelper timer lifecycle regressions. 平滑滚动计时器生命周期回归。"""

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
    Qt,
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
    / "containers"
    / "ScrollBar"
    / "SmoothScrollHelper.qml"
)
BOUNCE_TIMER_PATH = SOURCE_PATH.parent / "_internal" / "SmoothScrollBounceTimer.qml"
RECONCILE_TIMER_PATH = (
    SOURCE_PATH.parent / "_internal" / "SmoothScrollBoundsReconcileTimer.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "smooth-scroll-timer-lifecycle.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/controls/containers/ScrollBar" as Internal

Window {
    id: root

    readonly property real verticalPosition: verticalFlick.contentY
    readonly property real horizontalPosition: horizontalFlick.contentX
    readonly property real verticalMaximum:
        verticalFlick.originY + verticalFlick.contentHeight - verticalFlick.height
    readonly property real horizontalMaximum:
        horizontalFlick.originX + horizontalFlick.contentWidth - horizontalFlick.width

    function overshootBoth() {
        verticalHelper.scrollBy(1000)
        horizontalHelper.scrollBy(1000)
    }

    width: 520
    height: 220
    visible: true
    color: Enums.backgroundColor

    Flickable {
        id: verticalFlick
        x: 20
        y: 20
        width: 180
        height: 160
        contentWidth: width
        contentHeight: 640
        interactive: false
        clip: true

        Rectangle {
            width: verticalFlick.width
            height: verticalFlick.contentHeight
            color: Enums.accentColor
        }
    }

    Internal.SmoothScrollHelper {
        id: verticalHelper
        objectName: "verticalHelper"
        target: verticalFlick
        orientation: Qt.Vertical
    }

    Flickable {
        id: horizontalFlick
        x: 240
        y: 20
        width: 240
        height: 160
        contentWidth: 760
        contentHeight: height
        interactive: false
        clip: true

        Rectangle {
            width: horizontalFlick.contentWidth
            height: horizontalFlick.height
            color: Enums.accentColor
        }
    }

    Internal.SmoothScrollHelper {
        id: horizontalHelper
        objectName: "horizontalHelper"
        target: horizontalFlick
        orientation: Qt.Horizontal
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


def _timers(helper: QQuickItem) -> list[QObject]:
    timers = {
        shiboken6.getCppPointer(child)[0]: child
        for child in helper.findChildren(QObject)
        if child.metaObject().className() == "QQmlTimer"
        or child.objectName()
        in {
            "smoothScrollVerticalReconcileTimer",
            "smoothScrollHorizontalReconcileTimer",
        }
    }
    for property_name in ("_bounceTimerV", "_bounceTimerH"):
        timer = helper.property(property_name)
        if timer is not None:
            timers[shiboken6.getCppPointer(timer)[0]] = timer
    return list(timers.values())


def _image_hash(image: QImage) -> str:
    normalized = image.convertToFormat(QImage.Format.Format_RGBA8888)
    return hashlib.sha256(bytes(normalized.bits())).hexdigest()


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
    vertical = window.findChild(QQuickItem, "verticalHelper")
    horizontal = window.findChild(QQuickItem, "horizontalHelper")
    assert vertical is not None
    assert horizontal is not None
    assert _wait_for(window.isExposed)
    return engine, component, window, vertical, horizontal, warnings


def _dispose_scene(qapp, engine, component, window) -> None:
    window.close()
    for obj in (window, component, engine):
        if obj is not None and shiboken6.isValid(obj):
            obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def test_smooth_scroll_bounce_timer_and_pixels(qapp):
    """Both axes must bounce concurrently and settle without visual drift.

    横纵轴必须并发回弹，并在结束后保持像素稳定。
    """
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, vertical, horizontal, warnings = _create_scene()
    try:
        _pump(800)
        initial_vertical_timers = _timers(vertical)
        initial_horizontal_timers = _timers(horizontal)
        initial_objects = (
            len(vertical.findChildren(QObject)),
            len(horizontal.findChildren(QObject)),
        )

        assert QMetaObject.invokeMethod(window, "overshootBoth")
        active_vertical_timers = _timers(vertical)
        active_horizontal_timers = _timers(horizontal)
        vertical_maximum = window.property("verticalMaximum")
        horizontal_maximum = window.property("horizontalMaximum")
        peak_vertical = window.property("verticalPosition")
        peak_horizontal = window.property("horizontalPosition")
        for _ in range(100):
            _pump(10)
            peak_vertical = max(
                peak_vertical, window.property("verticalPosition")
            )
            peak_horizontal = max(
                peak_horizontal, window.property("horizontalPosition")
            )

        assert _wait_for(
            lambda: window.property("verticalPosition") == vertical_maximum
        )
        assert _wait_for(
            lambda: window.property("horizontalPosition") == horizontal_maximum
        )
        _pump(100)
        settled_hash = _image_hash(window.grabWindow())
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        qapp.processEvents()
        settled_vertical_timers = _timers(vertical)
        settled_horizontal_timers = _timers(horizontal)
        settled_objects = (
            len(vertical.findChildren(QObject)),
            len(horizontal.findChildren(QObject)),
        )
        repeated_hash = _image_hash(window.grabWindow())

        print(
            "SMOOTH_SCROLL_TIMER",
            f"vertical={len(initial_vertical_timers)}/"
            f"{len(active_vertical_timers)}/{len(settled_vertical_timers)}",
            f"horizontal={len(initial_horizontal_timers)}/"
            f"{len(active_horizontal_timers)}/{len(settled_horizontal_timers)}",
            f"objects={initial_objects}/{settled_objects}",
            f"peaks={peak_vertical:.2f}/{peak_horizontal:.2f}",
            f"hash={settled_hash}",
        )

        assert len(initial_vertical_timers) == 2
        assert len(initial_horizontal_timers) == 2
        assert len(active_vertical_timers) == 3
        assert len(active_horizontal_timers) == 3
        assert len(settled_vertical_timers) == 2
        assert len(settled_horizontal_timers) == 2
        assert initial_objects == (7, 7)
        assert settled_objects == (7, 7)
        assert peak_vertical > vertical_maximum
        assert peak_horizontal > horizontal_maximum
        assert repeated_hash == settled_hash
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(qapp, engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_smooth_scroll_source_creates_axis_bounce_timers_on_demand():
    """Each axis creates an independent bounce timer only while needed.

    每个轴仅在需要时创建独立回弹计时器。
    """
    source = SOURCE_PATH.read_text(encoding="utf-8")
    bounce_timer_source = BOUNCE_TIMER_PATH.read_text(encoding="utf-8")
    assert "id: bounceTimerV" not in source
    assert "id: bounceTimerH" not in source
    assert "id: bounceTimerComponent" in source
    assert "bounceTimerComponent.createObject(" in source
    assert "ScrollBarInternal.SmoothScrollBounceTimer {" in source
    assert "required property var scrollHelper" in bounce_timer_source
    assert "required property bool verticalAxis" in bounce_timer_source
    assert "scrollHelper._releaseBounceTimer(verticalAxis, bounceTimer)" in bounce_timer_source
    assert "_restartBounceTimer(true)" in source
    assert "_restartBounceTimer(false)" in source
    assert "_stopBounceTimer(true)" in source
    assert "_stopBounceTimer(false)" in source
    assert "_releaseBounceTimer(verticalAxis, bounceTimer)" not in source


def test_smooth_scroll_reconcile_timer_contract(qapp):
    """Each axis keeps its deferred bounds reconciliation timer modularized.

    每个滚动轴都保留独立且可重启的延迟边界校准计时器。
    """
    source = SOURCE_PATH.read_text(encoding="utf-8")
    reconcile_source = RECONCILE_TIMER_PATH.read_text(encoding="utf-8")
    assert "ScrollBarInternal.SmoothScrollBoundsReconcileTimer {" in source
    assert "id: verticalReconcileTimer" in source
    assert "id: horizontalReconcileTimer" in source
    assert "verticalAxis: true" in source
    assert "verticalAxis: false" in source
    assert "required property var scrollHelper" in reconcile_source
    assert "required property bool verticalAxis" in reconcile_source
    assert "scrollHelper._reconcileVerticalBounds()" in reconcile_source
    assert "scrollHelper._reconcileHorizontalBounds()" in reconcile_source

    engine, component, window, vertical, horizontal, warnings = _create_scene()
    try:
        for helper, timer_name, is_vertical in (
            (vertical, "smoothScrollVerticalReconcileTimer", True),
            (horizontal, "smoothScrollHorizontalReconcileTimer", False),
        ):
            timer = helper.findChild(QObject, timer_name)
            assert timer is not None
            assert timer.parent() is helper
            assert timer.property("scrollHelper") is helper
            assert timer.property("verticalAxis") is is_vertical
            assert timer.property("interval") == 50
            assert timer.property("repeat") is False
            assert QMetaObject.invokeMethod(timer, "restart")
            assert timer.property("running") is True
            _pump(70)
            assert timer.property("running") is False
        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)
