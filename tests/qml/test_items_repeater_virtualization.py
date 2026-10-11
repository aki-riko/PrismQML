# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""ItemsRepeater virtualization contracts. ItemsRepeater 虚拟化合同。"""

from pathlib import Path, PurePosixPath

import pytest
import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QTimer,
    QUrl,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem

from prismqml import configure_qml_environment, register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]

STACK_SCENE = b"""
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

    readonly property int repeaterCount: repeater.count
    readonly property int instantiated: repeater.instantiatedCount
    readonly property int recycled: repeater.recycledCount
    readonly property real contentHeight: repeater.contentHeight
    readonly property real itemExtent: repeater.itemExtent
    readonly property real expectedExtent: Enums.controlSize.listItemHeight
    readonly property real viewportWidth: repeater.contentWidth
    readonly property int hitTop: repeater.indexAt(10, 5)

    property int jumpTarget: 100
    property real jumpOffset: 0

    function jump() { repeater.scrollToIndex(jumpTarget) }
    function jumpTo() { repeater.flickableItem.contentY = jumpOffset }

    ListModel {
        id: rows

        Component.onCompleted: {
            for (var index = 0; index < 500; ++index)
                rows.append({ "text": "Row " + index })
        }
    }

    ItemsRepeater {
        id: repeater
        objectName: "repeater"
        anchors.fill: parent
        model: rows

        delegate: Rectangle {
            required property int index
            required property var modelData

            property string itemText: modelData && modelData.text !== undefined
                ? modelData.text : ""
            color: "transparent"
        }
    }
}
"""

STAGGER_SCENE = b"""
import QtQuick
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/controls/data/List"
import "repeater_fixtures"

Window {
    id: root
    objectName: "window"
    width: 240
    height: 200
    visible: true
    color: Enums.backgroundColor

    readonly property real contentHeight: repeater.contentHeight
    readonly property real viewportWidth: repeater.flickableItem
        ? repeater.flickableItem.width : 0

    property real jumpOffset: 0

    function jumpTo() { repeater.flickableItem.contentY = jumpOffset }

    ListModel {
        id: rows

        Component.onCompleted: {
            for (var index = 0; index < 300; ++index)
                rows.append({ "text": "Row " + index })
        }
    }

    ItemsRepeater {
        id: repeater
        objectName: "repeater"
        anchors.fill: parent
        model: rows

        layout: ItemsRepeaterStaggerLayout {
        }

        delegate: Rectangle {
            required property int index
            required property var modelData

            property string itemText: modelData && modelData.text !== undefined
                ? modelData.text : ""
            color: "transparent"
        }
    }
}
"""

GRID_SCENE = b"""
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

    readonly property int itemsPerRow: gridLayout.itemsPerRow
    readonly property real cellWidth: gridLayout.cellWidth
    readonly property real contentHeight: repeater.contentHeight
    readonly property real viewportWidth: repeater.flickableItem
        ? repeater.flickableItem.width : 0
    readonly property int hitSecondRow: repeater.indexAt(130, 45)

    ListModel {
        id: rows

        Component.onCompleted: {
            for (var index = 0; index < 200; ++index)
                rows.append({ "text": "Row " + index })
        }
    }

    ItemsRepeater {
        id: repeater
        objectName: "repeater"
        anchors.fill: parent
        model: rows

        layout: ItemsUniformGridLayout {
            id: gridLayout
            minItemWidth: 100
            itemHeight: 40
        }

        delegate: Rectangle {
            required property int index
            required property var modelData

            property string itemText: modelData && modelData.text !== undefined
                ? modelData.text : ""
            color: "transparent"
        }
    }
}
"""

NO_REUSE_SCENE = b"""
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

    readonly property int recycled: repeater.recycledCount
    readonly property real itemExtent: repeater.itemExtent

    property real jumpOffset: 0

    function jumpTo() { repeater.flickableItem.contentY = jumpOffset }

    ListModel {
        id: rows

        Component.onCompleted: {
            for (var index = 0; index < 200; ++index)
                rows.append({ "text": "Row " + index })
        }
    }

    ItemsRepeater {
        id: repeater
        objectName: "repeater"
        anchors.fill: parent
        model: rows
        reuseItems: false

        delegate: Rectangle {
            required property int index
            required property var modelData

            property string itemText: modelData && modelData.text !== undefined
                ? modelData.text : ""
            color: "transparent"
        }
    }
}
"""

