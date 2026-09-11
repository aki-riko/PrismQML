# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
from combo_box_core_conventions_scenes import (
    SCENE_SOURCE,
)

# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""ComboBoxCore public and interaction contracts. 下拉框核心公共与交互合同。"""

from pathlib import Path, PurePosixPath

import pytest

from PySide6.QtCore import (
    Q_ARG,
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QObject,
    QPoint,
    QPointF,
    QTimer,
    Qt,
    QUrl,
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
    / "inputs"
    / "ComboBox"
    / "ComboBoxCore.qml"
)

SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "combo-box-core-conventions.qml")
)

def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()

def _wait_for(predicate, timeout_ms: int = 1800) -> bool:
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
        item = pending.pop()
        result.append(item)
        pending.extend(item.children())
    return result

def _visual_descendants(root: QQuickItem) -> list[QQuickItem]:
    result = []
    pending = list(root.childItems())
    while pending:
        item = pending.pop()
        result.append(item)
        pending.extend(item.childItems())
    return result

def _popup_core(combo: QQuickItem) -> QQuickItem:
    matches = [
        item
        for item in _object_descendants(combo)
        if isinstance(item, QQuickItem)
        and item.metaObject().className().startswith("PopupWindowCore")
        and item.metaObject().indexOfProperty("isClosing") >= 0
    ]
    assert len(matches) == 1
    return matches[0]

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

def _local_point(window: QQuickWindow, item: QQuickItem, x: float, y: float):
    point = item.mapToItem(window.contentItem(), QPointF(x, y))
    return QPoint(round(point.x()), round(point.y()))

def _move_pointer_away(window: QQuickWindow) -> None:
    """Park the pointer off every control so the next scene starts unhovered.

    把指针移到控件之外，否则下一场沿用同一坐标时 containsMouse 不变化，
    悬停预热不会触发。
    """
    QTest.mouseMove(
        window, QPoint(round(window.width() - 12), round(window.height() - 12))
    )
    _pump()

def _popup_rows(popup_window: QQuickWindow) -> list[QQuickItem]:
    rows = [
        item
        for item in _visual_descendants(popup_window.contentItem())
        if item.metaObject().indexOfProperty("itemEnabled") >= 0
        and item.metaObject().indexOfProperty("selected") >= 0
        and item.metaObject().indexOfProperty("text") >= 0
    ]
    return sorted(
        rows,
        key=lambda item: item.mapToItem(popup_window.contentItem(), 0, 0).y(),
    )

def _send_wheel(window: QQuickWindow, point: QPoint, delta: int) -> None:
    event = QWheelEvent(
        QPointF(point),
        QPointF(window.mapToGlobal(point)),
        QPoint(),
        QPoint(0, delta),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    QCoreApplication.sendEvent(window, event)
    _pump()

def _type_custom(window: QQuickWindow) -> None:
    QTest.keyClick(window, Qt.Key.Key_C, Qt.KeyboardModifier.ShiftModifier)
    for key in (
        Qt.Key.Key_U,
        Qt.Key.Key_S,
        Qt.Key.Key_T,
        Qt.Key.Key_O,
        Qt.Key.Key_M,
    ):
        QTest.keyClick(window, key)

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
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    window.requestActivate()
    assert _wait_for(window.isActive)
    combo = window.findChild(QQuickItem, "combo")
    editable = window.findChild(QQuickItem, "editableCombo")
    assert combo is not None and editable is not None
    return engine, component, window, combo, editable, warnings

def _close_combo(combo: QQuickItem) -> None:
    popup = _popup_core(combo)
    if combo.property("isOpen"):
        combo.closePopup()
    _wait_for(lambda: not combo.property("isOpen"))
    _wait_for(lambda: not popup.property("isClosing"))

def _dispose_scene(engine, component, window, combo, editable) -> None:
    _close_combo(combo)
    _close_combo(editable)
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump()

def _open_popup(window, combo, windows_before):
    popup = _popup_core(combo)
    click_point = _local_point(window, combo, combo.width() - 12, combo.height() / 2)
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=click_point)
    assert _wait_for(lambda: combo.property("isOpen"))
    assert _wait_for(lambda: popup.property("isOpen"))
    assert _wait_for(
        lambda: popup.property("_clipHeight") == popup.property("popupHeight")
    )
    popup_windows = _new_visible_windows(windows_before, window)
    assert len(popup_windows) == 1
    popup_window = popup_windows[0]
    assert isinstance(popup_window, QQuickWindow)
    popup_window.requestActivate()
    assert _wait_for(popup_window.isActive)
    return popup, popup_window
