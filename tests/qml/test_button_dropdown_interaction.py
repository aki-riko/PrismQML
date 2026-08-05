# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Button dropdown interaction regressions. 按钮下拉菜单交互回归。"""

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

from _button_dropdown_prewarm_support import (
    _active_qt_popup_window,
    _button,
    _button_dropdown,
    _click,
    _click_popup_item,
    _create_scene,
    _dispose_scene,
    _dropdown_popup,
    _dropdown_popups,
    _invoke,
    _move_to,
    _new_visible_windows,
    _popup_content,
    _popup_is_visible,
    _popup_panel_global_position,
    _popup_windows,
    _pump,
    _tooltip,
    _visual_descendants,
    _wait_for,
)


@pytest.fixture
def dropdown_scene(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, warnings = _create_scene()
    window = QQuickWindow()
    window.setWidth(360)
    window.setHeight(240)
    root.setParentItem(window.contentItem())
    window.show()
    window.requestActivate()
    _pump(30)
    try:
        yield root, window, warnings, windows_before
    finally:
        _dispose_scene(engine, component, root, window)


@pytest.mark.parametrize(
    ("object_name", "split_arrow"),
    [("dropdownButton", False), ("splitButton", True)],
)
def test_cold_click_opens_left_aligned_dropdown(
    dropdown_scene, object_name, split_arrow
):
    root, window, warnings, windows_before = dropdown_scene
    button = _button(root, object_name)
    button.setWidth(120)
    button.setProperty(
        "menuItems",
        ["repositories/kiro-account-manager"],
    )
    dropdown = _button_dropdown(button)
    QTest.mouseMove(window, QPoint(340, 220))
    _pump(20)
    assert _dropdown_popups(dropdown) == []

    _click(window, button, split_arrow)
    assert _wait_for(lambda: len(_dropdown_popups(dropdown)) == 1)
    popup = _dropdown_popup(dropdown)
    assert _wait_for(lambda: popup.property("isOpen"))

    target_global = window.mapToGlobal(
        button.mapToScene(QPointF()).toPoint()
    )
    assert _popup_panel_global_position(
        popup, root.property("popupPanelOffset")
    ).x() == pytest.approx(target_global.x())
    assert popup.property("_prewarmed")
    assert not popup.property("_prewarmScheduled")
    assert _popup_is_visible(popup)
    assert not popup.property("useInWindowPopup")
    assert popup.property("useQtPopupWindow")
    _active_qt_popup_window(windows_before, window)
    assert _popup_windows(popup) == []
    assert warnings == []


def test_qt_popup_window_closes_on_outside_press(dropdown_scene):
    root, window, warnings, windows_before = dropdown_scene
    button = _button(root, "dropdownButton")
    dropdown = _button_dropdown(button)
    assert _dropdown_popups(dropdown) == []

    _click(window, button)
    popup = _dropdown_popup(dropdown)
    assert _wait_for(lambda: popup.property("isOpen"))

    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(340, 220),
    )

    assert _wait_for(lambda: not popup.property("isOpen"))
    assert not _popup_is_visible(popup)
    assert _new_visible_windows(windows_before, window) == []
    assert warnings == []


def test_qt_popup_window_closes_on_escape(dropdown_scene):
    root, window, warnings, windows_before = dropdown_scene
    button = _button(root, "dropdownButton")
    dropdown = _button_dropdown(button)
    assert _dropdown_popups(dropdown) == []

    _click(window, button)
    popup = _dropdown_popup(dropdown)
    assert _wait_for(lambda: popup.property("isOpen"))
    popup_window = _active_qt_popup_window(windows_before, window)

    QTest.keyClick(popup_window, Qt.Key.Key_Escape)

    assert _wait_for(lambda: not popup.property("isOpen"))
    assert not _popup_is_visible(popup)
    assert _new_visible_windows(windows_before, window) == []
    assert warnings == []


def test_qt_popup_window_item_click_emits_and_closes(dropdown_scene):
    root, window, warnings, windows_before = dropdown_scene
    button = _button(root, "dropdownButton")
    dropdown = _button_dropdown(button)
    received = []
    button.menuItemClicked.connect(
        lambda index, text: received.append((index, text))
    )

    _click(window, button)
    popup = _dropdown_popup(dropdown)
    assert _wait_for(lambda: popup.property("isOpen"))
    _pump(20)
    alpha = next(
        child
        for child in _visual_descendants(_popup_content(popup))
        if child.metaObject().indexOfProperty("isSeparator") >= 0
        and child.property("text") == "Alpha"
    )
    assert alpha.window() is _active_qt_popup_window(windows_before, window)
    _click_popup_item(alpha)

    assert received == [(0, "Alpha")]
    assert _wait_for(lambda: not popup.property("isOpen"))
    assert _wait_for(lambda: not _popup_is_visible(popup))
    assert _new_visible_windows(windows_before, window) == []
    assert warnings == []


