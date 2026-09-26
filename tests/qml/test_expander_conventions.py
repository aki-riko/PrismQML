# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Expander and GroupBox runtime contracts. Expander 与 GroupBox 运行时合同。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QPoint,
    QPointF,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATHS = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "containers"
    / "Expander"
    / "ExpanderCore.qml",
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "containers"
    / "Expander"
    / "_internal"
    / "HeaderContent.qml",
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "containers"
    / "Expander"
    / "GroupBox.qml",
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "expander-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"

    readonly property bool expanderState: expander.isExpanded()
    readonly property bool groupState: groupBox.isChecked()
    readonly property string groupTitle: groupBox.getTitle()
    readonly property real groupContentGap: Enums.spacing.s
    readonly property real disabledOpacity: Enums.opacityLevel.disabled
    property var lastAddedWidget: null

    function resetGroup() {
        groupBox.setChecked(true)
    }

    function attachExpanderWidgets() {
        expander.addHeaderWidget(headerWidget)
        expander.addExpandWidget(expandWidget)
        lastAddedWidget = expandWidget
    }

    width: 720
    height: 420
    visible: true

    Expander {
        id: expander
        objectName: "expander"
        x: 20
        y: 20
        width: 320
        title: "Details"
        content: "Description"

        headerContent: Component {
            Item {
                objectName: "headerSlot"
                width: 40
                height: 24
            }
        }

        Rectangle {
            objectName: "expandedChild"
            width: 120
            height: 40
        }
    }

    Rectangle {
        id: headerWidget
        objectName: "headerWidget"
        width: 8
        height: 8
        visible: false
    }

    Rectangle {
        id: expandWidget
        objectName: "expandWidget"
        width: 8
        height: 8
        visible: false
    }

    GroupBox {
        id: groupBox
        objectName: "groupBox"
        x: 380
        y: 20
        width: 260
        height: 150
        title: "Options"
        checkable: true
        checked: true

        Rectangle {
            objectName: "groupChild"
            width: 100
            height: 40
        }
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 30
    return predicate()


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is accepted for accepted in allowed)
    ]


def _visual_items(item):
    result = []
    for child in item.childItems():
        result.append(child)
        result.extend(_visual_items(child))
    return result


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
    expander = window.findChild(QQuickItem, "expander")
    group_box = window.findChild(QQuickItem, "groupBox")
    _pump()
    return engine, component, window, expander, group_box, warnings


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
def expander_scene(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    try:
        yield (*scene[2:], windows_before)
    finally:
        _dispose_scene(scene[0], scene[1], scene[2])
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_expander_methods_animation_and_header_click(expander_scene):
    window, expander, _group_box, warnings, windows_before = expander_scene
    toggled = []
    expander.toggled.connect(toggled.append)
    collapsed_height = expander.height()
    title_items = [
        item for item in _visual_items(expander) if item.property("text") == "Details"
    ]
    assert len(title_items) == 1
    assert title_items[0].property("font").weight() == QFont.Weight.DemiBold
    assert not window.property("expanderState")

    assert QMetaObject.invokeMethod(expander, "toggle")
    assert _wait_for(lambda: window.property("expanderState"))
    assert _wait_for(lambda: expander.height() > collapsed_height)
    assert toggled == [True]

    assert QMetaObject.invokeMethod(expander, "collapse")
    assert _wait_for(lambda: not window.property("expanderState"))
    assert _wait_for(lambda: expander.height() == pytest.approx(collapsed_height))
    assert toggled == [True]

    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=QPoint(120, 50))
    assert _wait_for(lambda: window.property("expanderState"))
    assert toggled == [True, True]
    expander.setProperty("disabled", True)
    assert QMetaObject.invokeMethod(expander, "collapse")
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=QPoint(120, 50))
    _pump()
    assert not window.property("expanderState")
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_group_box_checkbox_controls_content(expander_scene):
    window, _expander, group_box, warnings, windows_before = expander_scene
    content_area = group_box.findChild(QQuickItem, "contentArea")
    toggled = []
    clicked = []
    group_box.toggled.connect(toggled.append)
    group_box.clicked.connect(clicked.append)
    assert window.property("groupState")
    assert window.property("groupTitle") == "Options"
    assert content_area.isEnabled()
    assert content_area.y() == pytest.approx(
        group_box.property("_titleHeight") + window.property("groupContentGap")
    )
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        pos=QPoint(group_box.x() + 24, group_box.y() + 10),
    )
    assert _wait_for(lambda: not window.property("groupState"))
    assert not window.property("groupState")
    assert not content_area.isEnabled()
    assert content_area.opacity() == pytest.approx(window.property("disabledOpacity"))
    assert toggled == [False]
    assert clicked == [False]
    assert QMetaObject.invokeMethod(window, "resetGroup")
    _pump()
    assert window.property("groupState")
    assert content_area.isEnabled()
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_expander_custom_header_and_widget_parent_contracts(expander_scene):
    window, expander, _group_box, warnings, _windows_before = expander_scene
    header_slot = window.findChild(QQuickItem, "headerSlot")
    header_widget = window.findChild(QQuickItem, "headerWidget")
    expand_widget = window.findChild(QQuickItem, "expandWidget")
    content_area = expander.findChild(QQuickItem, "contentArea")

    assert header_slot is not None
    assert header_widget is not None
    assert expand_widget is not None
    assert content_area is not None
    assert header_widget.parentItem() is not header_slot
    assert expand_widget.parentItem() is not content_area

    assert QMetaObject.invokeMethod(window, "attachExpanderWidgets")
    assert _wait_for(lambda: header_widget.parentItem() is header_slot)
    assert expand_widget.parentItem() is content_area
    last_added = window.property("lastAddedWidget")
    assert last_added is not None
    assert last_added.objectName() == "expandWidget"
    assert warnings == []


