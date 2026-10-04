# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Smooth-scroll frame-driver regressions. 平滑滚动逐帧驱动回归。"""

from __future__ import annotations

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
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(
    os.environ.get("PRISMQML_TEST_ROOT", Path(__file__).resolve().parents[2])
).resolve()
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "smooth-scroll-frame-driver.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick as QtQ
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/controls/containers/ScrollBar" as Internal

Window {
    id: root

    readonly property real position: flickable.contentY

    function startScroll() {
        helper.scrollTo(180)
    }

    width: 240
    height: 180
    visible: true

    Flickable {
        id: flickable
        width: parent.width
        height: parent.height
        contentWidth: width
        contentHeight: 640
        interactive: false
    }

    Internal.SmoothScrollHelper {
        id: helper
        objectName: "smoothScrollHelper"
        target: flickable
        duration: 120
        easing: Easing.OutCubic
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


def test_smooth_scroll_frame_driver_runs_only_during_motion(qapp):
    """Frame drivers are idle at rest and preserve the requested end position.

    逐帧驱动器仅在运动期间运行，并保持请求的最终位置。
    """
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
    assert isinstance(window, QQuickWindow)
    helper = window.findChild(QQuickItem, "smoothScrollHelper")
    vertical = window.findChild(QObject, "smoothScrollVerticalFrameDriver")
    horizontal = window.findChild(QObject, "smoothScrollHorizontalFrameDriver")
    try:
        assert helper is not None
        assert vertical is not None
        assert horizontal is not None
        assert vertical.property("running") is False
        assert horizontal.property("running") is False

        assert QMetaObject.invokeMethod(window, "startScroll")
        assert _wait_for(lambda: vertical.property("running") is True)
        assert horizontal.property("running") is False
        completed = _wait_for(
            lambda: window.property("position") == 180
            and vertical.property("running") is False
        )
        assert completed, {
            "position": window.property("position"),
            "running": vertical.property("running"),
            "from": vertical.property("_fromValue"),
            "to": vertical.property("_toValue"),
            "duration": vertical.property("_durationMilliseconds"),
        }
        assert warnings == []
    finally:
        window.close()
        for obj in (window, component, engine):
            if shiboken6.isValid(obj):
                obj.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        qapp.processEvents()


ANCHOR_SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "smooth-scroll-anchor-keeper.qml")
)
ANCHOR_SCENE_SOURCE = b"""
import QtQuick
import QtQuick as QtQ
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/controls/containers/ScrollBar" as Internal

Window {
    id: root

    // Heights of one row far above the viewport and one far below it. Growing them
    // re-measures the content range exactly the way a virtual list refines its height
    // estimates while scrolling: contentHeight changes and the rows below the grown
    // one are re-positioned, while contentY is left untouched.
    property real tallRowHeight: 40
    property real lowRowHeight: 40

    width: 240
    height: 200
    visible: true

    QtQ.ListView {
        id: view
        objectName: "anchorView"
        anchors.fill: parent
        model: 40
        delegate: Rectangle {
            width: view.width
            height: index === 14
                ? root.tallRowHeight
                : (index === 25 ? root.lowRowHeight : 40)
            color: "#eeeeee"
        }
    }

    Internal.SmoothScrollHelper {
        id: helper
        objectName: "anchorHelper"
        target: view
        duration: 0
    }
}
"""


def _anchor_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    engine.addImportPath(str(ROOT / "prismqml"))
    component = QQmlComponent(engine)
    component.setData(ANCHOR_SCENE_SOURCE, ANCHOR_SCENE_URL)
    assert _wait_for(lambda: component.status() != QQmlComponent.Status.Loading)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow)
    return engine, component, window, warnings


def _dispose(engine, component, window, qapp):
    window.close()
    for obj in (window, component, engine):
        if shiboken6.isValid(obj):
            obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def _inner_list_view(view):
    """The virtual ListView inside the PrismQML wrapper (alias returns a raw pointer)."""
    return next(
        child
        for child in view.findChildren(QObject)
        if child.metaObject().indexOfProperty("atYEnd") >= 0
        and child.metaObject().indexOfProperty("contentHeight") >= 0
        and child.metaObject().indexOfProperty("count") >= 0
    )


def _anchor_state(inner):
    """Top visible row plus its offset from the viewport edge, and the axis position."""
    content_y = float(inner.property("contentY"))
    row = int(inner.indexAt(1, content_y + 1))
    item = inner.itemAtIndex(row)
    offset = float(item.y()) - content_y if item is not None else None
    return content_y, row, offset


