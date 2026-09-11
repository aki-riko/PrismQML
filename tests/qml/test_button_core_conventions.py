# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Domain bucket 1/1 of the former test_button_core_conventions.py."""
import pytest  # noqa: F401
from button_core_conventions_shared import *
from button_core_conventions_shared import (
    _pump,
    _create_scene,
    _create_click_scene,
    _new_visible_windows,
    _descendants,
    _visual_descendants,
    _mapped_x,
    _right_gap,
    _painted_right_gap,
    _matching,
    _unique,
    _button,
    _active_gradient,
    _content_modules,
    _dropdown_modules,
    _progress_modules,
    _set_feature,
    _assert_dropdown_bindings,
    _assert_progress_bindings,
    _assert_initial_colors,
)

def test_button_core_border_alias_and_custom_content(button_core_scene):
    root, warnings, windows_before = button_core_scene
    alias_button = _button(root, "aliasButton")
    custom_button = _button(root, "customButton")
    payload = _button(root, "customPayload")
    assert root.property("aliasBorderWidth") == root.property("expectedBorderWidth")
    assert root.property("aliasBorderColor") == root.property("expectedBorderColor")
    assert not alias_button.property("hasCustomContent")
    assert custom_button.property("hasCustomContent")
    assert payload in _descendants(custom_button)
    assert payload.parentItem() is not custom_button
    assert len(_content_modules(alias_button)) == 1
    assert _content_modules(custom_button) == []
    assert warnings == []
    assert _new_visible_windows(windows_before) == []

def test_button_core_custom_content_state_is_not_a_live_children_binding():
    source = BUTTON_CORE_SOURCE.read_text(encoding="utf-8")
    content_source = BUTTON_CONTENT_LAYER_SOURCE.read_text(encoding="utf-8")
    assert "property bool hasCustomContent: false" in source
    assert "function _syncCustomContentState()" in source
    assert "onChildrenChanged: contentLayer.buttonControl._syncCustomContentState()" in content_source
    assert "Component.onCompleted: contentLayer.buttonControl._syncCustomContentState()" in content_source
    assert (
        "hasCustomContent: customContentContainer.children.length" not in source
    )

def test_button_core_schedules_menu_retry_without_per_instance_timer():
    source = BUTTON_CORE_SOURCE.read_text(encoding="utf-8")
    assert "property bool _menuPrewarmRetryScheduled: false" in source
    assert "Qt.callLater(control._runMenuPrewarmRetry)" in source
    assert "_menuPrewarmRetryTimer" not in source

def test_button_style_omits_unused_feature_bindings():
    button_source = BUTTON_CORE_SOURCE.read_text(encoding="utf-8")
    helper_source = BUTTON_STYLE_HELPER_SOURCE.read_text(encoding="utf-8")
    assert "readonly property int _spectralEdgeInset" not in button_source
    assert "required property int feature" not in helper_source

def test_button_core_reuses_widget_tooltip_show_timer():
    source = BUTTON_CORE_SOURCE.read_text(encoding="utf-8")
    assert "_startToolTipShowTimer()" in source
    assert "_stopToolTipShowTimer()" in source
    assert "_btnToolTipTimer" not in source

def test_button_core_initial_colors_and_handlers(button_core_scene):
    root, warnings, windows_before = button_core_scene
    button = _button(root, "lifecycleButton")
    _assert_initial_colors(root, button)
    button.setProperty("pseudoPressed", True)
    _pump(20)
    assert button.property("pressed")
    assert button.property("_animatedBgColor") == root.property(
        "expectedLifecycleBackground"
    )
    button.setProperty("pseudoPressed", False)
    button.setProperty("pseudoHovered", True)
    _pump(20)
    assert button.property("hovered")
    assert button.property("_targetBgColor") == root.property(
        "expectedLifecycleBackground"
    )
    button.setProperty("pseudoHovered", False)
    assert warnings == []
    assert _new_visible_windows(windows_before) == []

