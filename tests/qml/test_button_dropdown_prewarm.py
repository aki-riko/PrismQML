# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Button dropdown prewarm and tooltip lifecycle regressions. 按钮菜单预热回归。"""

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
    _invoke,
    _move_to,
    _new_visible_windows,
    _point_for,
    _popup_content,
    _popup_is_visible,
    _popup_panel_global_position,
    _popup_surface,
    _popup_window,
    _pump,
    _qt_popup_windows,
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


def _use_qt_popup_window(popup):
    """Opt infrastructure checks into the explicit native mode. 基础设施用例显式启用原生模式。"""
    popup.setProperty("useInWindowPopup", False)
    popup.setProperty("useQtPopupWindow", True)
    assert not popup.property("useInWindowPopup")
    assert popup.property("useQtPopupWindow")


def test_dropdown_defaults_to_in_window_popup(dropdown_scene):
    """Simple menuItems must keep pointer input in the owning scene. 简单菜单必须在宿主场景内接收指针输入。"""
    root, window, warnings, windows_before = dropdown_scene
    button = _button(root, "dropdownButton")
    popup = _dropdown_popup(_button_dropdown(button))
    received = []
    button.menuItemClicked.connect(
        lambda index, text: received.append((index, text))
    )

    assert popup.property("useInWindowPopup")
    assert not popup.property("useQtPopupWindow")
    _click(window, button)
    assert _wait_for(lambda: popup.property("isOpen"))
    alpha = next(
        child
        for child in _visual_descendants(_popup_content(popup))
        if child.metaObject().indexOfProperty("isSeparator") >= 0
        and child.property("text") == "Alpha"
    )
    assert alpha.window() is window
    assert _new_visible_windows(windows_before, window) == []
    _pump(20)

    _click_popup_item(alpha)

    assert received == [(0, "Alpha")]
    assert _wait_for(lambda: not popup.property("isOpen"))
    assert warnings == []


@pytest.mark.parametrize(
    ("object_name", "split_arrow"),
    [("dropdownButton", False), ("splitButton", True)],
)
def test_dropdown_and_split_hover_prepare_hidden_menu_surface(
    dropdown_scene, object_name, split_arrow
):
    root, window, warnings, windows_before = dropdown_scene
    button = _button(root, object_name)
    popup = _dropdown_popup(_button_dropdown(button))
    assert not popup.property("_prewarmed")

    _move_to(window, button, split_arrow)

    assert _wait_for(lambda: popup.property("_prewarmed"))
    assert not popup.property("_prewarmScheduled")
    assert not popup.property("isOpen")
    assert not _popup_is_visible(popup)
    assert popup.property("useInWindowPopup")
    assert not popup.property("useQtPopupWindow")
    assert _qt_popup_windows(window) == []
    assert _popup_window(popup) not in _new_visible_windows(windows_before, window)
    assert warnings == []


def test_split_main_action_hover_does_not_prewarm_menu(dropdown_scene):
    root, window, warnings, windows_before = dropdown_scene
    button = _button(root, "splitButton")
    popup = _dropdown_popup(_button_dropdown(button))
    tooltip = _tooltip(button)

    _move_to(window, button)
    _pump(120)

    assert not popup.property("_prewarmed")
    assert not popup.property("_prewarmScheduled")
    assert not _popup_is_visible(popup)
    assert tooltip.property("visible")
    assert _popup_window(popup) not in _new_visible_windows(windows_before, window)
    assert warnings == []


def test_split_arrow_hover_drives_tooltip_state(dropdown_scene):
    root, window, warnings, _windows_before = dropdown_scene
    button = _button(root, "splitButton")
    dropdown = _button_dropdown(button)
    popup = _dropdown_popup(dropdown)
    popup.setProperty("_prewarmed", True)

    _move_to(window, button, True)

    assert dropdown.property("dropHovered")
    assert button.property("_toolTipHovered")
    assert warnings == []


