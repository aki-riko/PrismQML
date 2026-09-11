# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Domain bucket 1/1 of the former test_combo_box_core_conventions.py."""
import pytest  # noqa: F401
from combo_box_core_conventions_shared import *
from combo_box_core_conventions_shared import (
    _pump,
    _wait_for,
    _variant,
    _object_descendants,
    _visual_descendants,
    _popup_core,
    _new_visible_windows,
    _point_for,
    _local_point,
    _move_pointer_away,
    _popup_rows,
    _send_wheel,
    _type_custom,
    _create_scene,
    _close_combo,
    _dispose_scene,
    _open_popup,
)

def test_combo_box_core_qt_style_item_methods_preserve_metadata(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    engine, component, window, combo, editable, warnings = scene
    try:
        assert combo.count() == 3
        assert combo.itemText(1) == "Beta"
        assert combo.findText("Beta") == 1
        assert combo.currentData() == 10
        assert combo.itemData(1) == 20
        assert combo.itemIcon(1) == "beta-icon"
        assert not combo.isItemEnabled(1)

        combo.setCurrentText("Gamma")
        assert combo.property("currentIndex") == 2
        assert combo.property("currentText") == "Gamma"
        combo.setItemText(2, "Gamma Renamed")
        assert combo.itemText(2) == "Gamma Renamed"
        assert combo.property("currentText") == "Gamma Renamed"
        combo.setProperty("currentIndex", 0)

        combo.addItem("Delta", 40)
        assert combo.count() == 4
        assert combo.itemData(3) == 40
        combo.setItemData(0, 11)
        combo.insertItem(1, "Inserted", 15)
        assert combo.itemText(1) == "Inserted"
        assert combo.itemData(0) == 11
        assert combo.itemData(1) == 15
        assert combo.itemData(2) == 20

        combo.setItemIcon(1, "inserted-icon")
        combo.setItemEnabled(1, False)
        assert combo.itemIcon(1) == "inserted-icon"
        assert not combo.isItemEnabled(1)
        combo.removeItem(0)
        assert combo.itemText(0) == "Inserted"
        assert combo.itemData(0) == 15
        assert combo.itemIcon(0) == "inserted-icon"
        assert not combo.isItemEnabled(0)

        combo.clear()
        combo.addItem("Fresh", None)
        assert combo.itemData(0) is None
        assert combo.itemIcon(0) == ""
        assert combo.isItemEnabled(0)
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window, combo, editable)
        assert _new_visible_windows(windows_before) == []

def test_combo_box_core_default_placeholder_follows_runtime_language(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    engine, component, window, combo, editable, warnings = scene
    translated = window.findChild(QQuickItem, "translatedCombo")
    custom = window.findChild(QQuickItem, "customPlaceholderCombo")
    assert translated is not None and custom is not None
    try:
        assert QMetaObject.invokeMethod(window, "useEnglish")
        assert _wait_for(lambda: translated.property("placeholderText") == "Select")
        assert custom.property("placeholderText") == "Choose a value"

        assert QMetaObject.invokeMethod(window, "useSimplifiedChinese")
        assert _wait_for(lambda: translated.property("placeholderText") == "请选择")
        assert custom.property("placeholderText") == "Choose a value"
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window, combo, editable)
        assert _new_visible_windows(windows_before) == []

