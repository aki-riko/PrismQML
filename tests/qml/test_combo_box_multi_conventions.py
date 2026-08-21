# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Multi-select combo parent-chain regressions. 多选下拉框父链回归。"""

from pathlib import Path, PurePosixPath

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QObject, QPoint, QPointF, QTimer, Qt, QUrl
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
    / "ComboBox"
    / "ComboBoxMulti.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "combo-box-multi-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    readonly property int expectedItemHeight: Enums.comboBoxMetrics.itemHeight

    width: 560
    height: 280
    visible: true

    ComboBoxMulti {
        id: combo
        objectName: "combo"
        x: 70
        y: 60
        width: 260
        model: ["Alpha", {"text": "Beta"}, "Gamma"]
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


def _object_descendants(root: QObject) -> list[QObject]:
    result = []
    pending = list(root.children())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.children())
    return result


def _visual_descendants(root: QQuickItem) -> list[QQuickItem]:
    result = []
    pending = list(root.childItems())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.childItems())
    return result


def _popup_core(combo: QQuickItem) -> QQuickItem:
    matches = [
        child
        for child in _object_descendants(combo)
        if isinstance(child, QQuickItem)
        and child.metaObject().className().startswith("PopupWindowCore")
        and child.metaObject().indexOfProperty("isClosing") >= 0
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _tokens(combo: QQuickItem) -> list[QQuickItem]:
    return [
        child
        for child in _visual_descendants(combo)
        if child.metaObject().className().startswith("MultiSelectToken")
        and child.metaObject().indexOfProperty("tokenIndex") >= 0
    ]


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
    ]


def _point_for(window: QQuickWindow, item: QQuickItem) -> QPoint:
    point = item.mapToItem(
        window.contentItem(), QPointF(item.width() / 2, item.height() / 2)
    )
    return QPoint(round(point.x()), round(point.y()))


def _popup_rows(popup_window: QQuickWindow, expected_height: int) -> list[QQuickItem]:
    rows = [
        item
        for item in _visual_descendants(popup_window.contentItem())
        if item.metaObject().indexOfProperty("selected") >= 0
        and item.height() == expected_height
        and item.metaObject().className().startswith("QQuickRectangle")
    ]
    return sorted(
        rows,
        key=lambda item: item.mapToItem(popup_window.contentItem(), 0, 0).y(),
    )


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
    combo = window.findChild(QQuickItem, "combo")
    assert combo is not None
    assert _wait_for(lambda: len(_tokens(combo)) == 1)
    return engine, component, window, combo, warnings


def _dispose_scene(engine, component, window, combo) -> None:
    if combo.property("isOpen"):
        combo.closePopup()
        _wait_for(lambda: not combo.property("isOpen"))
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump()


def test_combo_box_multi_popup_selection_and_token_removal(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, combo, warnings = _create_scene()
    try:
        changes = []
        combo.selectionChanged.connect(
            lambda indices, items: changes.append(
                (_variant(indices), _variant(items))
            )
        )
        popup = _popup_core(combo)
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            _point_for(window, combo),
        )
        assert _wait_for(lambda: popup.property("isOpen"))
        popup_windows = _new_visible_windows(windows_before, window)
        assert len(popup_windows) == 1
        popup_window = popup_windows[0]
        assert isinstance(popup_window, QQuickWindow)
        popup_window.requestActivate()
        assert _wait_for(popup_window.isActive)
        assert _wait_for(
            lambda: popup.property("_clipHeight") == popup.property("popupHeight")
        )
        rows = _popup_rows(popup_window, window.property("expectedItemHeight"))
        assert len(rows) == 3
        assert [row.property("selected") for row in rows] == [True, False, False]

        QTest.mouseClick(
            popup_window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            _point_for(popup_window, rows[1]),
        )
        assert _wait_for(
            lambda: _variant(combo.property("selectedIndices")) == [0, 1]
        )
        assert changes[-1][0] == [0, 1]
        assert changes[-1][1][0] == "Alpha"
        assert changes[-1][1][1]["text"] == "Beta"

        QTest.mouseClick(
            popup_window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            _point_for(popup_window, rows[0]),
        )
        assert _wait_for(lambda: _variant(combo.property("selectedIndices")) == [1])

        combo.closePopup()
        assert _wait_for(lambda: not combo.property("isOpen"))
        assert _wait_for(lambda: not popup.property("isClosing"))
        assert _wait_for(lambda: _new_visible_windows(windows_before, window) == [])
        tokens = _tokens(combo)
        assert len(tokens) == 1
        assert tokens[0].property("text") == "Beta"
        tokens[0].removeClicked.emit(0)
        _pump()
        assert _variant(combo.property("selectedIndices")) == []
        assert changes[-1][0] == []
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window, combo)
        assert _new_visible_windows(windows_before) == []


def test_combo_box_multi_source_conventions():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
