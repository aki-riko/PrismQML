# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""ScrollAreaGrid selection and incremental loading contracts. ScrollAreaGrid 选择与增量加载合同。"""

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
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from prismqml import configure_qml_environment, register_types


ROOT = Path(__file__).resolve().parents[2]

GRID_SCENE = b"""
import QtQuick
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/controls/containers/ScrollBar"

Window {
    id: root
    objectName: "window"
    width: 240
    height: 200
    visible: true
    color: Enums.backgroundColor

    readonly property int total: grid.count
    readonly property var selection: grid.selectedIndexes
    readonly property int selectedCount: grid.selectedCount
    readonly property real contentOffset: grid.contentY
    readonly property color chromeColor: Enums.stateColor.accentLight
    readonly property bool loading: grid.isLoadingMore
    readonly property bool layerActive: {
        grid.selectionMode
        grid.contentY
        var children = grid.gridView.contentItem.children
        for (var index = 0; index < children.length; ++index) {
            var child = children[index]
            if (typeof child.active === "boolean"
                    && child.sourceComponent !== undefined)
                return child.active
        }
        return false
    }

    property int clickedCount: 0
    property int lastClicked: -1
    property int selectionEvents: 0
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

    function selectAll() { grid.selectAll() }
    function clearSelection() { grid.clearSelection() }
    function appendRows(count) {
        for (var index = 0; index < count; ++index)
            rows.append({ "text": "Row " + rows.count })
    }
    function scrollToEnd() { grid.contentY = grid.contentHeight }
    function scrollByDelta() { grid.contentY = grid.contentY + root.scrollDelta }
    function completeLoad() { grid.completeIncrementalLoad() }
    function enableIncremental() { grid.incrementalLoadingEnabled = true }

    ScrollAreaGrid {
        id: grid
        objectName: "grid"
        anchors.fill: parent
        model: rows
        cellWidth: 100
        cellHeight: 40
        selectionMode: Enums.scroll.selection_none
        incrementalLoadingEnabled: false
        incrementalLoadingThreshold: 1
        incrementalLoadingBatchSize: 20

        delegate: Rectangle {
            required property int index
            required property var modelData

            property string itemText: modelData && modelData.text !== undefined
                ? modelData.text : ""
            width: grid.cellWidth
            height: grid.cellHeight
            color: "transparent"
        }

        onItemClicked: (index, item) => {
            root.clickedCount += 1
            root.lastClicked = index
        }
        onSelectionChanged: root.selectionEvents += 1
        onLoadMoreRequested: (batchSize) => {
            root.requestCount += 1
            root.lastBatch = batchSize
            if (root.autoComplete) {
                root.appendRows(batchSize)
                grid.completeIncrementalLoad()
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


def _selection(window) -> list[int]:
    return [int(index) for index in _variant(window.property("selection"))]


def _cell_point(index: int) -> QPoint:
    """Centre of grid cell `index` in a 100x40 grid. 100x40 网格中单元格的中心。"""
    row, column = divmod(index, 2)
    return QPoint(column * 100 + 50, row * 40 + 20)


def _click(window, index: int, modifiers=Qt.KeyboardModifier.NoModifier) -> None:
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, modifiers, _cell_point(index)
    )
    _pump(60)


def _inside_loader(item: QQuickItem) -> bool:
    parent = item.parentItem()
    while parent is not None:
        if "Loader" in parent.metaObject().className():
            return True
        parent = parent.parentItem()
    return False


def _visual_descendants(root: QQuickItem) -> list[QQuickItem]:
    """Every item in the visual tree. 视觉树中的全部项目。

    Repeater delegates keep their QObject parent on the Repeater, so only the visual
    tree reaches them.
    Repeater 委托的 QObject 父对象仍是 Repeater, 只有视觉树能到达它们。
    """
    result = []
    pending = list(root.childItems())
    while pending:
        item = pending.pop()
        result.append(item)
        pending.extend(item.childItems())
    return result


def _chrome_rects(grid: QQuickItem, color) -> list[QQuickItem]:
    """Visible selection chrome rectangles. 可见的选择底板矩形。"""
    rects = []
    for child in _visual_descendants(grid):
        if "QQuickRectangle" not in child.metaObject().className():
            continue
        if not child.isVisible() or child.width() <= 0 or child.height() <= 0:
            continue
        if not _inside_loader(child):
            continue
        if child.property("color") == color:
            rects.append(child)
    return rects


def _scroll(window, delta: float) -> None:
    window.setProperty("scrollDelta", delta)
    assert QMetaObject.invokeMethod(window, "scrollByDelta")
    _pump(60)


def test_grid_default_mode_has_no_selection_layer_or_selection(qapp):
    """Default settings must keep the previous behaviour and painting. 默认设置必须保持既有行为与绘制。"""
    engine, component, window, warnings = _create_window(
        GRID_SCENE, "grid-selection-default.qml"
    )
    try:
        grid = window.findChild(QQuickItem, "grid")
        assert grid is not None
        assert window.property("total") == 60
        assert window.property("layerActive") is False
        assert _selection(window) == []
        assert _chrome_rects(grid, window.property("chromeColor")) == []

        _click(window, 1)
        _click(window, 3)
        assert window.property("clickedCount") == 0
        assert window.property("lastClicked") == -1
        assert window.property("selectionEvents") == 0
        assert _selection(window) == []
        assert window.property("layerActive") is False
        assert warnings == []
    finally:
        _dispose(qapp, engine, component, window)


def test_grid_selection_modes_follow_real_clicks(qapp):
    """Selection modes must react to real grid clicks. 选择模式必须响应真实网格点击。"""
    engine, component, window, warnings = _create_window(
        GRID_SCENE, "grid-selection-modes.qml"
    )
    try:
        grid = window.findChild(QQuickItem, "grid")
        assert grid is not None
        chrome_color = window.property("chromeColor")

        # Single 单选
        grid.setProperty("selectionMode", 1)
        _pump(60)
        assert window.property("layerActive") is True
        _click(window, 1)
        assert _selection(window) == [1]
        assert len(_chrome_rects(grid, chrome_color)) == 1
        _click(window, 3)
        assert _selection(window) == [3]

        # Multiple 多选
        grid.setProperty("selectionMode", 2)
        assert QMetaObject.invokeMethod(window, "clearSelection")
        _click(window, 1)
        _click(window, 3)
        assert _selection(window) == [1, 3]
        assert len(_chrome_rects(grid, chrome_color)) == 2
        _click(window, 1)
        assert _selection(window) == [3]

        # Extended 扩展
        grid.setProperty("selectionMode", 3)
        assert QMetaObject.invokeMethod(window, "clearSelection")
        _click(window, 2)
        assert _selection(window) == [2]
        _click(window, 5, Qt.KeyboardModifier.ControlModifier)
        assert _selection(window) == [2, 5]
        _click(window, 8, Qt.KeyboardModifier.ShiftModifier)
        assert _selection(window) == [5, 6, 7, 8]
        assert len(_chrome_rects(grid, chrome_color)) == 4
        _click(window, 1)
        assert _selection(window) == [1]

        # Programmatic API 编程接口
        assert QMetaObject.invokeMethod(window, "selectAll")
        assert _selection(window) == list(range(60))
        assert window.property("selectedCount") == 60
        assert QMetaObject.invokeMethod(window, "clearSelection")
        assert _selection(window) == []
        assert _chrome_rects(grid, chrome_color) == []
        assert window.property("clickedCount") > 0
        assert window.property("lastClicked") == 1
        assert warnings == []
    finally:
        _dispose(qapp, engine, component, window)


def test_grid_drag_scroll_keeps_working_with_selection(qapp):
    """The selection layer must not block native drag scrolling. 选择层不得阻断原生拖拽滚动。"""
    engine, component, window, warnings = _create_window(
        GRID_SCENE, "grid-selection-drag.qml"
    )
    try:
        grid = window.findChild(QQuickItem, "grid")
        grid.setProperty("selectionMode", 2)
        _pump(60)

        clicks_before = window.property("clickedCount")
        start = QPoint(50, 180)
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


def test_grid_incremental_loading_requests_one_batch_at_a_time(qapp):
    """Near-end grid scrolling asks for one batch until it completes. 接近末尾的网格滚动在完成前只请求一批。"""
    engine, component, window, warnings = _create_window(
        GRID_SCENE, "grid-incremental.qml"
    )
    try:
        assert window.property("total") == 60
        assert window.property("requestCount") == 0

        assert QMetaObject.invokeMethod(window, "scrollToEnd")
        _pump(120)
        assert window.property("requestCount") == 0

        assert QMetaObject.invokeMethod(window, "enableIncremental")
        assert _wait_for(lambda: window.property("requestCount") == 1)
        assert window.property("lastBatch") == 20
        assert _wait_for(lambda: window.property("total") == 80)
        assert window.property("loading") is False

        window.setProperty("autoComplete", False)
        _scroll(window, -120)
        assert QMetaObject.invokeMethod(window, "scrollToEnd")
        assert _wait_for(lambda: window.property("requestCount") == 2)
        assert window.property("loading") is True
        _scroll(window, -120)
        assert QMetaObject.invokeMethod(window, "scrollToEnd")
        _pump(120)
        assert window.property("requestCount") == 2

        assert QMetaObject.invokeMethod(window, "completeLoad")
        _pump(120)
        assert window.property("requestCount") == 2
        assert window.property("loading") is False

        _scroll(window, -120)
        assert QMetaObject.invokeMethod(window, "scrollToEnd")
        assert _wait_for(lambda: window.property("requestCount") == 3)
        assert warnings == []
    finally:
        _dispose(qapp, engine, component, window)
