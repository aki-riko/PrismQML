# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Editable ComboBox type-to-search contracts. 可编辑下拉框输入即搜索合同。

The editable input doubles as the search field: typing narrows the candidate list,
a match expands it, a non-matching free value keeps the full list, and every visible
row still reports its source model index. The filter belongs to the default candidate
row — a custom popupDelegate keeps the full list — and it survives the close animation.
可编辑输入框同时充当搜索框: 输入收窄候选, 命中即展开, 未命中的自由文本保持完整列表,
且每个可见行仍回报其源模型下标。过滤归默认候选行所有 —— 自定义 popupDelegate 保持完整
列表 —— 并且会活过关闭动画。
"""

from pathlib import Path

import pytest  # noqa: F401
import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types

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
    _visual_descendants,
    _wait_for,
)

ROOT = Path(__file__).resolve().parents[2]
# The scene is inline, so the URL only supplies a base for relative imports.
# 场景内联定义, 该 URL 只用于给相对 import 提供基准。
CUSTOM_DELEGATE_SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "combo-box-editable-search-custom-delegate.qml")
)
CUSTOM_DELEGATE_SCENE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 380
    height: 260
    visible: true
    color: Enums.backgroundColor

    ComboBoxCore {
        id: customDelegateCombo
        objectName: "customDelegateCombo"
        x: 20
        y: 20
        width: 200
        model: ["Alpha", "Beta", "Gamma"]
        editable: true

        // A user-supplied row delegate owns its own index mapping: it reports the view's
        // `index` straight through, so the candidate list must never be narrowed.
        popupDelegate: Component {
            Rectangle {
                objectName: "customCandidateRow"
                property int candidateIndex: index
                property string candidateText: modelData
                width: ListView.view ? ListView.view.width : 200
                height: 32
                color: Enums.transparent
                Label { anchors.centerIn: parent; text: modelData }
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        customDelegateCombo.currentIndex = index
                        customDelegateCombo.currentText = modelData
                        customDelegateCombo.closePopup()
                    }
                }
            }
        }
    }
}
"""


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


def _custom_rows(popup_window):
    """Candidate rows of the custom delegate scene. 自定义委托场景的候选行。"""
    rows = [
        item
        for item in _visual_descendants(popup_window.contentItem())
        if item.objectName() == "customCandidateRow"
    ]
    return sorted(
        rows, key=lambda item: item.mapToItem(popup_window.contentItem(), 0, 0).y()
    )


def _create_custom_delegate_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    engine.addImportPath(str(ROOT / "prismqml"))
    component = QQmlComponent(engine)
    component.setData(CUSTOM_DELEGATE_SCENE, CUSTOM_DELEGATE_SCENE_URL)
    assert _wait_for(lambda: component.status() != QQmlComponent.Status.Loading)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    assert _wait_for(window.isExposed)
    window.requestActivate()
    assert _wait_for(window.isActive)
    combo = window.findChild(QQuickItem, "customDelegateCombo")
    assert combo is not None
    return engine, component, window, combo, warnings


def _dispose_custom_delegate_scene(engine, component, window) -> None:
    window.close()
    for obj in (window, component, engine):
        if obj is not None and shiboken6.isValid(obj):
            obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump()


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


def test_combo_box_editable_keeps_the_filtered_view_while_closing(qapp):
    """关闭动画期间候选列表必须保持过滤视图, 展开态也不得掉一拍。

    Dropping the query as soon as `isOpen` turns false made the fading list jump back to
    the full model, and made `popupVisible` dip to false for one turn — which released the
    open-fill lock in the middle of the close animation.
    isOpen 一变 false 就丢弃查询, 会让收起中的列表跳回全量模型, 并让 popupVisible 掉一拍
    false, 从而在关闭动画中途解除展开底色的锁定。
    """
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    engine, component, window, combo, editable, warnings = scene
    try:
        popup, popup_window = _open_without_activating(window, editable, windows_before)
        _select_all(window)
        _type_text(window, "amm")
        assert _wait_for(lambda: len(_popup_rows(popup_window)) == 1)

        editable.closePopup()
        # The close call publishes `isClosing` synchronously. 关闭调用同步发布 isClosing。
        assert popup.property("isClosing") is True
        assert editable.property("popupVisible") is True

        samples = []
        while popup.property("isClosing"):
            samples.append(
                (
                    bool(editable.property("popupVisible")),
                    len(_popup_rows(popup_window)) if popup_window.isVisible() else 0,
                )
            )
            _pump(5)
        assert samples, "关闭动画没有产生任何采样"
        assert all(visible for visible, _rows in samples), samples
        assert all(rows == 1 for _visible, rows in samples), samples
        assert _wait_for(lambda: not editable.property("popupVisible"))
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window, combo, editable)
        assert _new_visible_windows(windows_before) == []


def test_combo_box_custom_delegate_keeps_every_candidate(qapp):
    """自定义候选行委托不做源下标映射, 因此候选列表不得被输入即搜索收窄。

    The row reports the view's own `index`, so a narrowed list hands the control a
    renumbered index — the only visible row of a three-item model reports 0 instead of 2.
    Filtering therefore stays limited to the default delegate.
    该行直接回报视图自身的 index, 收窄后的列表会把重新编号的下标交给控件 —— 三项模型中唯一
    的可见行会回报 0 而不是 2。因此过滤只对默认委托生效。
    """
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, combo, warnings = _create_custom_delegate_scene()
    try:
        popup, popup_window = _open_without_activating(window, combo, windows_before)
        assert len(_custom_rows(popup_window)) == 3

        _select_all(window)
        _type_text(window, "amm")
        assert combo.property("currentText") == "amm"

        rows = _custom_rows(popup_window)
        assert [row.property("candidateIndex") for row in rows] == [0, 1, 2]
        assert [row.property("candidateText") for row in rows] == [
            "Alpha",
            "Beta",
            "Gamma",
        ]

        QTest.mouseClick(
            popup_window,
            Qt.MouseButton.LeftButton,
            pos=_point_for(popup_window, rows[2]),
        )
        assert _wait_for(lambda: not combo.property("isOpen"))
        assert combo.property("currentIndex") == 2
        assert combo.property("currentText") == "Gamma"
        assert warnings == []
    finally:
        _dispose_custom_delegate_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []
