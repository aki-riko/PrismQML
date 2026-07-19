# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Button dropdown prewarm and tooltip lifecycle regressions. 按钮菜单预热回归。"""

import pytest
from PySide6.QtCore import QPoint, QPointF
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

from _button_dropdown_prewarm_support import (
    _button,
    _button_dropdown,
    _click,
    _create_scene,
    _dispose_scene,
    _dropdown_popup,
    _invoke,
    _move_to,
    _new_visible_windows,
    _point_for,
    _popup_window,
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
def test_dropdown_and_split_hover_prewarm_hidden_menu_window(
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
    assert not _popup_window(popup).isVisible()
    assert _new_visible_windows(windows_before, window) == []
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
    assert not _popup_window(popup).isVisible()
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


@pytest.mark.parametrize("object_name", ["dropdownButton", "splitButton"])
def test_dropdown_and_split_focus_prewarm(dropdown_scene, object_name):
    root, _window, warnings, _windows_before = dropdown_scene
    button = _button(root, object_name)
    popup = _dropdown_popup(_button_dropdown(button))
    assert not popup.property("_prewarmed")

    button.forceActiveFocus()

    assert _wait_for(lambda: popup.property("_prewarmed"))
    assert button.hasActiveFocus()
    assert not _popup_window(popup).isVisible()
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
    assert not _popup_window(popup).isVisible()
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
    assert popup.property("_prewarmScheduled")
    assert _wait_for(lambda: popup.property("_prewarmed"))
    assert not dropdown.property("_geometryPrewarmScheduled")
    assert dropdown.property("_geometryPrepared")
    assert not popup.property("_prewarmScheduled")
    assert popup.property("popupWidth") == pytest.approx(button.width())

    _invoke(dropdown, "prewarmMenu")

    assert not popup.property("_prewarmScheduled")
    assert not _popup_window(popup).isVisible()
    assert warnings == []


def test_destroying_loader_cancels_queued_prewarm_work(dropdown_scene):
    root, window, warnings, windows_before = dropdown_scene
    button = _button(root, "dropdownButton")
    dropdown = _button_dropdown(button)
    popup = _dropdown_popup(dropdown)

    _invoke(dropdown, "prewarmMenu")
    assert dropdown.property("_geometryPrewarmScheduled")
    assert popup.property("_prewarmScheduled")

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
        for child in _visual_descendants(_popup_window(popup).contentItem())
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
    popup_window = _popup_window(popup)
    assert popup_window.x() + root.property("popupPanelOffset") == pytest.approx(
        target_global.x()
    )

    button.setX(button.x() + 36)
    tracked_global = window.mapToGlobal(
        button.mapToScene(QPointF()).toPoint()
    )
    assert _wait_for(
        lambda: popup_window.x() + root.property("popupPanelOffset")
        == pytest.approx(tracked_global.x())
    )

    _invoke(popup, "forceReset")
    _pump(20)
    _invoke(dropdown, "openMenu")
    _pump(20)
    reopened_global = window.mapToGlobal(
        button.mapToScene(QPointF()).toPoint()
    )
    assert popup_window.x() + root.property("popupPanelOffset") == pytest.approx(
        reopened_global.x()
    )
    assert not dropdown.property("_geometryPrepared")
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


def test_scheduled_prewarm_cannot_hide_immediate_dropdown_open(dropdown_scene):
    root, _window, warnings, _windows_before = dropdown_scene
    dropdown = _button_dropdown(_button(root, "dropdownButton"))
    popup = _dropdown_popup(dropdown)

    _invoke(dropdown, "prewarmMenu")
    assert popup.property("_prewarmScheduled")
    _invoke(dropdown, "openMenu")
    assert _popup_window(popup).isVisible()

    assert _wait_for(lambda: popup.property("isOpen"))
    assert popup.property("_prewarmed")
    assert not dropdown.property("_geometryPrewarmScheduled")
    assert not dropdown.property("_geometryPrepared")
    assert not popup.property("_prewarmScheduled")
    assert popup.property("isOpen")
    assert _popup_window(popup).isVisible()
    assert warnings == []


@pytest.mark.parametrize(
    ("object_name", "split_arrow"),
    [("dropdownButton", False), ("splitButton", True)],
)
def test_cold_click_opens_left_aligned_dropdown(
    dropdown_scene, object_name, split_arrow
):
    root, window, warnings, _windows_before = dropdown_scene
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
    assert _popup_window(popup).x() + root.property(
        "popupPanelOffset"
    ) == pytest.approx(target_global.x())
    assert popup.property("_prewarmed")
    assert not popup.property("_prewarmScheduled")
    assert _popup_window(popup).isVisible()
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
    assert _popup_window(popup).isVisible()
    assert _new_visible_windows(windows_before, window) == [_popup_window(popup)]
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
    assert _popup_window(popup).isVisible()
    assert _new_visible_windows(windows_before, _window) == [_popup_window(popup)]
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
    assert _popup_window(popup).isVisible()
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
    assert _popup_window(popup).isVisible()

    button.setProperty("feature", root.property("featureNone"))
    assert _wait_for(
        lambda: _new_visible_windows(windows_before, window) == []
    )
    assert warnings == []