def test_qt_popup_window_item_click_closes_before_sync_model_rebuild(
    dropdown_scene,
):
    root, window, warnings, windows_before = dropdown_scene
    button = _button(root, "dropdownButton")
    dropdown = _button_dropdown(button)
    button.menuItemClicked.connect(
        lambda _index, _text: _invoke(root, "replaceDropdownMenuItems")
    )

    _click(window, button)
    popup = _dropdown_popup(dropdown)
    assert _wait_for(lambda: popup.property("isOpen"))
    _pump(20)
    alpha = next(
        child
        for child in _visual_descendants(_popup_content(popup))
        if child.metaObject().indexOfProperty("isSeparator") >= 0
        and child.property("text") == "Alpha"
    )
    assert alpha.window() is _active_qt_popup_window(windows_before, window)
    _click_popup_item(alpha)

    assert _wait_for(lambda: not popup.property("isOpen"))
    assert _wait_for(lambda: not _popup_is_visible(popup))
    assert _new_visible_windows(windows_before, window) == []
    assert warnings == []


def test_qt_popup_window_object_items_select_and_close(
    dropdown_scene,
):
    root, window, warnings, windows_before = dropdown_scene
    button = _button(root, "dropdownButton")
    button.setProperty(
        "menuItems",
        [
            {"text": "Claude Code CLI", "id": "claude-code"},
            {"text": "Claude Desktop 官网版", "id": "claude-desktop"},
        ],
    )
    dropdown = _button_dropdown(button)
    received = []
    button.menuItemClicked.connect(
        lambda index, text: received.append((index, text))
    )

    _click(window, button)
    popup = _dropdown_popup(dropdown)
    assert _wait_for(lambda: popup.property("isOpen"))
    _pump(20)
    desktop_item = next(
        child
        for child in _visual_descendants(_popup_content(popup))
        if child.metaObject().indexOfProperty("isSeparator") >= 0
        and child.property("text") == "Claude Desktop 官网版"
    )
    assert desktop_item.window() is _active_qt_popup_window(
        windows_before, window
    )
    _click_popup_item(desktop_item)

    assert received == [(1, "Claude Desktop 官网版")]
    assert _wait_for(lambda: not popup.property("isOpen"))
    assert _wait_for(lambda: not _popup_is_visible(popup))
    assert _popup_windows(popup) == []
    assert _new_visible_windows(windows_before, window) == []
    assert warnings == []


@pytest.mark.parametrize(
    ("object_name", "split_arrow"),
    [("dropdownButton", False), ("splitButton", True)],
)
def test_open_menu_immediately_dismisses_visible_tooltip(
    dropdown_scene, object_name, split_arrow
):
    root, window, warnings, windows_before = dropdown_scene
    button = _button(root, object_name)
    dropdown = _button_dropdown(button)
    tooltip = _tooltip(button)
    _invoke(button, "showToolTip")
    assert _wait_for(lambda: tooltip.property("visible"))

    _click(window, button, split_arrow)

    popup = _dropdown_popup(dropdown)
    assert not tooltip.property("visible")
    assert _popup_is_visible(popup)
    _active_qt_popup_window(windows_before, window)
    assert warnings == []


def test_open_menu_interrupts_tooltip_exit_transition(dropdown_scene):
    root, window, warnings, windows_before = dropdown_scene
    button = _button(root, "dropdownButton")
    dropdown = _button_dropdown(button)
    tooltip = _tooltip(button)

    _invoke(button, "showToolTip")
    assert _wait_for(lambda: tooltip.property("visible"))
    _invoke(button, "hideToolTip")
    _pump(10)
    assert tooltip.property("visible")

    _invoke(dropdown, "openMenu")

    popup = _dropdown_popup(dropdown)
    assert not tooltip.property("visible")
    assert _popup_is_visible(popup)
    _active_qt_popup_window(windows_before, window)
    assert warnings == []


@pytest.mark.parametrize(
    ("object_name", "split_arrow"),
    [("dropdownButton", False), ("splitButton", True)],
)
def test_open_menu_cancels_pending_tooltip_show(
    dropdown_scene, object_name, split_arrow
):
    root, window, warnings, _windows_before = dropdown_scene
    button = _button(root, object_name)
    dropdown = _button_dropdown(button)
    tooltip = _tooltip(button)
    _move_to(window, button, split_arrow)
    assert _wait_for(lambda: len(_dropdown_popups(dropdown)) == 1)
    popup = _dropdown_popup(dropdown)

    _click(window, button, split_arrow)
    _pump(140)

    assert not tooltip.property("visible")
    assert popup.property("isOpen")
    assert _popup_is_visible(popup)
    assert warnings == []


def test_dropdown_split_loader_lifecycle_leaves_no_popup_window(
    dropdown_scene,
):
    root, window, warnings, windows_before = dropdown_scene
    button = _button(root, "dropdownButton")
    _move_to(window, button)
    dropdown = _button_dropdown(button)
    popup = _dropdown_popup(dropdown)
    assert _wait_for(lambda: popup.property("_prewarmed"))

    button.setProperty("feature", root.property("featureNone"))
    _pump(40)
    assert _new_visible_windows(windows_before, window) == []

    button.setProperty("feature", root.property("featureSplit"))
    _pump(40)
    dropdown = _button_dropdown(button)
    _move_to(window, button, True)
    assert _wait_for(lambda: len(_dropdown_popups(dropdown)) == 1)
    popup = _dropdown_popup(dropdown)
    assert _wait_for(lambda: popup.property("_prewarmed"))
    _click(window, button, True)
    assert _wait_for(lambda: popup.property("isOpen"))
    assert _popup_is_visible(popup)

    button.setProperty("feature", root.property("featureNone"))
    assert _wait_for(
        lambda: _new_visible_windows(windows_before, window) == []
    )
    assert warnings == []