LONG_TITLE = (
    "PerformanceRiskWarning 性能风险警告（非拒审判据） · Python UI 性能风险警告（合并 46 项）"
)
LONG_CONTENT = (
    "OnUiInitFinished（第 741 行）调用高成本操作：CreateUI, RegisterUI。"
    "这是静态风险提示，需用 Tracy/AirPerf 在真实玩法中确认。"
)
SCENE_LONG_HEADER_SOURCE = (
    """
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "longHeaderWindow"

    width: 720
    height: 520
    visible: true

    Expander {
        id: plainHeader
        objectName: "plainHeader"
        x: 20
        y: 20
        width: 320
        title: __TITLE__
        content: __CONTENT__
    }

    Expander {
        id: wrappedHeader
        objectName: "wrappedHeader"
        x: 20
        y: 220
        width: 320
        wrapHeaderText: true
        title: __TITLE__
        content: __CONTENT__
    }
}
"""
    .replace("__TITLE__", '"' + LONG_TITLE + '"')
    .replace("__CONTENT__", '"' + LONG_CONTENT + '"')
    .encode("utf-8")
)


def test_expander_long_header_text_is_clamped_and_can_wrap():
    """长标题不得撑破头部；默认省略，wrapHeaderText 打开后换行并自适应高度。"""

    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(
        SCENE_LONG_HEADER_SOURCE,
        QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "expander-long-header.qml")),
    )
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow)
    _pump()

    plain = window.findChild(QQuickItem, "plainHeader")
    wrapped = window.findChild(QQuickItem, "wrappedHeader")
    assert plain is not None and wrapped is not None

    def header_items(expander):
        return (
            expander.findChild(QQuickItem, "expanderHeaderTitle"),
            expander.findChild(QQuickItem, "expanderHeaderContent"),
        )

    plain_title, plain_content = header_items(plain)
    wrapped_title, wrapped_content = header_items(wrapped)
    for item in (plain_title, plain_content, wrapped_title, wrapped_content):
        assert item is not None

    # 默认：单行 + 省略，绝不越过头部可用宽度
    assert plain_title.property("width") < plain_title.property("implicitWidth")
    assert plain_title.property("lineCount") == 1
    assert plain_title.property("truncated") is True
    assert plain_content.property("truncated") is True
    assert plain_title.property("width") <= plain.property("width")
    assert plain_content.property("width") <= plain.property("width")

    # 打开 wrapHeaderText：换成多行、不再被截断，头部按内容变高
    assert wrapped.property("wrapHeaderText") is True
    assert wrapped_title.property("lineCount") > 1
    assert wrapped_content.property("lineCount") > 1
    assert wrapped_title.property("truncated") is False
    assert wrapped_content.property("truncated") is False
    assert wrapped.property("height") > plain.property("height")
    # 文本右边缘始终留在头部区域内
    title_right = wrapped_title.mapToItem(
        window.contentItem(), QPointF(wrapped_title.width(), 0)
    ).x()
    assert title_right <= wrapped.property("x") + wrapped.property("width")

    # 关闭后回到单行省略
    wrapped.setProperty("wrapHeaderText", False)
    assert _wait_for(lambda: wrapped_title.property("lineCount") == 1)
    assert wrapped_title.property("truncated") is True

    assert warnings == []
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()
    assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_expander_sources_follow_conventions():
    violations = []
    for source_path in SOURCE_PATHS:
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        violations.extend(
            violation
            for violation in scan_source_text(
                source_path.read_text(encoding="utf-8"), path
            )
            if violation.rule in {"QML008", "QML009"}
        )
    assert violations == []