def test_content_reflow_keeps_visible_rows_still(qapp):
    """A re-measured content range must not slide the visible rows.

    Virtual item views estimate the height of the delegates they have not created yet
    and refine those estimates while scrolling. The view rewrites only `contentHeight`,
    so every row above the viewport is re-positioned and the visible content slides —
    a real chat list measured a 96px whole-screen jump mid-scroll. The anchor keeper
    puts that movement back into the axis, so the axis follows the re-measured rows.

    内容范围被重测时不得让可见行整体滑动。虚拟项视图会为尚未孵化的委托估算高度并在滚动中
    修正；视图只改写 `contentHeight`，于是视口上方每一行都被重新定位、可见内容整体滑动
    ——真实聊天列表实测滚动途中整屏跳 96px。锚定器把这段位移补回轴向，让轴跟着被重排的行走。
    """
    engine, component, window, warnings = _anchor_scene()
    try:
        view = window.findChild(QObject, "anchorView")
        helper = window.findChild(QObject, "anchorHelper")
        keeper = window.findChild(QObject, "smoothScrollAnchorKeeper")
        assert view is not None and helper is not None and keeper is not None
        inner = view
        assert _wait_for(lambda: float(inner.property("contentHeight")) == 1600.0)

        # Move the axis once so the keeper can pick its anchor row, exactly the way a
        # scrolling user gives it one.
        # 先把轴动一次，让锚定器挑到锚点行——真实用户滚动时就是这样给它锚点的。
        inner.setProperty("contentY", 601.0)
        assert _wait_for(lambda: float(inner.property("contentY")) == 601.0)
        inner.setProperty("contentY", 600.0)
        assert _wait_for(lambda: float(inner.property("contentY")) == 600.0)
        assert _wait_for(lambda: int(keeper.property("_anchorRow")) >= 0), (
            keeper.property("_anchorRow")
        )
        assert float(keeper.property("compensatedDistance")) == 0

        # Grow a row far above the viewport by 200px. Every row below it is pushed
        # 200px down the content, so the keeper must put exactly that distance back;
        # without anchoring nothing compensates and the visible rows slide.
        # 把视口上方某行放大 200px，它下方每一行都被推后 200px，锚定器必须把这段距离补回去；
        # 没有锚定时不会有任何补偿，可见行就会滑动。
        window.setProperty("tallRowHeight", 240.0)
        assert _wait_for(
            lambda: abs(float(keeper.property("compensatedDistance")) - 200.0) < 2.0
        ), keeper.property("compensatedDistance")
        assert float(inner.property("contentHeight")) > 1700.0
        assert warnings == []
    finally:
        _dispose(engine, component, window, qapp)


def test_content_reflow_below_the_anchor_is_not_compensated(qapp):
    """Growth below the viewport must not move the axis.

    视口下方的增长不得移动轴向。
    """
    engine, component, window, warnings = _anchor_scene()
    try:
        view = window.findChild(QObject, "anchorView")
        keeper = window.findChild(QObject, "smoothScrollAnchorKeeper")
        assert view is not None and keeper is not None
        inner = view
        assert _wait_for(lambda: float(inner.property("contentHeight")) == 1600.0)

        # Move the axis once so the keeper can pick its anchor row.
        # 先把轴动一次，让锚定器挑到锚点行。
        inner.setProperty("contentY", 601.0)
        assert _wait_for(lambda: float(inner.property("contentY")) == 601.0)
        inner.setProperty("contentY", 600.0)
        assert _wait_for(lambda: float(inner.property("contentY")) == 600.0)

        # Row 30 sits below the viewport: growing it changes contentHeight but must not
        # move the rows the user is looking at, so the axis stays where it is.
        # 第 30 行在视口下方：放大它只会改变 contentHeight，不得移动用户正在看的内容，
        # 因此轴向保持不动。
        window.setProperty("lowRowHeight", 240.0)
        assert _wait_for(
            lambda: float(inner.property("contentHeight")) > 1700.0
        ), inner.property("contentHeight")
        assert _wait_for(lambda: float(inner.property("contentY")) == 600.0)
        assert abs(float(keeper.property("compensatedDistance"))) < 2.0
        assert warnings == []
    finally:
        _dispose(engine, component, window, qapp)
