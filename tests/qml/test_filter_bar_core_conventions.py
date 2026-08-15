# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Filter bar runtime contracts. 筛选栏运行时合同。"""

from pathlib import Path, PurePosixPath

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QPoint,
    QPointF,
    QTimer,
    Qt,
    QUrl,
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
    / "inputs"
    / "FilterBar"
    / "FilterBarCore.qml"
)
CONTENT_SOURCE_PATH = SOURCE_PATH.parent / "_internal" / "FilterBarContent.qml"
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "filter-bar-core-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    function replaceSingleItems() {
        singleFilter.items = ["one", "two", "three", "four"]
        singleFilter.currentIndex = 3
    }

    width: 760
    height: 260
    visible: true

    FilterBarCore {
        id: singleFilter
        objectName: "singleFilter"
        x: 40
        y: 50
        items: [
            "All",
            "Home",
            {"icon": "Image", "text": "Pictures"}
        ]
        currentIndex: 0
    }

    FilterBarCore {
        id: multiFilter
        objectName: "multiFilter"
        x: 40
        y: 140
        exclusive: false
        items: ["All", {"icon": "Image", "text": "Pictures"}, "Web"]
        selectedIndices: [0]
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1600) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _visual_descendants(root: QQuickItem) -> list[QQuickItem]:
    result = []
    pending = list(root.childItems())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.childItems())
    return result


def _delegates(control: QQuickItem) -> list[QQuickItem]:
    matches = [
        child
        for child in _visual_descendants(control)
        if child.metaObject().indexOfProperty("parsedData") >= 0
        and child.metaObject().indexOfProperty("selected") >= 0
        and child.metaObject().indexOfProperty("index") >= 0
    ]
    return sorted(matches, key=lambda item: item.property("index"))


def _indicator(control: QQuickItem) -> QQuickItem:
    matches = [
        child
        for child in _visual_descendants(control)
        if child.metaObject().indexOfProperty("targetIndex") >= 0
        and child.metaObject().indexOfProperty("refreshTrigger") >= 0
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _point_for(window: QQuickWindow, item: QQuickItem) -> QPoint:
    point = item.mapToItem(
        window.contentItem(), QPointF(item.width() / 2, item.height() / 2)
    )
    return QPoint(round(point.x()), round(point.y()))


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
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    window.requestActivate()
    assert _wait_for(window.isActive)
    single = window.findChild(QQuickItem, "singleFilter")
    multi = window.findChild(QQuickItem, "multiFilter")
    assert single is not None
    assert multi is not None
    assert _wait_for(lambda: len(_delegates(single)) == 3)
    assert _wait_for(lambda: len(_delegates(multi)) == 3)
    return engine, component, window, single, multi, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump()


def _assert_parse_contract(single: QQuickItem) -> None:
    assert _variant(single.parseItem("All")) == {"icon": "", "text": "All"}
    assert _variant(single.parseItem("Home")) == {"icon": "Home", "text": ""}
    assert _variant(single.parseItem({"icon": "Image", "text": "Pictures"})) == {
        "icon": "Image",
        "text": "Pictures",
    }
    assert _variant(single.parseItem(7)) == {"icon": "", "text": "7"}


def _assert_single_click(window, single, clicks, changes) -> None:
    third = _delegates(single)[2]
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _point_for(window, third),
    )
    assert single.property("currentIndex") == 2
    assert clicks == [2]
    assert changes == [2]
    assert _wait_for(lambda: third.property("selected"))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _point_for(window, third),
    )
    assert clicks == [2, 2]
    assert changes == [2]


def _assert_multi_clicks(window, multi, clicks, selections) -> None:
    first, second, _third = _delegates(multi)
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _point_for(window, second),
    )
    assert _variant(multi.property("selectedIndices")) == [0, 1]
    assert selections[-1] == [0, 1]
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _point_for(window, first),
    )
    assert _variant(multi.property("selectedIndices")) == [1]
    assert selections[-1] == [1]
    assert clicks == [1, 0]


def _assert_dynamic_items(window, single) -> None:
    assert QMetaObject.invokeMethod(
        window, "replaceSingleItems", Qt.ConnectionType.DirectConnection
    )
    assert _wait_for(lambda: len(_delegates(single)) == 4)
    indicator = _indicator(single)
    target_x = single.getItemX(3)
    target_width = single.getItemWidth(3)
    assert _wait_for(lambda: abs(indicator.x() - target_x) < 0.5)
    assert _wait_for(lambda: abs(indicator.width() - target_width) < 0.5)
    assert indicator.property("targetIndex") == 3


def test_filter_bar_single_multi_dynamic_and_signal_contracts(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, single, multi, warnings = _create_scene()
    try:
        single_clicks = []
        index_changes = []
        multi_clicks = []
        selections = []
        single.itemClicked.connect(single_clicks.append)
        single.indexChanged.connect(index_changes.append)
        multi.itemClicked.connect(multi_clicks.append)
        multi.selectionChanged.connect(lambda value: selections.append(_variant(value)))
        _assert_parse_contract(single)
        _assert_single_click(window, single, single_clicks, index_changes)
        _assert_multi_clicks(window, multi, multi_clicks, selections)
        _assert_dynamic_items(window, single)
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_filter_bar_core_source_conventions():
    sources = (
        (SOURCE_PATH, SOURCE_PATH.read_text(encoding="utf-8")),
        (CONTENT_SOURCE_PATH, CONTENT_SOURCE_PATH.read_text(encoding="utf-8")),
    )
    violations = []
    for path, source in sources:
        violations.extend(
            violation
            for violation in scan_source_text(
                source, PurePosixPath(path.relative_to(ROOT).as_posix())
            )
            if violation.rule in {"QML008", "QML009"}
        )
    assert violations == []