def test_dropdown_snapshots_animation_duration(dropdown_scene):
    """Nested animations must not bind directly to a tearing-down singleton. 子动画不得直绑销毁中的单例。"""
    root, _window, warnings, _windows_before = dropdown_scene
    dropdown = _button_dropdown(_button(root, "splitButton"))

    assert dropdown.property("_animationDuration") == root.property("durationFast")
    assert warnings == []


@pytest.mark.parametrize("object_name", ["dropdownButton", "splitButton"])
def test_dropdown_and_split_focus_prewarm(dropdown_scene, object_name):
    root, _window, warnings, _windows_before = dropdown_scene
    button = _button(root, object_name)
    popup = _dropdown_popup(_button_dropdown(button))
    assert not popup.property("_prewarmed")

    button.forceActiveFocus()

    assert _wait_for(lambda: popup.property("_prewarmed"))
    assert button.hasActiveFocus()
    assert not _popup_is_visible(popup)
    assert warnings == []


@pytest.mark.parametrize("trigger", ["hover", "focus"])
def test_loader_prewarms_when_intent_precedes_dropdown_feature(
    dropdown_scene, trigger
):
    root, window, warnings, _windows_before = dropdown_scene
    button = _button(root, "dropdownButton")
    button.setProperty("feature", root.property("featureNone"))
    _pump(30)
    if trigger == "hover":
        _move_to(window, button)
        assert button.property("hovered")
    else:
        button.forceActiveFocus()
        assert button.hasActiveFocus()

    button.setProperty("feature", root.property("featureDropdown"))
    _pump(30)
    dropdown = _button_dropdown(button)
    popup = _dropdown_popup(dropdown)

    assert _wait_for(lambda: popup.property("_prewarmed"))
    assert dropdown.property("_geometryPrepared")
    assert not popup.property("_prewarmScheduled")
    assert warnings == []


@pytest.mark.parametrize("blocked_state", ["empty", "loading"])
def test_active_focus_retries_prewarm_when_menu_becomes_available(
    dropdown_scene, blocked_state
):
    root, _window, warnings, _windows_before = dropdown_scene
    button = _button(root, "dropdownButton")
    if blocked_state == "empty":
        button.setProperty("menuItems", [])
    else:
        button.setProperty("loading", True)
    popup = _dropdown_popup(_button_dropdown(button))
    button.forceActiveFocus()
    _pump(30)
    assert button.hasActiveFocus()
    assert not popup.property("_prewarmed")

    if blocked_state == "empty":
        button.setProperty("menuItems", ["Alpha"])
    else:
        button.setProperty("loading", False)
    assert button.hasActiveFocus()

    assert _wait_for(lambda: popup.property("_prewarmed"))
    assert warnings == []


@pytest.mark.parametrize("blocked_state", ["disabled", "loading", "empty"])
def test_unavailable_dropdown_does_not_prewarm(dropdown_scene, blocked_state):
    root, window, warnings, windows_before = dropdown_scene
    button = _button(root, "dropdownButton")
    button.setProperty("toolTipText", "")
    if blocked_state == "disabled":
        button.setEnabled(False)
    elif blocked_state == "loading":
        button.setProperty("loading", True)
    else:
        button.setProperty("menuItems", [])
    popup = _dropdown_popup(_button_dropdown(button))

    _move_to(window, button)
    _pump(120)

    assert not popup.property("_prewarmed")
    assert not popup.property("_prewarmScheduled")
    assert not _popup_is_visible(popup)
    assert _new_visible_windows(windows_before, window) == []
    assert warnings == []


@pytest.mark.parametrize("object_name", ["dropdownButton", "splitButton"])
def test_dropdown_prewarm_delegate_is_idempotent(dropdown_scene, object_name):
    root, _window, warnings, _windows_before = dropdown_scene
    button = _button(root, object_name)
    dropdown = _button_dropdown(button)
    popup = _dropdown_popup(dropdown)

    _invoke(dropdown, "prewarmMenu")
    _invoke(dropdown, "prewarmMenu")
    assert dropdown.property("_geometryPrewarmScheduled")
    assert popup.property("_prewarmed")
    assert not popup.property("_prewarmScheduled")
    assert _wait_for(lambda: popup.property("_prewarmed"))
    assert _wait_for(
        lambda: not dropdown.property("_geometryPrewarmScheduled")
    )
    assert dropdown.property("_geometryPrepared")
    assert not popup.property("_prewarmScheduled")
    assert popup.property("popupWidth") == pytest.approx(button.width())

    _invoke(dropdown, "prewarmMenu")

    assert not popup.property("_prewarmScheduled")
    assert not _popup_is_visible(popup)
    assert warnings == []