def test_combo_box_core_hover_prewarms_hidden_popup_content(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    engine, component, window, combo, editable, warnings = scene
    try:
        popup = _popup_core(combo)
        descendants = _object_descendants(combo)
        assert not combo.property("_popupContentRequested")
        assert not any(
            "TextMetrics" in item.metaObject().className()
            for item in descendants
        )
        assert not any(
            item.metaObject().className().startswith("ComboBoxPopupContent")
            for item in descendants
        )

        hover_point = _local_point(
            window, combo, combo.width() - 12, combo.height() / 2
        )
        QTest.mouseMove(window, hover_point)

        assert _wait_for(lambda: combo.property("_popupContentRequested"))
        assert _wait_for(lambda: popup.property("_prewarmed"))
        descendants = _object_descendants(combo)
        assert any(
            "TextMetrics" in item.metaObject().className()
            for item in descendants
        )
        assert any(
            item.metaObject().className().startswith("ComboBoxPopupContent")
            for item in descendants
        )
        assert not combo.property("isOpen")
        assert not popup.property("isOpen")
        assert _new_visible_windows(windows_before, window) == []
        assert warnings == []
    finally:
        QTest.mouseMove(
            window, QPoint(round(window.width() - 12), round(window.height() - 12))
        )
        _pump()
        _dispose_scene(engine, component, window, combo, editable)
        assert _new_visible_windows(windows_before) == []

def test_combo_box_core_press_settles_queued_prewarm_before_click(qapp):
    """A press settles a queued prewarm so the released click can open warm.

    按下时就地结算排队中的预热，使抬起后的点击走暖路径，而不是在点击回调里
    新建原生表面。
    """
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    engine, component, window, combo, editable, warnings = scene
    try:
        popup = _popup_core(combo)
        click_point = _local_point(
            window, combo, combo.width() - 12, combo.height() / 2
        )
        # 只排队、不给 0ms 定时器机会，模拟「快速 hover→点击」
        assert QMetaObject.invokeMethod(popup, "prewarm")
        assert popup.property("_prewarmScheduled")
        assert not popup.property("_prewarmed")

        QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=click_point)

        assert popup.property("_prewarmed")
        assert not popup.property("_prewarmScheduled")
        # 按下只结算预热，不得顺手把弹层打开
        assert not combo.property("isOpen")
        assert not popup.property("isOpen")
        assert _new_visible_windows(windows_before, window) == []
        assert warnings == []

        # 真实点击仍必须能打开：结算预热不得破坏打开链路
        QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=click_point)
        _open_popup(window, combo, windows_before)
    finally:
        _move_pointer_away(window)
        _dispose_scene(engine, component, window, combo, editable)
        assert _new_visible_windows(windows_before) == []

def test_combo_box_core_immediate_click_after_prewarm_request_opens_warm(qapp):
    """A click that arrives right after a prewarm request still opens the popup.

    预热请求之后紧接着的点击必须照常打开弹层（暖路径），不得被结算流程吞掉。
    """
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    engine, component, window, combo, editable, warnings = scene
    try:
        popup = _popup_core(combo)
        click_point = _local_point(
            window, combo, combo.width() - 12, combo.height() / 2
        )
        assert QMetaObject.invokeMethod(popup, "prewarm")
        assert popup.property("_prewarmScheduled")
        assert not popup.property("_prewarmed")

        QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=click_point)

        assert _wait_for(lambda: combo.property("isOpen"))
        assert _wait_for(lambda: popup.property("isOpen"))
        assert popup.property("_prewarmed")
        assert not popup.property("_prewarmScheduled")
        assert len(_new_visible_windows(windows_before, window)) == 1
        assert warnings == []
    finally:
        _move_pointer_away(window)
        _dispose_scene(engine, component, window, combo, editable)
        assert _new_visible_windows(windows_before) == []

