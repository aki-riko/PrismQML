# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Shared real-QML harness for button dropdown tests. 按钮菜单真实 QML 测试夹具。"""

from pathlib import Path

from PySide6.QtCore import (
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
from PySide6.QtGui import QGuiApplication, QWindow
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtTest import QTest

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "button-dropdown-prewarm.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property int featureDropdown: Enums.button.feature_dropdown
    readonly property int featureSplit: Enums.button.feature_split
    readonly property int featureNone: Enums.button.feature_none
    readonly property int featureProgress: Enums.button.feature_progress_bar
    readonly property int durationFast: Enums.duration.fast
    readonly property int popupPanelOffset: Enums.popupMetrics.panelOffset

    function replaceDropdownMenuItems() {
        dropdownButton.menuItems = [
            "An intentionally very long replacement label that must be remeasured",
            "Gamma"
        ]
    }

    width: 360
    height: 240

    Button {
        id: dropdownButton
        objectName: "dropdownButton"
        x: 20
        y: 20
        width: 240
        height: 40
        feature: Enums.button.feature_dropdown
        text: "Dropdown"
        menuItems: ["Alpha", "Beta"]
        toolTipText: "Dropdown tooltip"
        toolTipShowDelay: 80
    }

    Button {
        id: splitButton
        objectName: "splitButton"
        x: 20
        y: 90
        width: 240
        height: 40
        feature: Enums.button.feature_split
        text: "Split"
        menuItems: ["Alpha", "Beta"]
        toolTipText: "Split tooltip"
        toolTipShowDelay: 80
    }
}
"""


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump(10)
        elapsed += 10
    return predicate()


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
        _pump(20)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    return engine, component, root, warnings


def _descendants(root):
    result = []
    pending = list(root.children())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.children())
    return result


def _visual_descendants(root):
    result = []
    pending = list(root.childItems())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.childItems())
    return result


def _button(root, object_name):
    button = root.findChild(QQuickItem, object_name)
    assert button is not None
    return button


def _button_dropdown(button):
    matches = [
        child
        for child in _descendants(button)
        if child.metaObject().indexOfProperty("isMenuOpen") >= 0
        and child.metaObject().indexOfProperty("mainHovered") >= 0
        and child.metaObject().indexOfProperty("dropHovered") >= 0
    ]
    assert len(matches) == 1, [child.metaObject().className() for child in matches]
    return matches[0]


def _dropdown_popups(dropdown):
    return [
        child
        for child in _descendants(dropdown)
        if child.metaObject().indexOfProperty("_itemsHeight") >= 0
        and child.metaObject().indexOfProperty("_prewarmed") >= 0
    ]


def _dropdown_popup(dropdown):
    matches = _dropdown_popups(dropdown)
    assert len(matches) == 1, [child.metaObject().className() for child in matches]
    return matches[0]


def _popup_windows(popup):
    return [
        window
        for window in popup.findChildren(QWindow)
        if window.metaObject().className() != "QQuickPopupWindow"
    ]


def _popup_window(popup):
    windows = _popup_windows(popup)
    assert len(windows) == 1
    return windows[0]


def _popup_surface(popup):
    surface = popup.findChild(QQuickItem, "_popupSurface")
    assert surface is not None
    return surface


def _popup_content(popup):
    content = popup.findChild(QQuickItem, "_popupContent")
    assert content is not None
    return content


def _popup_is_visible(popup):
    return bool(popup.property("_surfaceVisible"))


def _popup_panel_global_position(popup, panel_offset):
    return _popup_surface(popup).mapToGlobal(QPointF(panel_offset, panel_offset))


def _click_popup_item(item):
    window = item.window()
    assert window is not None
    click_position = item.mapToScene(
        QPointF(item.width() / 2, item.height() / 2)
    ).toPoint()
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        click_position,
    )


def _tooltip(button):
    tooltip = button.findChild(QObject, "_toolTip")
    if tooltip is None:
        support = button.findChild(QObject, "_hoverArea")
        assert support is not None
        assert QMetaObject.invokeMethod(support, "_prewarm")
        assert _wait_for(lambda: button.findChild(QObject, "_toolTip") is not None)
        tooltip = button.findChild(QObject, "_toolTip")
    assert tooltip is not None
    return tooltip


def _point_for(button, split_arrow=False):
    x = button.x() + button.width() - 16 if split_arrow else button.x() + 40
    return QPoint(round(x), round(button.y() + button.height() / 2))


def _move_to(window, button, split_arrow=False):
    QTest.mouseMove(window, _point_for(button, split_arrow))
    _pump(10)


def _click(window, button, split_arrow=False):
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _point_for(button, split_arrow),
    )


def _invoke(obj, method):
    assert QMetaObject.invokeMethod(obj, method), method


def _new_visible_windows(windows_before, root_window):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and window is not root_window
        and not any(window is existing for existing in windows_before)
    ]


def _active_qt_popup_window(windows_before, root_window):
    windows = _new_visible_windows(windows_before, root_window)
    assert len(windows) == 1
    assert (
        windows[0].flags() & Qt.WindowType.WindowType_Mask
    ) == Qt.WindowType.Popup
    return windows[0]


def _qt_popup_windows(root_window):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window is not root_window
        and window.transientParent() is root_window
        and window.metaObject().className() == "QQuickPopupWindow"
    ]


def _reset_button_popups(root):
    for object_name in ("dropdownButton", "splitButton"):
        button = root.findChild(QQuickItem, object_name)
        if button is None:
            continue
        _invoke(button, "hideToolTip")
        dropdowns = [
            child
            for child in _descendants(button)
            if child.metaObject().indexOfProperty("isMenuOpen") >= 0
        ]
        for dropdown in dropdowns:
            for popup in _dropdown_popups(dropdown):
                _invoke(popup, "forceReset")


def _dispose_scene(engine, component, root, window):
    _reset_button_popups(root)
    root.setParentItem(None)
    window.hide()
    window.close()
    root.deleteLater()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump(20)