def test_gradient_buttons_share_theme_bound_resource(button_core_scene):
    root, warnings, windows_before = button_core_scene
    gradient_a = _active_gradient(_button(root, "gradientButtonA"))
    gradient_b = _active_gradient(_button(root, "gradientButtonB"))
    button_source = BUTTON_CORE_SOURCE.read_text(encoding="utf-8")
    surface_source = BUTTON_SURFACE_SOURCE.read_text(encoding="utf-8")
    enums_source = ENUMS_SOURCE.read_text(encoding="utf-8")

    assert gradient_a is gradient_b
    assert "property Gradient _gradientDef" not in button_source
    assert "gradient: surface.buttonControl.style === Enums.button.style_gradient" in surface_source
    assert "&& !Enums.isVintageTicket ? Enums._buttonGradientDef : null" in surface_source
    assert "? Enums._buttonGradientDef : null" in surface_source
    assert "readonly property Gradient _buttonGradientDef: Gradient" in enums_source
    assert "color: Qt.lighter(root.accentColor, _button.gradientLighten)" in enums_source
    assert "color: root.accentColor" in enums_source
    assert warnings == []
    assert _new_visible_windows(windows_before) == []

def test_button_core_defers_neo_press_transform(button_core_scene):
    root, warnings, windows_before = button_core_scene
    button = _button(root, "lifecycleButton")
    assert not any(
        child.metaObject().className().startswith("QQuickTranslate")
        for child in _descendants(button)
    )
    source = BUTTON_CORE_SOURCE.read_text(encoding="utf-8")
    surface_source = BUTTON_SURFACE_SOURCE.read_text(encoding="utf-8")
    assert "ButtonInternal.ButtonSurface {" in source
    assert "sourceComponent: ButtonNeoShadow" in surface_source
    assert "Behavior on _neoPressShift" not in source
    assert warnings == []
    assert _new_visible_windows(windows_before) == []

def test_button_core_double_click_preserves_both_click_activations(qapp):
    engine, component, window, warnings = _create_click_scene()
    try:
        button = _button(window, "rapidClickButton")
        center = button.mapToScene(
            QPointF(button.width() / 2, button.height() / 2)
        ).toPoint()
        QTest.mouseDClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(center.x(), center.y()),
        )
        _pump(20)

        assert (
            window.property("pressedCount"),
            window.property("releasedCount"),
            window.property("clickedCount"),
            window.property("doubleClickedCount"),
        ) == (2, 2, 2, 1)
        assert warnings == []
    finally:
        window.close()
        window.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)

def test_button_core_main_mouse_area_drives_hover_state(qapp):
    engine, component, window, warnings = _create_click_scene()
    try:
        button = _button(window, "rapidClickButton")
        center = button.mapToScene(
            QPointF(button.width() / 2, button.height() / 2)
        ).toPoint()

        QTest.mouseMove(window, QPoint(window.width() - 1, window.height() - 1))
        _pump(20)
        QTest.mouseMove(window, center)
        _pump(20)
        assert button.property("hovered")

        QTest.mouseMove(window, QPoint(window.width() - 2, 1))
        _pump(20)
        assert not button.property("hovered")
        assert warnings == []
    finally:
        window.close()
        window.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)

def test_button_core_feature_loader_lifecycle(button_core_scene):
    root, warnings, windows_before = button_core_scene
    button = _button(root, "lifecycleButton")
    scenarios = (
        ("featureNone", (1, 0, 0), "alignCenter"),
        ("featureDropdown", (1, 1, 0), "alignLeft"),
        ("featureSplit", (1, 1, 0), "alignCenter"),
        ("featureProgress", (1, 0, 1), "alignCenter"),
        ("featureNone", (1, 0, 0), "alignCenter"),
    )
    for feature_name, expected, alignment_name in scenarios:
        _set_feature(root, feature_name)
        content = _content_modules(button)
        dropdown = _dropdown_modules(button)
        progress = _progress_modules(button)
        assert (len(content), len(dropdown), len(progress)) == expected
        assert button.property("contentAlignment") == root.property(alignment_name)
        if alignment_name == "alignLeft":
            assert _mapped_x(content[0], button) == pytest.approx(
                root.property("menuContentLeadingPadding")
            )
        if dropdown:
            if feature_name == "featureDropdown":
                assert _matching(
                    dropdown[0], "_itemsHeight", "_needsScroll"
                ) == []
            _assert_dropdown_bindings(root, button, dropdown[0])
        if progress:
            _assert_progress_bindings(button, progress[0])
        assert warnings == []
        assert _new_visible_windows(windows_before) == []