CHANGED_SOURCES = (
    "prismqml/PrismQML/PrismEnums/Scroll.qml",
    "prismqml/PrismQML/controls/data/List/ItemsRepeater.qml",
    "prismqml/PrismQML/controls/data/List/ItemsView.qml",
    "prismqml/PrismQML/controls/data/List/StandardUICommand.qml",
    "prismqml/PrismQML/controls/data/List/_internal/ItemsRepeaterCore.qml",
    "prismqml/PrismQML/controls/data/List/_internal/ItemsRepeaterLayout.qml",
    "prismqml/PrismQML/controls/data/List/_internal/ItemsStackLayout.qml",
    "prismqml/PrismQML/controls/data/List/_internal/ItemsUniformGridLayout.qml",
    "prismqml/PrismQML/controls/data/List/_internal/RepeaterModel.js",
    "prismqml/PrismQML/controls/data/List/_internal/StandardCommandTable.js",
    "prismqml/PrismQML/controls/data/List/_internal/collection/CollectionSelection.qml",
    "prismqml/PrismQML/controls/data/List/_internal/collection/IncrementalLoadTrigger.qml",
    "prismqml/PrismQML/controls/containers/ScrollBar/ScrollAreaGrid.qml",
)


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


def _delegates(repeater) -> list[QQuickItem]:
    """Every delegate object the repeater still owns, pooled or live. 重复器仍持有的全部委托对象。"""
    items = []
    for child in repeater.findChildren(QQuickItem):
        meta = child.metaObject()
        if meta.indexOfProperty("index") < 0 or meta.indexOfProperty("itemText") < 0:
            continue
        items.append(child)
    return items


def _live_delegates(repeater) -> list[QQuickItem]:
    """Visible delegates inside the viewport content. 视口内容中的可见委托。"""
    items = [child for child in _delegates(repeater) if child.isVisible()]
    items.sort(key=lambda item: int(item.property("index")))
    return items


def _indexes(repeater) -> list[int]:
    return [int(item.property("index")) for item in _live_delegates(repeater)]


def _pointer(item: QQuickItem) -> int:
    return int(shiboken6.getCppPointer(item)[0])


def test_items_repeater_virtualizes_default_stack_and_recycles(qapp):
    """Only the visible slice is instantiated and released delegates are reused.

    只有可见切片被实例化, 释放的委托被复用。
    """
    engine, component, window, warnings = _create_window(
        STACK_SCENE, "items-repeater-stack.qml"
    )
    try:
        repeater = window.findChild(QQuickItem, "repeater")
        assert repeater is not None
        assert window.property("repeaterCount") == 500

        extent = float(window.property("expectedExtent"))
        assert extent > 0
        assert float(window.property("itemExtent")) == pytest.approx(extent)
        assert float(window.property("contentHeight")) == pytest.approx(500 * extent)
        assert window.property("hitTop") == 0

        live = _live_delegates(repeater)
        indexes = [int(item.property("index")) for item in live]
        assert indexes == list(range(len(indexes))), indexes
        assert 0 < len(indexes) <= 20, indexes
        assert repeater.property("instantiatedCount") == len(indexes)
        assert repeater.property("recycledCount") == 0
        for item in live:
            assert item.property("itemText") == f"Row {item.property('index')}"
        assert float(live[0].property("width")) == pytest.approx(
            float(window.property("viewportWidth"))
        )
        assert float(live[0].property("height")) == pytest.approx(extent)

        before = {_pointer(item) for item in live}
        window.setProperty("jumpOffset", 400 * extent)
        assert QMetaObject.invokeMethod(window, "jumpTo")
        assert QMetaObject.invokeMethod(repeater, "syncNow")
        _pump(80)

        after_indexes = _indexes(repeater)
        assert after_indexes == list(
            range(after_indexes[0], after_indexes[0] + len(after_indexes))
        ), after_indexes
        assert 395 <= after_indexes[0] <= 405, after_indexes
        assert len(after_indexes) <= 20, after_indexes

        # The object count stays bounded after visiting a distant slice, and the
        # recycled instances are the very same C++ objects.
        # 访问远端切片后对象总数仍然有界, 且复用的就是同一批 C++ 对象。
        assert repeater.property("instantiatedCount") == len(after_indexes)
        assert len(_delegates(repeater)) <= 30
        after = {_pointer(item) for item in _live_delegates(repeater)}
        assert before & after, "released delegates were recreated instead of recycled"

        # The animated scroll path must land on the requested slice as well.
        # 动画滚动路径同样必须落到请求的切片上。
        window.setProperty("jumpTarget", 100)
        assert QMetaObject.invokeMethod(window, "jump")
        assert _wait_for(
            lambda: 95 <= _indexes(repeater)[0] <= 105, timeout_ms=4000
        ), _indexes(repeater)
        assert warnings == []
    finally:
        _dispose(qapp, engine, component, window)