def test_destroying_loader_cancels_queued_geometry_prewarm_work(dropdown_scene):
    root, window, warnings, windows_before = dropdown_scene
    button = _button(root, "dropdownButton")
    dropdown = _button_dropdown(button)
    popup = _dropdown_popup(dropdown)

    _invoke(dropdown, "prewarmMenu")
    assert dropdown.property("_geometryPrewarmScheduled")
    assert popup.property("_prewarmed")
    assert not popup.property("_prewarmScheduled")

    button.setProperty("feature", root.property("featureNone"))
    _pump(200)

    assert _new_visible_windows(windows_before, window) == []
    assert warnings == []


@pytest.mark.parametrize("object_name", ["dropdownButton", "splitButton"])
def test_open_remeasures_and_tracks_left_aligned_wide_menu(
    dropdown_scene, object_name
):
    root, window, warnings, _windows_before = dropdown_scene
    button = _button(root, object_name)
    dropdown = _button_dropdown(button)
    popup = _dropdown_popup(dropdown)
    _invoke(dropdown, "prewarmMenu")
    assert _wait_for(lambda: dropdown.property("_geometryPrepared"))
    prepared_width = popup.property("popupWidth")

    button.setProperty(
        "menuItems",
        [
            "repositories/kiro-account-manager",
            "Gamma",
        ],
    )
    _pump(20)
    assert popup.property("popupWidth") == pytest.approx(prepared_width)

    _invoke(dropdown, "openMenu")
    _pump(20)
    menu_texts = [
        child.property("text")
        for child in _visual_descendants(_popup_content(popup))
        if child.metaObject().indexOfProperty("isSeparator") >= 0
        and child.metaObject().indexOfProperty("text") >= 0
    ]
    assert sorted(menu_texts) == [
        "Gamma",
        "repositories/kiro-account-manager",
    ]

    assert popup.property("popupWidth") > prepared_width
    target_global = window.mapToGlobal(
        button.mapToScene(QPointF()).toPoint()
    )
    panel_offset = root.property("popupPanelOffset")
    assert _popup_panel_global_position(popup, panel_offset).x() == pytest.approx(
        target_global.x()
    )

    button.setX(button.x() + 36)
    tracked_global = window.mapToGlobal(
        button.mapToScene(QPointF()).toPoint()
    )
    assert _wait_for(
        lambda: _popup_panel_global_position(popup, panel_offset).x()
        == pytest.approx(tracked_global.x())
    )

    _invoke(popup, "forceReset")
    _pump(20)
    _invoke(dropdown, "openMenu")
    _pump(20)
    reopened_global = window.mapToGlobal(
        button.mapToScene(QPointF()).toPoint()
    )
    assert _popup_panel_global_position(popup, panel_offset).x() == pytest.approx(
        reopened_global.x()
    )
    assert not dropdown.property("_geometryPrepared")
    assert warnings == []


def test_in_window_popup_clamps_wide_menu_inside_owner(dropdown_scene):
    """Popup.Item must trade overflow for reliable in-scene input. 页内弹层以边界夹紧换取可靠输入。"""
    root, window, warnings, windows_before = dropdown_scene
    button = _button(root, "dropdownButton")
    button.setWidth(120)
    button.setX(window.width() - button.width() - 12)
    button.setProperty(
        "menuItems",
        [
            "Soft — 保留暂存区+工作区",
            "Mixed — 保留工作区,清暂存区",
            "Hard — 丢弃所有改动",
        ],
    )
    dropdown = _button_dropdown(button)
    popup = _dropdown_popup(dropdown)

    _invoke(dropdown, "openMenu")
    assert _wait_for(lambda: popup.property("isOpen"))

    surface = _popup_surface(popup)
    surface_global = surface.mapToGlobal(QPointF())
    window_left = window.mapToGlobal(QPoint()).x()
    window_right = window.mapToGlobal(
        QPoint(round(window.width()), 0)
    ).x()
    assert surface_global.x() >= window_left
    assert surface_global.x() + surface.width() <= window_right
    assert _new_visible_windows(windows_before, window) == []
    assert warnings == []