def test_button_core_merges_mutually_exclusive_feature_shells():
    source = BUTTON_CORE_SOURCE.read_text(encoding="utf-8")
    assert "id: featureLoader" in source
    assert "id: dropdownFeature" not in source
    assert "id: progressFeatureLoader" not in source
    assert "id: toggleAnimLoader" not in source
    assert "active: true" not in source

def test_menu_bar_buttons_default_to_left_alignment(button_core_scene):
    root, warnings, windows_before = button_core_scene
    menu_bar = _button(root, "menuBar")
    menu_buttons = [
        child
        for child in _visual_descendants(menu_bar)
        if child.metaObject().indexOfProperty("contentAlignment") >= 0
    ]
    assert len(menu_buttons) == 1
    menu_button = menu_buttons[0]
    content = _content_modules(menu_button)
    assert len(content) == 1
    assert menu_button.property("text") == "File"
    assert menu_button.property("contentAlignment") == root.property("alignLeft")
    content_x = _mapped_x(content[0], menu_button)
    assert content_x == pytest.approx(root.property("contentLeftMargin"))
    assert menu_button.width() - content_x - content[0].width() > content_x
    assert warnings == []
    assert _new_visible_windows(windows_before) == []

def test_dropdown_uses_asymmetric_padding_and_split_main_content_is_centered(button_core_scene):
    root, warnings, windows_before = button_core_scene
    expected_leading = root.property("menuContentLeadingPadding")
    expected_trailing = root.property("menuContentTrailingPadding")

    dropdown_button = _button(root, "pillDropdownButton")
    dropdown_content = _content_modules(dropdown_button)
    dropdown_chevrons = [
        child
        for child in _visual_descendants(dropdown_button)
        if child.metaObject().indexOfProperty("animated") >= 0
        and child.metaObject().indexOfProperty("isOpen") >= 0
        and child.isVisible()
    ]
    assert len(dropdown_content) == 1
    assert len(dropdown_chevrons) == 1
    dropdown_texts = _matching(dropdown_content[0], "text", "font", "paintedWidth")
    assert len(dropdown_texts) == 1
    assert _mapped_x(dropdown_texts[0], dropdown_button) == pytest.approx(expected_leading)
    assert _painted_right_gap(dropdown_texts[0], dropdown_chevrons[0], dropdown_button) == pytest.approx(
        expected_trailing
    )

    split_button = _button(root, "pillSplitButton")
    split_content = _content_modules(split_button)
    split_dropdown = _dropdown_modules(split_button)
    assert len(split_content) == 1
    assert len(split_dropdown) == 1
    split_texts = _matching(split_content[0], "text", "font", "paintedWidth")
    assert len(split_texts) == 1
    separators = _matching(split_dropdown[0], "lineLength", "lineColor", "isHorizontal")
    assert len(separators) == 1
    split_left_gap = _mapped_x(split_texts[0], split_button)
    split_right_gap = _painted_right_gap(split_texts[0], separators[0], split_button)
    assert split_left_gap == pytest.approx(
        split_right_gap,
        abs=root.property("menuPaddingTolerance"),
    )

    compact_button = _button(root, "compactSplitButton")
    compact_content = _content_modules(compact_button)
    assert len(compact_content) == 1
    compact_texts = _matching(compact_content[0], "text", "font", "paintedWidth")
    assert len(compact_texts) == 1
    expected_width = max(
        root.property("buttonHeight"),
        compact_texts[0].property("paintedWidth")
        + expected_leading
        + expected_trailing
        + root.property("splitArrowWidth"),
    )
    assert compact_button.width() == pytest.approx(expected_width)
    assert compact_button.width() < root.property("buttonMinWidth")

    assert warnings == []
    assert _new_visible_windows(windows_before) == []

def test_button_core_source_conventions():
    source = BUTTON_CORE_SOURCE.read_text(encoding="utf-8")
    path = PurePosixPath(BUTTON_CORE_SOURCE.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
