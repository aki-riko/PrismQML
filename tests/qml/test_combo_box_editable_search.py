# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Editable ComboBox type-to-search contracts. 可编辑下拉框输入即搜索合同。

The editable input doubles as the search field: typing narrows the candidate list,
a match expands it, a non-matching free value keeps the full list, and every visible
row still reports its source model index.
可编辑输入框同时充当搜索框: 输入收窄候选, 命中即展开, 未命中的自由文本保持完整列表,
且每个可见行仍回报其源模型下标。
"""

import pytest  # noqa: F401

from combo_box_core_conventions_shared import (
    Qt,
    QTest,
    QGuiApplication,
    _close_combo,
    _create_scene,
    _dispose_scene,
    _local_point,
    _new_visible_windows,
    _point_for,
    _popup_core,
    _popup_rows,
    _pump,
    _type_custom,
    _wait_for,
)


def _type_text(window, text: str) -> None:
    """Type printable ASCII into the focused editable input. 向已聚焦的可编辑输入框输入文本。"""
    for char in text:
        modifier = (
            Qt.KeyboardModifier.ShiftModifier
            if char.isupper()
            else Qt.KeyboardModifier.NoModifier
        )
        QTest.keyClick(window, getattr(Qt.Key, f"Key_{char.upper()}"), modifier)
    _pump()


def _select_all(window) -> None:
    """Select the current value so the next keystroke replaces it. 全选当前值, 下次按键即替换。"""
    QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    _pump()


def _open_without_activating(window, combo, windows_before):
    """Show the candidate surface the way the control itself does.

    The native surface is never activated, so the editable input keeps the keyboard
    and the surface's own focus-loss guard cannot dismiss the list.
    候选表面按控件自身方式显示且不激活, 因此输入框保住键盘, 表面自身的失焦守卫也不会收起列表。
    """
    popup = _popup_core(combo)
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        pos=_local_point(window, combo, combo.width() - 12, combo.height() / 2),
    )
    assert _wait_for(lambda: combo.property("isOpen"))
    assert _wait_for(lambda: popup.property("isOpen"))
    assert _wait_for(
        lambda: popup.property("_clipHeight") == popup.property("popupHeight")
    )
    popup_windows = _new_visible_windows(windows_before, window)
    assert len(popup_windows) == 1
    return popup, popup_windows[0]


def test_combo_box_editable_input_narrows_candidates_and_keeps_source_index(qapp):
    """输入即搜索: 过滤后选中项仍回报源模型下标。

    A narrowed candidate list must not renumber currentIndex or activated(): the single
    visible row is the third model item, so selecting it has to report index 2.
    候选被收窄后不得改变 currentIndex 与 activated(): 唯一的可见行是模型第三项,
    选中它必须回报下标 2。
    """
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    engine, component, window, combo, editable, warnings = scene
    try:
        popup, popup_window = _open_without_activating(window, editable, windows_before)
        assert len(_popup_rows(popup_window)) == 3

        _select_all(window)
        _type_text(window, "amm")
        assert _wait_for(lambda: len(_popup_rows(popup_window)) == 1)
        rows = _popup_rows(popup_window)
        assert rows[0].property("text") == "Gamma"

        QTest.mouseClick(
            popup_window,
            Qt.MouseButton.LeftButton,
            pos=_point_for(popup_window, rows[0]),
        )
        assert _wait_for(lambda: not editable.property("isOpen"))
        assert editable.property("currentIndex") == 2
        assert editable.property("currentText") == "Gamma"
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window, combo, editable)
        assert _new_visible_windows(windows_before) == []


def test_combo_box_editable_typing_a_match_expands_the_candidate_list(qapp):
    """输入命中候选时自动展开列表。"""
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    engine, component, window, combo, editable, warnings = scene
    try:
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            pos=_local_point(window, editable, 40, editable.height() / 2),
        )
        assert _wait_for(lambda: editable.property("focused"))
        assert editable.property("isOpen") is False

        _select_all(window)
        _type_text(window, "amm")
        assert _wait_for(lambda: editable.property("isOpen"))
        popup_windows = _new_visible_windows(windows_before, window)
        assert len(popup_windows) == 1
        assert _wait_for(lambda: len(_popup_rows(popup_windows[0])) == 1)
        assert _popup_rows(popup_windows[0])[0].property("text") == "Gamma"
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window, combo, editable)
        assert _new_visible_windows(windows_before) == []


def test_combo_box_editable_free_text_keeps_every_candidate(qapp):
    """未命中候选的自由文本不改变候选列表, 也不展开列表。"""
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    engine, component, window, combo, editable, warnings = scene
    try:
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            pos=_local_point(window, editable, 40, editable.height() / 2),
        )
        assert _wait_for(lambda: editable.property("focused"))
        _select_all(window)
        _type_custom(window)
        assert _wait_for(lambda: editable.property("currentText") == "custom")
        assert editable.property("isOpen") is False

        popup, popup_window = _open_without_activating(window, editable, windows_before)
        assert len(_popup_rows(popup_window)) == 3
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window, combo, editable)
        assert _new_visible_windows(windows_before) == []


def test_combo_box_editable_forgets_the_query_after_close(qapp):
    """列表收起后丢弃上一次查询, 重新展开显示全部候选。"""
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    engine, component, window, combo, editable, warnings = scene
    try:
        popup, popup_window = _open_without_activating(window, editable, windows_before)
        _select_all(window)
        _type_text(window, "amm")
        assert _wait_for(lambda: len(_popup_rows(popup_window)) == 1)

        _close_combo(editable)
        popup, popup_window = _open_without_activating(window, editable, windows_before)
        assert _wait_for(lambda: len(_popup_rows(popup_window)) == 3)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window, combo, editable)
        assert _new_visible_windows(windows_before) == []
