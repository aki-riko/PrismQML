# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""ItemsView selection and incremental loading contracts. ItemsView 选择与增量加载合同。"""

from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QPoint,
    QTimer,
    Qt,
    QUrl,
)
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from prismqml import configure_qml_environment, register_types


ROOT = Path(__file__).resolve().parents[2]

SELECTION_SCENE = b"""
import QtQuick
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/controls/data/List"

Window {
    id: root
    objectName: "window"
    width: 240
    height: 400
    visible: true
    color: Enums.backgroundColor

    readonly property var selection: view.selectedIndexes
    readonly property int selectedCount: view.selectedCount
    readonly property int currentIndex: view.currentIndex
    readonly property int chromeCount: view.selectionChromeCount
    readonly property int instantiated: view.instantiatedCount
    readonly property int total: view.count
    readonly property real rowExtent: 40
    readonly property real contentOffset: view.flickableItem
        ? view.flickableItem.contentY : -1
    readonly property var selectedTexts: {
        var items = view.selectedItems()
        var texts = []
        for (var cursor = 0; cursor < items.length; ++cursor)
            texts.push(items[cursor] ? items[cursor].text : "")
        return texts
    }

    property int clickedCount: 0
    property int lastClicked: -1
    property string lastClickedText: ""
    property int selectionEvents: 0
    property int shrinkTarget: 0

    ListModel {
        id: rows

        Component.onCompleted: {
            for (var index = 0; index < 40; ++index)
                rows.append({ "text": "Row " + index })
        }
    }

    function selectAll() { view.selectAll() }
    function clearSelection() { view.clearSelection() }
    function shrink() {
        while (rows.count > root.shrinkTarget)
            rows.remove(rows.count - 1, 1)
    }

    ItemsView {
        id: view
        objectName: "view"
        anchors.fill: parent
        model: rows
        selectionMode: Enums.scroll.selection_none
        layout: ItemsStackLayout {
            itemExtent: root.rowExtent
        }

        delegate: Rectangle {
            required property int index
            required property var modelData

            property string itemText: modelData && modelData.text !== undefined
                ? modelData.text : ""
            color: "transparent"
        }

        onItemClicked: (index, item) => {
            root.clickedCount += 1
            root.lastClicked = index
            root.lastClickedText = item && item.text !== undefined ? item.text : ""
        }
        onSelectionChanged: root.selectionEvents += 1
    }
}
"""