def test_combo_box_core_popup_honors_height_icon_disabled_and_signals(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    engine, component, window, combo, editable, warnings = scene
    activated = []
    text_activated = []
    index_changed = []
    text_changed = []
    wheel_scrolled = []
    combo.activated.connect(activated.append)
    combo.textActivated.connect(text_activated.append)
    combo.indexChanged.connect(index_changed.append)
    combo.textChanged.connect(text_changed.append)
    combo.wheelScrolled.connect(wheel_scrolled.append)
    try:
        popup = _popup_core(combo)
        hover_point = _local_point(
            window, combo, combo.width() - 12, combo.height() / 2
        )
        QTest.mouseMove(window, hover_point)
        assert _wait_for(lambda: popup.property("_prewarmed"))
        assert _new_visible_windows(windows_before, window) == []

        _send_wheel(window, hover_point, 120)
        assert wheel_scrolled == [120]
        popup, popup_window = _open_popup(window, combo, windows_before)
        expected_height = 3 * combo.property("popupItemHeight") + window.property(
            "expectedPopupPadding"
        )
        rows = _popup_rows(popup_window)
        assert len(rows) == 3
        assert [row.property("itemEnabled") for row in rows] == [True, False, True]
        assert [row.property("icon") for row in rows] == [
            "alpha-icon",
            "beta-icon",
            "gamma-icon",
        ]
        assert [row.height() for row in rows] == [40, 40, 40]
        assert popup.property("popupHeight") == expected_height

        QTest.mouseClick(popup_window, Qt.MouseButton.LeftButton, pos=_point_for(popup_window, rows[1]))
        _pump()
        assert combo.property("currentIndex") == 0
        assert combo.property("isOpen")

        QTest.mouseClick(popup_window, Qt.MouseButton.LeftButton, pos=_point_for(popup_window, rows[2]))
        assert _wait_for(lambda: not combo.property("isOpen"))
        assert combo.property("currentIndex") == 2
        assert combo.property("currentText") == "Gamma"
        assert activated == [2]
        assert text_activated == ["Gamma"]
        assert index_changed == [2]
        assert text_changed == ["Gamma"]
        assert warnings == []
        assert _wait_for(lambda: _new_visible_windows(windows_before, window) == [])
    finally:
        _dispose_scene(engine, component, window, combo, editable)
        assert _new_visible_windows(windows_before) == []

def test_combo_box_model_replacement_refreshes_current_text(qapp):
    """Replacing the whole model must refresh currentText even when the index stays.

    整表替换模型时，即使 currentIndex 没有变化，currentText 也必须跟着刷新；两层
    （ComboBoxCore 基类与 Fluent.ComboBox 入口）都要一致。
    """
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    engine, component, window, combo, editable, warnings = scene
    try:
        core = window.findChild(QQuickItem, "replacingCombo")
        entry = window.findChild(QQuickItem, "replacingEntryCombo")
        holder = window.findChild(QObject, "modelHolder")
        assert core is not None and entry is not None and holder is not None
        assert core.property("currentText") == "First"
        assert entry.property("currentText") == "First"

        def replace_only(values):
            # QML 声明的 JS 函数在元对象里统一是 QVariant 形参，类型必须写 QVariant
            assert QMetaObject.invokeMethod(
                window, "replaceModelOnly",
                Q_ARG("QVariant", holder), Q_ARG("QVariant", list(values)),
            )
            assert _variant(core.property("model")) == list(values)

        def replace_with_index(values, index):
            assert QMetaObject.invokeMethod(
                window, "replaceModelAndSetIndex",
                Q_ARG("QVariant", holder), Q_ARG("QVariant", core),
                Q_ARG("QVariant", entry), Q_ARG("QVariant", list(values)),
                Q_ARG("QVariant", index),
            )
            assert _variant(core.property("model")) == list(values)
            assert core.property("currentIndex") == index
            assert entry.property("currentIndex") == index

        def expect_text(values, index):
            assert _wait_for(
                lambda: core.property("currentText") == list(values)[index]
            ), (list(values), index, core.property("currentText"))
            assert _wait_for(
                lambda: entry.property("currentText") == list(values)[index]
            ), (list(values), index, entry.property("currentText"))

        # 1) 只替换模型，索引保持 0：文本必须换成新列表首项
        replace_only(["NewFirst", "NewSecond"])
        expect_text(["NewFirst", "NewSecond"], 0)
        # 2) 列表变短但索引仍在范围内
        replace_only(["OnlyOne"])
        expect_text(["OnlyOne"], 0)
        # 3) 同一拍内替换模型并把索引改到 1
        replace_with_index(["Third", "Fourth"], 1)
        expect_text(["Third", "Fourth"], 1)
        # 4) 同一拍内替换模型并把索引写回同一个值（不产生索引变更）
        replace_with_index(["Fifth", "Sixth"], 0)
        expect_text(["Fifth", "Sixth"], 0)

        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window, combo, editable)
        assert _new_visible_windows(windows_before) == []

