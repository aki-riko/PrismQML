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
    QPointF,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtGui import QGuiApplication, QWheelEvent
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
GRAPH_SOURCE_PATH = SOURCE_PATH.with_name("TimelineGraphLayer.qml")
GRAPH_LABELS_SOURCE_PATH = SOURCE_PATH.with_name("TimelineGraphLabels.qml")
VIRTUAL_ROW_SOURCE_PATH = SOURCE_PATH.parent / "_internal" / "TimelineVirtualRow.qml"
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
    readonly property string virtualFirstTitle:
        virtualTimeline._flatRows.length > 0 ? virtualTimeline._flatRows[0].title : ""
    readonly property string virtualFirstCardText:
        virtualTimeline._flatRows.length > 1 ? virtualTimeline._flatRows[1].text : ""
    readonly property int largeVirtualFlatCount: largeVirtualTimeline._flatRows.length
    readonly property int graphFlatCount: graphTimeline._flatRows.length
    readonly property real timelinePulseOpacity: timeline._pulseOpacity

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

    function updateVirtualFirstGroupInPlace() {
        virtualItems[0].title = "Updated Group 0"
        virtualItems[0].cards[0].text = "Updated Card 0A"
        virtualItems = virtualItems.slice()
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

    width: 1500
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
                "dateKey": "2026-08-29",
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

    TimelineCore {
        id: graphTimeline
        objectName: "graphTimeline"
        x: 1120
        y: 20
        width: 360
        height: 360
        type: Enums.timeline.type_graph
        graphLaneCount: 3
        selectedRole: "commit"
        selectedKey: "merge"
        items: [
            {
                "title": "Graph",
                "graph": {
                    "segments": [
                        {"fromLane": 0, "toLane": 0, "colorIndex": 0},
                        {"fromLane": 1, "toLane": 1, "colorIndex": 1}
                    ]
                },
                "cards": [
                    {
                        "text": "Merge feature",
                        "time": "10:42",
                        "commit": "merge",
                        "labels": [{"text": "main", "status": Enums.statusLevel.info}],
                        "graph": {
                            "nodeLane": 0,
                            "nodeColorIndex": 0,
                            "segments": [
                                {"fromLane": 0, "toLane": 0, "colorIndex": 0,
                                    "endAtNode": true},
                                {"fromLane": 0, "toLane": 1, "colorIndex": 1,
                                    "startAtNode": true}
                            ]
                        }
                    },
                    {
                        "text": "Feature work",
                        "time": "09:18",
                        "commit": "feature",
                        "graph": {
                            "nodeLane": 1,
                            "nodeColorIndex": 1,
                            "segments": [
                                {"fromLane": 0, "toLane": 0, "colorIndex": 0},
                                {"fromLane": 1, "toLane": 1, "colorIndex": 1}
                            ]
                        }
                    }
                ]
            }
        ]
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


def _visual_descendants(item):
    descendants = []
    for child in item.childItems():
        descendants.append(child)
        descendants.extend(_visual_descendants(child))
    return descendants


def _named_visible_descendants(item, object_name):
    return [
        child
        for child in _visual_descendants(item)
        if child.objectName() == object_name and child.isVisible()
    ]


def _send_wheel(window, item, delta):
    position = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    global_position = QPointF(window.x() + position.x(), window.y() + position.y())
    event = QWheelEvent(
        position,
        global_position,
        QPoint(0, 0),
        QPoint(0, delta),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    assert QGuiApplication.sendEvent(window, event)
    return event


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


def test_timeline_status_connectors_share_the_node_center(timeline_scene):
    window, timeline, virtual_timeline, warnings, windows_before = timeline_scene

    for owner in (timeline, virtual_timeline):
        nodes = _named_visible_descendants(owner, "timelineStatusNode")
        connectors = _named_visible_descendants(owner, "timelineStatusConnector")
        assert nodes
        assert connectors
        node_center = nodes[0].mapToItem(
            owner, QPointF(nodes[0].width() / 2, 0)
        ).x()
        connector_centers = [
            connector.mapToItem(
                owner, QPointF(connector.width() / 2, 0)
            ).x()
            for connector in connectors
        ]
        assert connector_centers == pytest.approx([node_center] * len(connectors))

    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_timeline_cards_keep_their_single_managed_inset(timeline_scene):
    window, timeline, virtual_timeline, warnings, windows_before = timeline_scene
    cards = [
        item
        for owner in (timeline, virtual_timeline)
        for item in _visual_descendants(owner)
        if item.property("clickEnabled") is True
        and item.property("contentPadding") is not None
    ]

    assert cards
    assert all(card.property("contentPadding") == 0 for card in cards)
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
    assert virtual_timeline.property("_lastFlatBuildGroupCount") == 12
    max_y = list_view.property("contentHeight") - list_view.height()
    list_view.setProperty("contentY", max_y - 5)
    assert _wait_for(lambda: reached)
    before_y = list_view.property("contentY")

    assert QMetaObject.invokeMethod(window, "appendVirtualGroup")
    assert _wait_for(lambda: window.property("virtualFlatCount") == 39)
    assert _wait_for(lambda: list_view.property("count") == 39)
    assert virtual_timeline.property("_lastFlatBuildGroupCount") == 1
    assert list_view.property("contentY") == pytest.approx(before_y)
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_timeline_virtual_same_group_reference_refreshes_existing_rows(timeline_scene):
    window, _timeline, virtual_timeline, warnings, windows_before = timeline_scene
    assert _wait_for(lambda: window.property("virtualFirstTitle") == "Group 0")

    assert QMetaObject.invokeMethod(window, "updateVirtualFirstGroupInPlace")
    assert _wait_for(
        lambda: window.property("virtualFirstTitle") == "Updated Group 0"
    )
    assert window.property("virtualFirstCardText") == "Updated Card 0A"
    assert virtual_timeline.property("_lastFlatBuildGroupCount") == 12
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
        for item in large_timeline.findChildren(QQuickItem)
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
        == pytest.approx(list_view.property("originY"), abs=1)
        and helper.property("targetPos")
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


def test_timeline_virtual_wheel_bounces_at_both_boundaries_without_jitter(
    timeline_scene,
):
    """Wheel overshoot must return once without boundary jitter. 滚轮越界须单次回弹且不抖动。"""
    window, _timeline, _virtual_timeline, warnings, windows_before = timeline_scene
    large_timeline = window.findChild(QQuickItem, "largeVirtualTimeline")
    assert large_timeline is not None
    list_view = next(
        item
        for item in large_timeline.findChildren(QQuickItem)
        if item.objectName() == "timelineVirtualViewport"
    )
    helper = next(
        item
        for item in large_timeline.findChildren(QQuickItem)
        if "SmoothScrollHelper" in item.metaObject().className()
    )
    assert _wait_for(
        lambda: list_view.property("count")
        == window.property("largeVirtualFlatCount")
        and helper.property("maxScroll") > helper.property("minScroll")
    )

    for at_start, wheel_delta in ((True, 120), (False, -120)):
        method = "scrollToStart" if at_start else "scrollToEnd"
        boundary_name = "minScroll" if at_start else "maxScroll"
        assert QMetaObject.invokeMethod(helper, method)
        assert _wait_for(
            lambda: list_view.property("contentY")
            == pytest.approx(helper.property(boundary_name), abs=0.5)
            and not helper.property("isOvershot")
        )
        visual_row = None
        baseline_row_y = 0.0
        if at_start:
            visual_rows = [
                item
                for item in _visual_descendants(list_view)
                if "TimelineVirtualRow" in item.metaObject().className()
                and item.isVisible()
            ]
            assert visual_rows
            visual_row = min(
                visual_rows,
                key=lambda item: item.mapToItem(list_view, QPointF(0, 0)).y(),
            )
            baseline_row_y = visual_row.mapToItem(list_view, QPointF(0, 0)).y()
        boundary = float(helper.property(boundary_name))
        maximum_overshoot = float(helper.property("_maxOvershoot"))
        visual_offsets = []
        position_samples = [
            (
                float(list_view.property("contentY")),
                float(helper.property("minScroll")),
                float(helper.property("maxScroll")),
            )
        ]
        helper._visualOvershootOffsetChanged.connect(
            lambda bucket=visual_offsets: bucket.append(
                float(helper.property("_visualOvershootOffset"))
            )
        )
        list_view.contentYChanged.connect(
            lambda bucket=position_samples: bucket.append(
                (
                    float(list_view.property("contentY")),
                    float(helper.property("minScroll")),
                    float(helper.property("maxScroll")),
                )
            )
        )

        event = _send_wheel(window, list_view, wheel_delta)
        assert event.isAccepted()
        crossed = (lambda value: value > 1) if at_start else (
            lambda value: value < -1
        )
        assert _wait_for(
            lambda: any(crossed(value) for value in visual_offsets)
        ), visual_offsets
        if visual_row is not None:
            shifted_row_y = visual_row.mapToItem(list_view, QPointF(0, 0)).y()
            assert shifted_row_y > baseline_row_y + 1
        assert all(
            abs(value) <= maximum_overshoot + 0.5 for value in visual_offsets
        ), visual_offsets
        assert all(
            minimum - 0.5 <= content_y <= maximum + 0.5
            for content_y, minimum, maximum in position_samples
        ), position_samples
        assert _wait_for(
            lambda: list_view.property("contentY")
            == pytest.approx(boundary, abs=0.5)
            and helper.property("_visualOvershootOffset")
            == pytest.approx(0, abs=0.5)
            and not helper.property("isOvershot"),
            timeout_ms=3000,
        )
        if visual_row is not None:
            assert visual_row.mapToItem(
                list_view, QPointF(0, 0)
            ).y() == pytest.approx(baseline_row_y, abs=0.5)
        magnitudes = [abs(value) for value in visual_offsets]
        outward = magnitudes[: magnitudes.index(max(magnitudes)) + 1]
        assert all(
            outward[index] + 2 >= outward[index - 1]
            for index in range(1, len(outward))
        ), visual_offsets
        settled_index = len(visual_offsets)
        _pump(300)
        assert all(
            value == pytest.approx(0, abs=0.5)
            for value in visual_offsets[settled_index:]
        ), visual_offsets

    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def _virtual_viewport_and_helper(owner):
    list_view = next(
        item
        for item in owner.findChildren(QQuickItem)
        if item.objectName() == "timelineVirtualViewport"
    )
    helper = next(
        item
        for item in owner.findChildren(QQuickItem)
        if "SmoothScrollHelper" in item.metaObject().className()
    )
    return list_view, helper


def test_timeline_virtual_continuous_same_direction_wheel_keeps_one_bounce(
    timeline_scene,
):
    """Continuous same-direction wheel must not re-bounce at a boundary.

    连续同向滚轮在边界不得反复回弹。
    """
    window, _timeline, _virtual_timeline, warnings, windows_before = timeline_scene
    large_timeline = window.findChild(QQuickItem, "largeVirtualTimeline")
    assert large_timeline is not None
    list_view, helper = _virtual_viewport_and_helper(large_timeline)
    assert _wait_for(
        lambda: list_view.property("count")
        == window.property("largeVirtualFlatCount")
        and helper.property("maxScroll") > helper.property("minScroll")
    )

    assert QMetaObject.invokeMethod(helper, "scrollToStart")
    assert _wait_for(
        lambda: list_view.property("contentY")
        == pytest.approx(helper.property("minScroll"), abs=0.5)
        and not helper.property("isOvershot"),
        timeout_ms=3000,
    )
    maximum_overshoot = float(helper.property("_maxOvershoot"))
    samples = []

    def capture_sample():
        samples.append(
            (
                round(float(helper.property("_visualOvershootOffset")), 1),
                round(float(list_view.property("contentY")), 1),
                round(float(helper.property("minScroll")), 1),
                round(float(helper.property("maxScroll")), 1),
            )
        )

    helper._visualOvershootOffsetChanged.connect(capture_sample)
    list_view.contentYChanged.connect(
        capture_sample
    )
    content_heights = []
    list_view.contentHeightChanged.connect(
        lambda: content_heights.append(float(list_view.property("contentHeight")))
    )
    capture_sample()

    # Keep wheeling the same direction while the bounce is still in flight.
    # Force wrapped delegates to remeasure during the burst; this is the real
    # geometry path that used to clamp contentY to zero. 回弹进行中强制换行委托
    # 重测,覆盖此前会把 contentY 夹回零的真实几何路径。
    burst_offsets = []
    original_width = large_timeline.width()
    for index in range(6):
        if index == 2:
            large_timeline.setWidth(original_width - 64)
        event = _send_wheel(window, list_view, 120)
        assert event.isAccepted()
        _pump(40)
        burst_offsets.append(float(helper.property("_visualOvershootOffset")))
    large_timeline.setWidth(original_width)
    _pump(40)
    burst_sample_count = len(samples)
    # Settle against the live boundary, which delegate re-measurement may have moved.
    # 与实时边界比较落位，delegate 重新测量可能已移动它。
    assert _wait_for(
        lambda: list_view.property("contentY")
        == pytest.approx(float(helper.property("minScroll")), abs=0.5)
        and helper.property("_visualOvershootOffset")
        == pytest.approx(0, abs=0.5)
        and not helper.property("isOvershot"),
        timeout_ms=3000,
    )
    _pump(200)

    assert samples
    assert content_heights
    # The first overshoot remains visible, but logical contentY never leaves the
    # current ListView bounds. 首次超出仍可见,逻辑 contentY 始终留在实时合法边界内。
    assert any(offset > 1 for offset, *_rest in samples), samples
    assert all(
        abs(offset) <= maximum_overshoot + 1
        for offset, *_rest in samples
    ), samples
    assert all(
        minimum - 0.5 <= content_y <= maximum + 0.5
        for _offset, content_y, minimum, maximum in samples
    ), samples
    # Once the outward visual leg starts, the same wheel burst must not reset it
    # to zero and launch it again. 同一滚轮串的视觉外移一旦开始,不得归零后重新外移。
    active_samples = samples[:burst_sample_count]
    first_outward = next(
        index for index, sample in enumerate(active_samples) if sample[0] > 1
    )
    assert all(
        offset > 0.5 for offset, *_rest in active_samples[first_outward:]
    ), active_samples
    assert all(offset > 0.5 for offset in burst_offsets), burst_offsets
    # Rest against the boundary as it stands now, not the pre-burst snapshot.
    # 与当前边界比较落位，而非滚轮前的快照。
    assert list_view.property("contentY") == pytest.approx(
        float(helper.property("minScroll")), abs=0.5
    )
    assert helper.property("_visualOvershootOffset") == pytest.approx(0, abs=0.5)
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_timeline_virtual_reverse_wheel_rearms_boundary_bounce(timeline_scene):
    """Reverse input into content must re-arm the boundary bounce.

    反向输入回到内容区后必须重新武装边界回弹。
    """
    window, _timeline, _virtual_timeline, warnings, windows_before = timeline_scene
    large_timeline = window.findChild(QQuickItem, "largeVirtualTimeline")
    assert large_timeline is not None
    list_view, helper = _virtual_viewport_and_helper(large_timeline)
    assert _wait_for(
        lambda: list_view.property("count")
        == window.property("largeVirtualFlatCount")
        and helper.property("maxScroll") > helper.property("minScroll")
    )

    assert QMetaObject.invokeMethod(helper, "scrollToStart")
    assert _wait_for(
        lambda: list_view.property("contentY")
        == pytest.approx(helper.property("minScroll"), abs=0.5)
        and not helper.property("isOvershot"),
        timeout_ms=3000,
    )
    boundary = float(helper.property("minScroll"))

    for _ in range(4):
        assert _send_wheel(window, list_view, 120).isAccepted()
        _pump(40)
    assert _wait_for(
        lambda: list_view.property("contentY") == pytest.approx(boundary, abs=0.5)
        and helper.property("_visualOvershootOffset")
        == pytest.approx(0, abs=0.5)
        and not helper.property("isOvershot"),
        timeout_ms=3000,
    )

    # Reverse into the content region, then come back to the boundary.
    # 反向进入内容区，再回到边界。
    assert _send_wheel(window, list_view, -120).isAccepted()
    assert _wait_for(lambda: list_view.property("contentY") > boundary + 5)
    _pump(400)
    assert QMetaObject.invokeMethod(helper, "scrollToStart")
    assert _wait_for(
        lambda: list_view.property("contentY") == pytest.approx(boundary, abs=0.5)
        and not helper.property("isOvershot"),
        timeout_ms=3000,
    )

    visual_trajectory = []
    helper._visualOvershootOffsetChanged.connect(
        lambda: visual_trajectory.append(
            float(helper.property("_visualOvershootOffset"))
        )
    )
    assert _send_wheel(window, list_view, 120).isAccepted()
    assert _wait_for(
        lambda: any(value > 1 for value in visual_trajectory)
    ), visual_trajectory
    assert _wait_for(
        lambda: list_view.property("contentY") == pytest.approx(boundary, abs=0.5)
        and helper.property("_visualOvershootOffset")
        == pytest.approx(0, abs=0.5)
        and not helper.property("isOvershot"),
        timeout_ms=3000,
    )
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_timeline_virtual_scrollbar_stays_visible_during_height_relayout(
    timeline_scene,
):
    """Remeasure must not expose transient scrollbar state. 重测不得暴露瞬态滚动条状态。"""
    window, _timeline, _virtual_timeline, warnings, windows_before = timeline_scene
    large_timeline = window.findChild(QQuickItem, "largeVirtualTimeline")
    assert large_timeline is not None
    descendants = large_timeline.findChildren(QQuickItem)
    list_view = next(
        item
        for item in descendants
        if item.objectName() == "timelineVirtualViewport"
    )
    scroll_state = next(
        item
        for item in descendants
        if "ScrollViewportState" in item.metaObject().className()
    )
    scroll_bar = next(
        item
        for item in descendants
        if item.metaObject().className().split("_QMLTYPE_")[0] == "ScrollBar"
    )

    assert _wait_for(
        lambda: list_view.property("count")
        == window.property("largeVirtualFlatCount")
        and bool(scroll_state.property("needsVertical"))
        and bool(scroll_bar.property("visible"))
    )
    model_count = int(list_view.property("count"))
    needs_states = []
    visible_states = []
    scroll_state.needsVerticalChanged.connect(
        lambda: needs_states.append(bool(scroll_state.property("needsVertical")))
    )
    scroll_bar.visibleChanged.connect(
        lambda: visible_states.append(bool(scroll_bar.property("visible")))
    )

    for index in range(60):
        maximum = max(
            0.0,
            float(list_view.property("contentHeight")) - list_view.height(),
        )
        ratio = ((index * 37) % 59) / 58 if index else 0
        list_view.setProperty("contentY", maximum * ratio)
        QCoreApplication.processEvents()
        _pump(8)
    _pump(100)

    assert int(list_view.property("count")) == model_count
    assert False not in needs_states, needs_states
    assert False not in visible_states, visible_states
    assert bool(scroll_state.property("needsVertical")) is True
    assert bool(scroll_bar.property("visible")) is True
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_timeline_graph_type_uses_virtual_rows_and_renders_graph_layers(timeline_scene):
    window, _timeline, _virtual_timeline, warnings, windows_before = timeline_scene
    graph_timeline = window.findChild(QQuickItem, "graphTimeline")
    assert graph_timeline is not None
    list_view = next(
        item
        for item in graph_timeline.findChildren(QQuickItem)
        if "ListView" in item.metaObject().className()
    )

    assert graph_timeline.property("_usesVirtualList") is True
    assert _wait_for(
        lambda: list_view.property("count") == window.property("graphFlatCount")
    )
    assert list_view.property("count") == 3
    def visible_graph_layers():
        return [
            item
            for item in _visual_descendants(graph_timeline)
            if item.objectName() == "timelineGraphLayer" and item.isVisible()
        ]

    assert _wait_for(lambda: len(visible_graph_layers()) == 3)
    graph_layers = visible_graph_layers()
    assert all(
        layer.width() == pytest.approx(graph_timeline.property("_graphWidth"))
        for layer in graph_layers
    )
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_timeline_time_badges_are_optional_and_keep_header_dates(timeline_scene):
    window, timeline, _virtual_timeline, warnings, windows_before = timeline_scene
    graph_timeline = window.findChild(QQuickItem, "graphTimeline")
    assert graph_timeline is not None
    assert _wait_for(
        lambda: len(
            [
                item
                for item in _visual_descendants(graph_timeline)
                if item.objectName() == "timelineCardTimeBadge" and item.isVisible()
            ]
        ) == 2
    )
    standard_badges = [
        item
        for item in _visual_descendants(timeline)
        if item.objectName() == "timelineCardTimeBadge" and item.isVisible()
    ]
    assert standard_badges == []
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_timeline_pulse_is_shared_and_bounded(timeline_scene):
    window, _timeline, _virtual_timeline, warnings, windows_before = timeline_scene
    graph_timeline = window.findChild(QQuickItem, "graphTimeline")
    assert graph_timeline is not None
    assert _wait_for(
        lambda: any(
            item.objectName() == "timelineGraphLayer" and item.isVisible()
            for item in _visual_descendants(graph_timeline)
        )
    )
    graph_layer = next(
        item
        for item in _visual_descendants(graph_timeline)
        if item.objectName() == "timelineGraphLayer" and item.isVisible()
    )
    samples = []
    for _ in range(10):
        samples.append(float(window.property("timelinePulseOpacity")))
        assert graph_layer.opacity() == pytest.approx(samples[-1], abs=0.001)
        _pump(120)

    assert min(samples) >= 0.84
    assert max(samples) <= 1.01
    assert max(samples) - min(samples) > 0.02, samples
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_timeline_selection_uses_render_thread_animators(timeline_scene):
    """Selection motion must survive GUI-thread result processing. 选中动效须独立于 GUI 线程。"""
    window, _timeline, _virtual_timeline, warnings, windows_before = timeline_scene
    graph_timeline = window.findChild(QQuickItem, "graphTimeline")
    assert graph_timeline is not None
    assert _wait_for(
        lambda: len(
            [
                item
                for item in _visual_descendants(graph_timeline)
                if item.objectName() == "timelineCardSelectionIndicator"
            ]
        )
        == 2
    )

    graph_timeline.setProperty("selectedKey", "feature")
    _pump(250)
    descendants = _visual_descendants(graph_timeline)
    card_indicators = [
        item
        for item in descendants
        if item.objectName() == "timelineCardSelectionIndicator"
    ]
    graph_rings = [
        item
        for item in descendants
        if item.objectName() == "timelineGraphSelectionRing"
    ]
    card_outlines = [
        item
        for item in descendants
        if item.objectName() == "timelineCardSelectionOutline"
    ]

    assert sorted(round(item.opacity(), 3) for item in card_indicators) == [0.0, 1.0]
    graph_ring_opacities = [round(item.opacity(), 3) for item in graph_rings]
    assert graph_ring_opacities.count(1.0) == 1
    assert all(opacity in (0.0, 1.0) for opacity in graph_ring_opacities)
    assert sorted(round(item.opacity(), 3) for item in card_outlines) == [0.0, 1.0]
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_timeline_selection_animation_does_not_change_geometry_on_gui_thread():
    timeline_source = SOURCE_PATH.read_text(encoding="utf-8")
    graph_source = GRAPH_SOURCE_PATH.read_text(encoding="utf-8")
    virtual_row_source = VIRTUAL_ROW_SOURCE_PATH.read_text(encoding="utf-8")

    assert "Behavior on height" not in timeline_source
    assert "TimelineInternal.TimelineVirtualRow" in timeline_source
    assert "Status hairline" not in virtual_row_source
    assert "timelineGraphNodeHalo" not in graph_source
    assert "timelineGraphSelectionHalo" not in graph_source
    assert "paintColor: control.selected" in graph_source
    assert "SequentialAnimation on _pulsePhase" in timeline_source
    assert "NumberAnimation" in timeline_source
    assert "OpacityAnimator" in virtual_row_source
    assert "ScaleAnimator" in virtual_row_source
    assert "OpacityAnimator" in graph_source
    assert "ScaleAnimator" in graph_source


def test_timeline_core_source_follows_conventions():
    for source_path in (SOURCE_PATH, GRAPH_SOURCE_PATH, GRAPH_LABELS_SOURCE_PATH):
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        violations = scan_source_text(source_path.read_text(encoding="utf-8"), path)
        assert [
            violation
            for violation in violations
            if violation.rule in {"QML008", "QML009"}
    ] == []


def test_timeline_time_and_date_fields_are_forwarded_without_formatting():
    timeline_source = SOURCE_PATH.read_text(encoding="utf-8")
    virtual_row_source = VIRTUAL_ROW_SOURCE_PATH.read_text(encoding="utf-8")

    assert '"dateKey": grp.dateKey || ""' in timeline_source
    assert '"time": cardObject ? card.time || "" : ""' in timeline_source
    assert 'objectName: "timelineCardTimeBadge"' in virtual_row_source