INCREMENTAL_SCENE = b"""
import QtQuick
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/controls/data/List"

Window {
    id: root
    objectName: "window"
    width: 240
    height: 200
    visible: true
    color: Enums.backgroundColor

    readonly property int total: view.count
    readonly property bool loading: view.isLoadingMore

    property int requestCount: 0
    property int lastBatch: -1
    property bool autoComplete: true
    property real scrollDelta: 0

    ListModel {
        id: rows

        Component.onCompleted: {
            for (var index = 0; index < 60; ++index)
                rows.append({ "text": "Row " + index })
        }
    }

    function appendRows(count) {
        for (var index = 0; index < count; ++index)
            rows.append({ "text": "Row " + rows.count })
    }
    function scrollToEnd() { view.flickableItem.contentY = view.contentHeight }
    function scrollByDelta() {
        view.flickableItem.contentY = view.flickableItem.contentY + root.scrollDelta
    }
    function completeLoad() { view.completeIncrementalLoad() }
    function enableIncremental() { view.incrementalLoadingEnabled = true }

    ItemsView {
        id: view
        objectName: "view"
        anchors.fill: parent
        model: rows
        layout: ItemsStackLayout {
            itemExtent: 40
        }
        incrementalLoadingEnabled: false
        incrementalLoadingThreshold: 2
        incrementalLoadingBatchSize: 20

        delegate: Rectangle {
            required property int index
            required property var modelData

            property string itemText: modelData && modelData.text !== undefined
                ? modelData.text : ""
            color: "transparent"
        }

        onLoadMoreRequested: (batchSize) => {
            root.requestCount += 1
            root.lastBatch = batchSize
            if (root.autoComplete) {
                root.appendRows(batchSize)
                view.completeIncrementalLoad()
            }
        }
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 30
    return predicate()


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _create_window(source: bytes, name: str):
    configure_qml_environment()
    engine = QQmlApplicationEngine()
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(source, QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / name)))
    for _ in range(100):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert window is not None, [error.toString() for error in component.errors()]
    _pump(200)
    return engine, component, window, warnings


def _dispose(qapp, engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def _visual_descendants(root: QQuickItem) -> list[QQuickItem]:
    """Every item in the visual tree. 视觉树中的全部项目。"""
    result = []
    pending = list(root.childItems())
    while pending:
        item = pending.pop()
        result.append(item)
        pending.extend(item.childItems())
    return result


def _view_chrome(view: QQuickItem, color) -> list[QQuickItem]:
    """Visible selection chrome rectangles of an ItemsView. ItemsView 的可见选择底板矩形。"""
    rects = []
    for child in _visual_descendants(view):
        if "QQuickRectangle" not in child.metaObject().className():
            continue
        if not child.isVisible() or child.width() <= 0 or child.height() <= 0:
            continue
        if child.property("color") == color:
            rects.append(child)
    return rects


def _selection(window) -> list[int]:
    return [int(index) for index in _variant(window.property("selection"))]


def _row_point(window, row: int) -> QPoint:
    extent = float(window.property("rowExtent"))
    return QPoint(60, int(row * extent + extent / 2))


def _click(window, row: int, modifiers=Qt.KeyboardModifier.NoModifier) -> None:
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, modifiers, _row_point(window, row)
    )
    _pump(60)


def _scroll(window, delta: float) -> None:
    window.setProperty("scrollDelta", delta)
    assert QMetaObject.invokeMethod(window, "scrollByDelta")
    _pump(60)


def test_items_view_selection_modes_follow_real_clicks(qapp):
    """Selection modes must react to real clicks and modifiers. 选择模式必须响应真实点击与修饰键。"""
    engine, component, window, warnings = _create_window(
        SELECTION_SCENE, "items-view-selection.qml"
    )
    try:
        view = window.findChild(QQuickItem, "view")
        assert view is not None
        assert window.property("total") == 40

        # selection_none still reports taps but never selects.
        # selection_none 仍然上报点击, 但从不选中。
        _click(window, 1)
        assert window.property("clickedCount") == 1
        assert window.property("lastClicked") == 1
        assert window.property("lastClickedText") == "Row 1"
        assert window.property("currentIndex") == 1
        assert _selection(window) == []
        assert window.property("selectionEvents") == 0
        assert window.property("chromeCount") == 0

        # Single 单选
        view.setProperty("selectionMode", 1)
        _click(window, 2)
        assert _selection(window) == [2]
        assert window.property("chromeCount") == 1

        # The chrome colour is owned by the entry and follows overrides.
        # 底板颜色由入口持有, 并跟随覆盖值。
        chrome_color = view.property("selectionChromeColor")
        assert len(_view_chrome(view, chrome_color)) == 1
        custom_color = QColor(12, 34, 56, 78)
        view.setProperty("selectionChromeColor", custom_color)
        _pump(60)
        assert len(_view_chrome(view, custom_color)) == 1
        assert _view_chrome(view, chrome_color) == []
        view.setProperty("selectionChromeColor", chrome_color)
        _pump(60)

        _click(window, 5)
        assert _selection(window) == [5]
        assert window.property("chromeCount") == 1

        # Multiple 多选
        view.setProperty("selectionMode", 2)
        assert QMetaObject.invokeMethod(window, "clearSelection")
        _click(window, 1)
        _click(window, 3)
        assert _selection(window) == [1, 3]
        assert window.property("chromeCount") == 2
        _click(window, 1)
        assert _selection(window) == [3]

        # Extended 扩展
        view.setProperty("selectionMode", 3)
        assert QMetaObject.invokeMethod(window, "clearSelection")
        _click(window, 2)
        assert _selection(window) == [2]
        _click(window, 5, Qt.KeyboardModifier.ControlModifier)
        assert _selection(window) == [2, 5]
        _click(window, 8, Qt.KeyboardModifier.ShiftModifier)
        assert _selection(window) == [5, 6, 7, 8]
        assert window.property("chromeCount") == 4
        _click(window, 1)
        assert _selection(window) == [1]

        # Programmatic API 编程接口
        assert QMetaObject.invokeMethod(window, "selectAll")
        assert _selection(window) == list(range(40))
        assert window.property("selectedCount") == 40
        assert window.property("chromeCount") == window.property("instantiated")
        assert _variant(window.property("selectedTexts"))[:2] == ["Row 0", "Row 1"]
        assert QMetaObject.invokeMethod(window, "clearSelection")
        assert _selection(window) == []
        assert window.property("chromeCount") == 0

        # Shrinking the model drops out-of-range members. 模型收缩会丢弃越界成员。
        view.setProperty("selectionMode", 2)
        assert QMetaObject.invokeMethod(window, "selectAll")
        assert window.property("selectedCount") == 40
        window.setProperty("shrinkTarget", 10)
        assert QMetaObject.invokeMethod(window, "shrink")
        assert _wait_for(lambda: window.property("total") == 10)
        assert _selection(window) == list(range(10))
        assert window.property("selectedCount") == 10
        assert window.property("chromeCount") == 10
        assert warnings == []
    finally:
        _dispose(qapp, engine, component, window)


def test_items_view_drag_scroll_keeps_working_with_selection(qapp):
    """The tap layer must not block native drag scrolling. 点击层不得阻断原生拖拽滚动。"""
    engine, component, window, warnings = _create_window(
        SELECTION_SCENE, "items-view-drag.qml"
    )
    try:
        view = window.findChild(QQuickItem, "view")
        view.setProperty("selectionMode", 2)
        assert QMetaObject.invokeMethod(window, "clearSelection")
        _pump(60)

        clicks_before = window.property("clickedCount")
        start = QPoint(60, 380)
        QTest.mousePress(
            window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, start
        )
        position = start
        for _ in range(10):
            position = QPoint(position.x(), position.y() - 14)
            QTest.mouseMove(window, position)
            _pump(16)
        QTest.mouseRelease(
            window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, position
        )
        _pump(300)

        assert float(window.property("contentOffset")) > 0
        assert window.property("clickedCount") == clicks_before
        assert _selection(window) == []
        assert warnings == []
    finally:
        _dispose(qapp, engine, component, window)


def test_items_view_keyboard_select_all_and_escape(qapp):
    """Ctrl+A and Escape drive selection while the view is focused. 聚焦时 Ctrl+A 与 Esc 驱动选择。"""
    engine, component, window, warnings = _create_window(
        SELECTION_SCENE, "items-view-keys.qml"
    )
    try:
        view = window.findChild(QQuickItem, "view")
        view.setProperty("selectionMode", 2)
        assert QMetaObject.invokeMethod(view, "forceActiveFocus")
        _pump(80)
        assert view.hasActiveFocus(), "the view never received active focus"

        QTest.keyClick(window, Qt.Key_A, Qt.KeyboardModifier.ControlModifier)
        _pump(80)
        assert _selection(window) == list(range(40))

        QTest.keyClick(window, Qt.Key_Escape)
        _pump(80)
        assert _selection(window) == []
        assert warnings == []
    finally:
        _dispose(qapp, engine, component, window)


def test_items_view_incremental_loading_requests_one_batch_at_a_time(qapp):
    """Near-end scrolling asks for exactly one batch until it completes.

    接近末尾的滚动在完成前只请求一个批次。
    """
    engine, component, window, warnings = _create_window(
        INCREMENTAL_SCENE, "items-view-incremental.qml"
    )
    try:
        assert window.property("total") == 60
        assert window.property("requestCount") == 0
        assert window.property("loading") is False

        # Scrolling to the end while the gate is disabled must stay silent.
        # 门关闭时滚动到末尾必须保持静默。
        assert QMetaObject.invokeMethod(window, "scrollToEnd")
        _pump(120)
        assert window.property("requestCount") == 0

        # Near the end with the gate on: one request, the consumer appends and completes.
        # 门开启且接近末尾: 一次请求, 消费方追加并完成。
        assert QMetaObject.invokeMethod(window, "enableIncremental")
        assert _wait_for(lambda: window.property("requestCount") == 1)
        assert window.property("lastBatch") == 20
        assert window.property("total") == 80
        assert window.property("loading") is False

        # A pending request must not be duplicated by further scrolling.
        # 挂起的请求不得因继续滚动而重复。
        window.setProperty("autoComplete", False)
        _scroll(window, -200)
        assert QMetaObject.invokeMethod(window, "scrollToEnd")
        assert _wait_for(lambda: window.property("requestCount") == 2)
        assert window.property("loading") is True
        _scroll(window, -150)
        assert QMetaObject.invokeMethod(window, "scrollToEnd")
        _pump(120)
        assert window.property("requestCount") == 2

        # Completing without appending must not re-fire on its own.
        # 未追加任何行就完成时, 不得自行重新触发。
        assert QMetaObject.invokeMethod(window, "completeLoad")
        _pump(120)
        assert window.property("requestCount") == 2
        assert window.property("loading") is False

        # A real scroll change near the end re-arms the gate.
        # 末尾附近的真实滚动变化会重新武装该门。
        _scroll(window, -150)
        assert QMetaObject.invokeMethod(window, "scrollToEnd")
        assert _wait_for(lambda: window.property("requestCount") == 3)
        assert warnings == []
    finally:
        _dispose(qapp, engine, component, window)