def test_reset_menu_near_right_edge_extends_beyond_window(dropdown_scene):
    root, window, warnings, windows_before = dropdown_scene
    button = _button(root, "dropdownButton")
    button.setWidth(120)
    edge_gap = 12
    button.setX(window.width() - button.width() - edge_gap)
    button.setProperty("text", "Reset")
    button.setProperty(
        "menuItems",
        [
            "Soft — 保留暂存区+工作区",
            "Mixed — 保留工作区,清暂存区",
            "Hard — 丢弃所有改动",
        ],
    )
    dropdown = _button_dropdown(button)
    popup = _dropdown_popup(dropdown)
    _use_qt_popup_window(popup)

    target_global = window.mapToGlobal(button.mapToScene(QPointF()).toPoint())
    window_right = window.mapToGlobal(QPoint(round(window.width()), 0)).x()
    _invoke(dropdown, "openMenu")
    assert _wait_for(lambda: popup.property("isOpen"))

    surface = _popup_surface(popup)
    assert target_global.x() + surface.width() > window_right
    surface_global = surface.mapToGlobal(QPointF())
    assert surface_global.x() == pytest.approx(
        target_global.x() - root.property("popupPanelOffset")
    )
    assert surface_global.x() + surface.width() > window_right
    _active_qt_popup_window(windows_before, window)
    assert warnings == []


def test_reset_menu_tracking_preserves_cross_window_anchor(dropdown_scene):
    root, window, warnings, windows_before = dropdown_scene
    button = _button(root, "dropdownButton")
    button.setWidth(120)
    button.setProperty(
        "menuItems",
        [
            "Soft — 保留暂存区+工作区",
            "Mixed — 保留工作区,清暂存区",
            "Hard — 丢弃所有改动",
        ],
    )
    dropdown = _button_dropdown(button)
    popup = _dropdown_popup(dropdown)
    _use_qt_popup_window(popup)
    _invoke(dropdown, "openMenu")
    assert _wait_for(lambda: popup.property("isOpen"))

    surface = _popup_surface(popup)
    edge_gap = 12
    button.setX(window.width() - button.width() - edge_gap)
    target_global = window.mapToGlobal(button.mapToScene(QPointF()).toPoint())
    window_right = window.mapToGlobal(QPoint(round(window.width()), 0)).x()
    expected_surface_x = target_global.x() - root.property("popupPanelOffset")

    assert target_global.x() + surface.width() > window_right
    assert _wait_for(
        lambda: abs(surface.mapToGlobal(QPointF()).x() - expected_surface_x) < 0.5
    )
    surface_global = surface.mapToGlobal(QPointF())
    assert surface_global.x() + surface.width() > window_right
    _active_qt_popup_window(windows_before, window)
    assert warnings == []


def test_qt_popup_window_stays_inside_available_screen(dropdown_scene):
    root, window, warnings, windows_before = dropdown_scene
    button = _button(root, "dropdownButton")
    button.setWidth(120)
    button.setX(window.width() - button.width() - 12)
    button.setProperty(
        "menuItems",
        [
            "Soft — 保留暂存区+工作区",
            "Mixed — 保留工作区,清暂存区",
            "Hard — 丢弃所有改动",
        ],
    )
    available = window.screen().availableGeometry()
    window.setX(available.right() - window.width() + 1)
    _pump(20)
    popup = _dropdown_popup(_button_dropdown(button))
    _use_qt_popup_window(popup)

    _invoke(_button_dropdown(button), "openMenu")
    assert _wait_for(lambda: popup.property("isOpen"))

    popup_window = _active_qt_popup_window(windows_before, window)
    assert popup_window.geometry().right() <= available.right()
    assert popup_window.geometry().left() >= available.left()
    assert warnings == []


