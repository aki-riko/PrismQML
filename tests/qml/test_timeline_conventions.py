# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""TimelineCore runtime contracts. TimelineCore 运行时合同。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QPoint,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtGui import QGuiApplication
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
    / "TimelineCore.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "timeline-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"

    property var virtualItems: makeItems(12)
    property var largeVirtualItems: makeLargeItems()
    readonly property int virtualFlatCount: virtualTimeline._flatRows.length
    readonly property int largeVirtualFlatCount: largeVirtualTimeline._flatRows.length

    function makeItems(count) {
        var result = []
        for (var i = 0; i < count; i++) {
            result.push({
                "title": "Group " + i,
                "status": i % 2 ? "success" : "info",
                "cards": [
                    { "text": "Card " + i + "A", "commit": "a" + i },
                    { "text": "Card " + i + "B", "commit": "b" + i }
                ]
            })
        }
        return result
    }

    function appendVirtualGroup() {
        var next = virtualItems.slice()
        next.push({
            "title": "Appended",
            "status": "warning",
            "cards": [
                { "text": "Appended A", "commit": "append-a" },
                { "text": "Appended B", "commit": "append-b" }
            ]
        })
        virtualItems = next
    }

    function makeLargeItems() {
        var result = []
        for (var groupIndex = 0; groupIndex < 3; groupIndex++) {
            var cards = []
            for (var cardIndex = 0; cardIndex < 30; cardIndex++) {
                var suffix = cardIndex % 5 === 0
                    ? " with a deliberately long summary that wraps onto multiple lines and changes delegate height"
                    : ""
                cards.push({
                    "text": "Commit " + groupIndex + "-" + cardIndex + suffix,
                    "commit": "large-" + groupIndex + "-" + cardIndex
                })
            }
            result.push({
                "title": "Large Group " + groupIndex,
                "status": groupIndex % 2 ? "success" : "info",
                "cards": cards
            })
        }
        return result
    }

    width: 1140
    height: 857
    visible: true

    TimelineCore {
        id: timeline
        objectName: "timeline"
        x: 20
        y: 20
        width: 320
        items: [
            {
                "title": "Plan",
                "status": "info",
                "cards": [
                    { "text": "One", "description": "First", "commit": "one" },
                    "Two"
                ]
            },
            {
                "title": "Done",
                "status": "success",
                "cards": [{ "text": "Three", "strikeOut": true }]
            }
        ]
    }

    TimelineCore {
        id: virtualTimeline
        objectName: "virtualTimeline"
        x: 380
        y: 20
        width: 340
        height: 220
        virtualized: true
        selectedRole: "commit"
        selectedKey: "b0"
        items: root.virtualItems
    }

    TimelineCore {
        id: largeVirtualTimeline
        objectName: "largeVirtualTimeline"
        x: 760
        y: 20
        width: 340
        height: 817
        virtualized: true
        items: root.largeVirtualItems
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1500) -> bool:
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
    timeline = window.findChild(QQuickItem, "timeline")
    virtual_timeline = window.findChild(QQuickItem, "virtualTimeline")
    assert timeline is not None
    assert virtual_timeline is not None
    _pump()
    return engine, component, window, timeline, virtual_timeline, warnings


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
def timeline_scene(qapp):
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    try:
        yield (*scene[2:], windows_before)
    finally:
        _dispose_scene(scene[0], scene[1], scene[2])
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_timeline_nonvirtual_header_and_card_clicks(timeline_scene):
    window, timeline, _virtual_timeline, warnings, windows_before = timeline_scene
    headers = []
    cards = []
    card_data = []
    timeline.itemClicked.connect(lambda index, title: headers.append((index, title)))
    timeline.cardClicked.connect(
        lambda group, index, text: cards.append((group, index, text))
    )
    timeline.cardClickedData.connect(
        lambda group, index, data: card_data.append((group, index, data))
    )

    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=QPoint(100, 36))
    assert _wait_for(lambda: headers == [(0, "Plan")])
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=QPoint(120, 82))
    assert _wait_for(lambda: cards == [(0, 0, "One")])
    assert card_data[0][0:2] == (0, 0)
    assert card_data[0][2]["commit"] == "one"
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_timeline_virtual_append_preserves_scroll_and_reaches_end(timeline_scene):
    window, _timeline, virtual_timeline, warnings, windows_before = timeline_scene
    list_view = next(
        item
        for item in virtual_timeline.findChildren(QQuickItem)
        if "ListView" in item.metaObject().className()
    )
    reached = []
    virtual_timeline.reachedEnd.connect(lambda: reached.append(True))
    assert _wait_for(
        lambda: list_view.property("count") == window.property("virtualFlatCount")
    )
    assert list_view.property("count") == 36
    max_y = list_view.property("contentHeight") - list_view.height()
    list_view.setProperty("contentY", max_y - 5)
    assert _wait_for(lambda: reached)
    before_y = list_view.property("contentY")

    assert QMetaObject.invokeMethod(window, "appendVirtualGroup")
    assert _wait_for(lambda: window.property("virtualFlatCount") == 39)
    assert _wait_for(lambda: list_view.property("count") == 39)
    assert list_view.property("contentY") == pytest.approx(before_y)
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_timeline_virtual_scroll_to_start_tracks_dynamic_origin(timeline_scene):
    window, _timeline, _virtual_timeline, warnings, windows_before = timeline_scene
    large_timeline = window.findChild(QQuickItem, "largeVirtualTimeline")
    assert large_timeline is not None
    list_view = next(
        item
        for item in large_timeline.findChildren(QQuickItem)
        if "ListView" in item.metaObject().className()
    )
    helper = next(
        item
        for item in large_timeline.findChildren(QQuickItem)
        if "SmoothScrollHelper" in item.metaObject().className()
    )
    scroll_bar = next(
        item
        for item in list_view.childItems()
        if "ScrollBar" in item.metaObject().className()
    )
    handle = next(
        item
        for item in scroll_bar.childItems()
        if item.metaObject().className().startswith("QQuickRectangle")
    )

    assert _wait_for(
        lambda: list_view.property("count")
        == window.property("largeVirtualFlatCount")
    )
    assert list_view.property("count") == 93
    assert QMetaObject.invokeMethod(list_view, "positionViewAtEnd")
    assert _wait_for(
        lambda: abs(list_view.property("originY")) > 1,
        timeout_ms=3000,
    )
    assert QMetaObject.invokeMethod(helper, "syncPosition")

    assert QMetaObject.invokeMethod(helper, "scrollToStart")
    assert _wait_for(
        lambda: list_view.property("contentY")
        == pytest.approx(list_view.property("originY"), abs=1),
        timeout_ms=3000,
    ), (
        list_view.property("contentY"),
        list_view.property("originY"),
        helper.property("targetPos"),
        helper.property("smoothPos"),
        helper.property("minScroll"),
        helper.property("maxScroll"),
    )
    assert helper.property("targetPos") == pytest.approx(
        list_view.property("originY"), abs=1
    )
    assert handle.y() == pytest.approx(0, abs=1)
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_timeline_core_source_follows_conventions():
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(SOURCE_PATH.read_text(encoding="utf-8"), path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