def test_items_repeater_accepts_a_third_party_layout(qapp):
    """A custom layout drives geometry and content extent. 自定义布局驱动几何与内容范围。"""
    engine, component, window, warnings = _create_window(
        STAGGER_SCENE, "items-repeater-stagger.qml"
    )
    try:
        repeater = window.findChild(QQuickItem, "repeater")
        assert repeater is not None
        assert float(window.property("contentHeight")) == pytest.approx(300 * 40)

        live = _live_delegates(repeater)
        assert live
        width = float(window.property("viewportWidth"))
        assert width > 0
        for item in live:
            index = int(item.property("index"))
            expected_x = 20 if index % 2 == 1 else 0
            assert float(item.property("x")) == pytest.approx(expected_x), index
            assert float(item.property("width")) == pytest.approx(width - expected_x)
            assert float(item.property("y")) == pytest.approx(index * 40)

        window.setProperty("jumpOffset", 100 * 40)
        assert QMetaObject.invokeMethod(window, "jumpTo")
        assert QMetaObject.invokeMethod(repeater, "syncNow")
        _pump(80)
        scrolled = _indexes(repeater)
        assert 95 <= scrolled[0] <= 105, scrolled
        assert len(scrolled) <= 20, scrolled
        assert warnings == []
    finally:
        _dispose(qapp, engine, component, window)


def test_items_repeater_uniform_grid_layout_derives_columns(qapp):
    """The built-in uniform grid derives columns from the viewport. 内置等宽网格按视口推导列数。"""
    engine, component, window, warnings = _create_window(
        GRID_SCENE, "items-repeater-grid.qml"
    )
    try:
        repeater = window.findChild(QQuickItem, "repeater")
        assert repeater is not None
        assert window.property("itemsPerRow") == 2
        cell_width = float(window.property("cellWidth"))
        assert cell_width == pytest.approx(float(window.property("viewportWidth")) / 2)
        assert float(window.property("contentHeight")) == pytest.approx(100 * 40)
        assert window.property("hitSecondRow") == 3

        live = _live_delegates(repeater)
        indexes = [int(item.property("index")) for item in live]
        assert indexes == list(range(indexes[0], indexes[-1] + 1)), indexes
        assert indexes[0] == 0
        assert len(indexes) <= 20, indexes
        first, second = live[0], live[1]
        assert float(first.property("x")) == pytest.approx(0)
        assert float(second.property("x")) == pytest.approx(cell_width)
        assert float(first.property("y")) == pytest.approx(0)
        assert float(second.property("width")) == pytest.approx(cell_width)
        assert float(second.property("height")) == pytest.approx(40)
        assert warnings == []
    finally:
        _dispose(qapp, engine, component, window)


def test_items_repeater_without_reuse_destroys_released_delegates(qapp):
    """reuseItems: false must destroy instead of pool. reuseItems: false 必须销毁而非入池。"""
    engine, component, window, warnings = _create_window(
        NO_REUSE_SCENE, "items-repeater-no-reuse.qml"
    )
    try:
        repeater = window.findChild(QQuickItem, "repeater")
        assert repeater is not None
        extent = float(window.property("itemExtent"))
        live = _live_delegates(repeater)
        assert live
        released = live[0]

        window.setProperty("jumpOffset", 150 * extent)
        assert QMetaObject.invokeMethod(window, "jumpTo")
        assert QMetaObject.invokeMethod(repeater, "syncNow")
        _pump(80)

        assert repeater.property("recycledCount") == 0
        assert not shiboken6.isValid(released)
        remaining = _live_delegates(repeater)
        assert remaining
        assert int(remaining[0].property("index")) >= 140
        assert warnings == []
    finally:
        _dispose(qapp, engine, component, window)


def test_changed_sources_follow_qml_conventions():
    """Every changed source must be clean under the repository scanner.

    所有改动源码必须通过仓库扫描器。
    """
    violations = []
    for relative in CHANGED_SOURCES:
        path = ROOT / relative
        assert path.is_file(), relative
        violations.extend(
            scan_source_text(
                path.read_text(encoding="utf-8"), PurePosixPath(relative)
            )
        )
    assert [
        (item.path.as_posix(), item.line, item.rule, item.message)
        for item in violations
    ] == []