def test_tooltip_hide_animates_but_menu_dismiss_is_immediate(dropdown_scene):
    root, _window, warnings, _windows_before = dropdown_scene
    button = _button(root, "dropdownButton")
    tooltip = _tooltip(button)
    _invoke(button, "showToolTip")
    assert _wait_for(lambda: tooltip.property("visible"))

    _invoke(button, "hideToolTip")
    assert tooltip.property("visible")
    assert _wait_for(lambda: not tooltip.property("visible"))

    _invoke(button, "showToolTip")
    assert _wait_for(lambda: tooltip.property("visible"))
    _invoke(button, "_dismissToolTip")

    assert not tooltip.property("visible")
    assert warnings == []


def test_public_tooltip_hide_cancels_button_show_timer(dropdown_scene):
    root, window, warnings, _windows_before = dropdown_scene
    button = _button(root, "dropdownButton")
    popup = _dropdown_popup(_button_dropdown(button))
    tooltip = _tooltip(button)
    popup.setProperty("_prewarmed", True)

    _move_to(window, button)
    _pump(20)
    assert not tooltip.property("visible")

    _invoke(button, "hideToolTip")
    _pump(120)

    assert not tooltip.property("visible")
    assert warnings == []


def test_queued_qt_popup_prewarm_cannot_hide_immediate_dropdown_open(
    dropdown_scene,
):
    root, _window, warnings, _windows_before = dropdown_scene
    dropdown = _button_dropdown(_button(root, "dropdownButton"))
    popup = _dropdown_popup(dropdown)
    _use_qt_popup_window(popup)

    _invoke(dropdown, "prewarmMenu")
    assert popup.property("_prewarmScheduled")
    _invoke(dropdown, "openMenu")
    assert _popup_is_visible(popup)

    assert _wait_for(lambda: popup.property("isOpen"))
    assert popup.property("_prewarmed")
    assert not dropdown.property("_geometryPrewarmScheduled")
    assert not dropdown.property("_geometryPrepared")
    assert not popup.property("_prewarmScheduled")
    assert popup.property("isOpen")
    assert _popup_is_visible(popup)
    assert warnings == []


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
    popup = _dropdown_popup(_button_dropdown(button))
    QTest.mouseMove(window, QPoint(340, 220))
    _pump(20)
    assert not popup.property("_prewarmed")

    _click(window, button, split_arrow)
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
    assert popup.property("useInWindowPopup")
    assert not popup.property("useQtPopupWindow")
    assert not _popup_window(popup).isVisible()
    assert _new_visible_windows(windows_before, window) == []
    assert warnings == []


def test_in_window_popup_closes_on_outside_press(dropdown_scene):
    root, window, warnings, windows_before = dropdown_scene
    button = _button(root, "dropdownButton")
    popup = _dropdown_popup(_button_dropdown(button))

    _click(window, button)
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


def test_in_window_popup_closes_on_escape(dropdown_scene):
    root, window, warnings, windows_before = dropdown_scene
    button = _button(root, "dropdownButton")
    popup = _dropdown_popup(_button_dropdown(button))

    _click(window, button)
    assert _wait_for(lambda: popup.property("isOpen"))

    QTest.keyClick(window, Qt.Key.Key_Escape)

    assert _wait_for(lambda: not popup.property("isOpen"))
    assert not _popup_is_visible(popup)
    assert _new_visible_windows(windows_before, window) == []
    assert warnings == []


def test_in_window_popup_item_click_emits_and_closes(dropdown_scene):
    root, window, warnings, windows_before = dropdown_scene
    button = _button(root, "dropdownButton")
    popup = _dropdown_popup(_button_dropdown(button))
    received = []
    button.menuItemClicked.connect(
        lambda index, text: received.append((index, text))
    )

    _click(window, button)
    assert _wait_for(lambda: popup.property("isOpen"))
    _pump(20)
    alpha = next(
        child
        for child in _visual_descendants(_popup_content(popup))
        if child.metaObject().indexOfProperty("isSeparator") >= 0
        and child.property("text") == "Alpha"
    )
    assert alpha.window() is window
    assert _new_visible_windows(windows_before, window) == []
    _click_popup_item(alpha)

    assert received == [(0, "Alpha")]
    assert _wait_for(lambda: not popup.property("isOpen"))
    assert _wait_for(lambda: not _popup_is_visible(popup))
    assert _new_visible_windows(windows_before, window) == []
    assert warnings == []