def test_combo_box_core_edit_then_select_restores_model_text(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    engine, component, window, combo, editable, warnings = scene
    edited = []
    editable.textEdited.connect(edited.append)
    try:
        inputs = [
            item
            for item in _visual_descendants(editable)
            if item.metaObject().className().startswith("QQuickTextInput")
            and item.isVisible()
        ]
        assert len(inputs) == 1
        click_point = _local_point(window, editable, 40, editable.height() / 2)
        QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=click_point)
        QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
        _type_custom(window)
        assert _wait_for(lambda: editable.property("currentText") == "custom"), (
            editable.property("currentText"),
            inputs[0].property("text"),
            inputs[0].property("activeFocus"),
            edited,
        )
        assert editable.property("currentIndex") == -1
        assert edited[-1] == "custom"

        editable.setProperty("model", ["Alpha", "Beta", "Gamma", "Delta"])
        _pump()
        assert editable.property("currentText") == "custom"
        assert inputs[0].property("text") == "custom"

        popup, popup_window = _open_popup(window, editable, windows_before)
        rows = _popup_rows(popup_window)
        assert len(rows) == 4
        QTest.mouseClick(popup_window, Qt.MouseButton.LeftButton, pos=_point_for(popup_window, rows[1]))
        assert _wait_for(lambda: not editable.property("isOpen"))
        assert editable.property("currentIndex") == 1
        assert editable.property("currentText") == "Beta"

        editable.setProperty("currentIndex", 2)
        assert _wait_for(lambda: editable.property("currentText") == "Gamma")
        assert warnings == []
        assert _wait_for(lambda: _new_visible_windows(windows_before, window) == [])
    finally:
        _dispose_scene(engine, component, window, combo, editable)
        assert _new_visible_windows(windows_before) == []

def test_combo_box_core_public_editing_commands_preserve_model(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    clipboard = QGuiApplication.clipboard()
    previous_clipboard_text = clipboard.text()
    scene = _create_scene()
    engine, component, window, combo, editable, warnings = scene
    edited = []
    editable.textEdited.connect(edited.append)
    try:
        editable.setProperty("currentIndex", 1)
        assert _wait_for(lambda: editable.property("currentText") == "Beta")
        model_before = _variant(editable.property("model"))

        assert QMetaObject.invokeMethod(editable, "selectAll")
        assert editable.property("selectedText") == "Beta"
        assert QMetaObject.invokeMethod(editable, "copy")
        assert clipboard.text() == "Beta"
        assert QMetaObject.invokeMethod(editable, "clearEditText")
        assert _wait_for(lambda: editable.property("currentText") == "")
        assert editable.property("currentIndex") == -1
        assert _variant(editable.property("model")) == model_before
        assert edited == [""]
        assert QMetaObject.invokeMethod(editable, "clearEditText")
        assert edited == [""]

        clipboard.setText("custom")
        assert QMetaObject.invokeMethod(editable, "paste")
        assert _wait_for(lambda: editable.property("currentText") == "custom")
        assert edited == ["", "custom"]
        assert QMetaObject.invokeMethod(editable, "undo")
        assert _wait_for(lambda: editable.property("currentText") == "")
        assert edited == ["", "custom", ""]
        assert QMetaObject.invokeMethod(editable, "redo")
        assert _wait_for(lambda: editable.property("currentText") == "custom")
        assert edited == ["", "custom", "", "custom"]
        assert QMetaObject.invokeMethod(editable, "selectAll")
        assert QMetaObject.invokeMethod(editable, "cut")
        assert _wait_for(lambda: editable.property("currentText") == "")
        assert edited == ["", "custom", "", "custom", ""]
        assert QMetaObject.invokeMethod(editable, "cut")
        assert edited == ["", "custom", "", "custom", ""]
        assert warnings == []
        assert _wait_for(lambda: _new_visible_windows(windows_before, window) == [])
    finally:
        clipboard.setText(previous_clipboard_text)
        _dispose_scene(engine, component, window, combo, editable)
        assert _new_visible_windows(windows_before) == []

def test_combo_box_core_wide_popup_left_aligns_and_tracks_control(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    engine, component, window, combo, editable, warnings = scene
    try:
        combo.setProperty(
            "model",
            ["An intentionally wide combo box item that exceeds the control width"],
        )
        popup, popup_window = _open_popup(window, combo, windows_before)
        assert popup.property("popupWidth") > combo.width()
        target_global = window.mapToGlobal(combo.mapToScene(QPointF()).toPoint())
        assert popup_window.x() + window.property(
            "expectedPanelOffset"
        ) == pytest.approx(target_global.x())

        combo.setX(combo.x() + 32)
        tracked_global = window.mapToGlobal(combo.mapToScene(QPointF()).toPoint())
        assert _wait_for(
            lambda: popup_window.x() + window.property("expectedPanelOffset")
            == pytest.approx(tracked_global.x())
        )
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window, combo, editable)
        assert _new_visible_windows(windows_before) == []

def test_combo_box_core_source_conventions():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