def test_in_window_popup_item_click_closes_before_sync_model_rebuild(
    dropdown_scene,
):
    root, window, warnings, windows_before = dropdown_scene
    button = _button(root, "dropdownButton")
    popup = _dropdown_popup(_button_dropdown(button))
    button.menuItemClicked.connect(
        lambda _index, _text: _invoke(root, "replaceDropdownMenuItems")
    )

    _click(window, button)
    assert _wait_for(lambda: popup.property("isOpen"))
    _pump(20)
    alpha = next(
        child
        for child in _visual_descendants(_popup_content(popup))
        if child.metaObject().indexOfProperty("isSeparator") >= 0
        and child.property("text") == "Alpha"
    )
    assert alpha.window() is window
    assert _new_visible_windows(windows_before, window) == []
    _click_popup_item(alpha)

    assert _wait_for(lambda: not popup.property("isOpen"))
    assert _wait_for(lambda: not _popup_is_visible(popup))
    assert _new_visible_windows(windows_before, window) == []
    assert warnings == []


def test_in_window_popup_object_items_select_and_close(
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
    popup = _dropdown_popup(_button_dropdown(button))
    received = []
    button.menuItemClicked.connect(
        lambda index, text: received.append((index, text))
    )

    _click(window, button)
    assert _wait_for(lambda: popup.property("isOpen"))
    _pump(20)
    desktop_item = next(
        child
        for child in _visual_descendants(_popup_content(popup))
        if child.metaObject().indexOfProperty("isSeparator") >= 0
        and child.property("text") == "Claude Desktop 官网版"
    )
    assert desktop_item.window() is window
    assert _new_visible_windows(windows_before, window) == []
    _click_popup_item(desktop_item)

    assert received == [(1, "Claude Desktop 官网版")]
    assert _wait_for(lambda: not popup.property("isOpen"))
    assert _wait_for(lambda: not _popup_is_visible(popup))
    assert not _popup_window(popup).isVisible()
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
    popup = _dropdown_popup(_button_dropdown(button))
    tooltip = _tooltip(button)
    _invoke(button, "showToolTip")
    assert _wait_for(lambda: tooltip.property("visible"))

    _click(window, button, split_arrow)

    assert not tooltip.property("visible")
    assert _popup_is_visible(popup)
    assert _new_visible_windows(windows_before, window) == []
    assert warnings == []


def test_open_menu_interrupts_tooltip_exit_transition(dropdown_scene):
    root, _window, warnings, windows_before = dropdown_scene
    button = _button(root, "dropdownButton")
    dropdown = _button_dropdown(button)
    popup = _dropdown_popup(dropdown)
    tooltip = _tooltip(button)
    popup.setProperty("_prewarmed", True)

    _invoke(button, "showToolTip")
    assert _wait_for(lambda: tooltip.property("visible"))
    _invoke(button, "hideToolTip")
    _pump(10)
    assert tooltip.property("visible")

    _invoke(dropdown, "openMenu")

    assert not tooltip.property("visible")
    assert _popup_is_visible(popup)
    assert _new_visible_windows(windows_before, _window) == []
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
    popup = _dropdown_popup(_button_dropdown(button))
    tooltip = _tooltip(button)
    popup.setProperty("_prewarmed", True)
    _move_to(window, button, split_arrow)

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
    popup = _dropdown_popup(dropdown)
    _move_to(window, button, True)
    assert _wait_for(lambda: popup.property("_prewarmed"))
    _click(window, button, True)
    assert _wait_for(lambda: popup.property("isOpen"))
    assert _popup_is_visible(popup)

    button.setProperty("feature", root.property("featureNone"))
    assert _wait_for(
        lambda: _new_visible_windows(windows_before, window) == []
    )
    assert warnings == []
