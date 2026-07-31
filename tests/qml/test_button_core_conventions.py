# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""ButtonCore convention and parent-chain regressions. ButtonCore 规范与父链回归。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import QEventLoop, QObject, QPoint, QPointF, Qt, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
BUTTON_CORE_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "buttons"
    / "Button"
    / "ButtonCore.qml"
)
ENUMS_SOURCE = ROOT / "prismqml" / "PrismQML" / "Enums.qml"
BUTTON_STYLE_HELPER_SOURCE = BUTTON_CORE_SOURCE.with_name("ButtonStyleHelper.qml")
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "button-core-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    id: root

    property int featureUnderTest: Enums.button.feature_none

    readonly property int featureNone: Enums.button.feature_none
    readonly property int featureDropdown: Enums.button.feature_dropdown
    readonly property int featureSplit: Enums.button.feature_split
    readonly property int featureProgress: Enums.button.feature_progress_bar
    readonly property int alignCenter: Enums.button.align_center
    readonly property int alignLeft: Enums.button.align_left
    readonly property int contentLeftMargin: Enums.spacing.m
    readonly property int menuContentLeadingPadding: Enums.spacing.l
    readonly property int menuContentTrailingPadding: Enums.spacing.xs
    readonly property int menuPaddingTolerance: Enums.spacing.xxs
    readonly property int buttonMinWidth: Enums.controlSize.buttonMinWidth
    readonly property int buttonHeight: Enums.controlSize.buttonHeight
    readonly property int splitArrowWidth: Enums.controlSize.splitButtonArrowWidth
    readonly property int wideMenuPadding: Enums.spacing.xxxl
    readonly property real aliasBorderWidth: aliasButton.border.width
    readonly property color aliasBorderColor: aliasButton.border.color
    readonly property real expectedBorderWidth: Enums.border.thick
    readonly property color expectedBorderColor: Enums.accentColor
    readonly property color expectedLifecycleBackground: lifecycleButton.color
    readonly property color expectedLifecycleBorder: lifecycleButton.styleHelper.borderColor
    readonly property color expectedLifecycleText: lifecycleButton.getTextColor()

    width: 500
    height: 220

    Button {
        id: aliasButton
        objectName: "aliasButton"
        width: 160
        height: 40
        text: "Alias"
        border.width: Enums.border.thick
        border.color: Enums.accentColor
    }

    Button {
        id: customButton
        objectName: "customButton"
        y: 50
        width: 160
        height: 40
        text: "Ignored default content"

        Rectangle {
            id: customPayload
            objectName: "customPayload"
            width: 37
            height: 19
            color: Enums.transparent
        }
    }

    Button {
        id: lifecycleButton
        objectName: "lifecycleButton"
        y: 100
        width: 180
        height: 40
        style: Enums.button.style_primary
        text: "State"
        icon: Enums.icon.checkmark
        feature: root.featureUnderTest
        menuItems: ["Alpha", "Beta"]
        progress: 0.4
        showProgress: true
        toolTipText: ""
    }

    MenuBar {
        id: menuBar
        objectName: "menuBar"
        x: 220
        width: 200
        itemPadding: root.wideMenuPadding
        items: ["File"]
    }

    Button {
        id: pillDropdownButton
        objectName: "pillDropdownButton"
        x: 220
        y: 50
        width: contentWidth
        height: contentHeight
        shape: Enums.button.shape_pill
        feature: Enums.button.feature_dropdown
        text: "DropDown"
        menuItems: ["Alpha", "Beta"]
    }

    Button {
        id: pillSplitButton
        objectName: "pillSplitButton"
        x: 220
        y: 100
        width: contentWidth
        height: contentHeight
        shape: Enums.button.shape_pill
        feature: Enums.button.feature_split
        text: "Split"
        menuItems: ["Alpha", "Beta"]
    }

    Button {
        id: compactSplitButton
        objectName: "compactSplitButton"
        x: 350
        y: 100
        width: contentWidth
        height: contentHeight
        shape: Enums.button.shape_pill
        feature: Enums.button.feature_split
        text: "I"
        menuItems: ["Alpha", "Beta"]
    }

    Button {
        id: gradientButtonA
        objectName: "gradientButtonA"
        x: 0
        y: 160
        style: Enums.button.style_gradient
        text: "Gradient A"
    }

    Button {
        id: gradientButtonB
        objectName: "gradientButtonB"
        x: 180
        y: 160
        style: Enums.button.style_gradient
        text: "Gradient B"
    }
}
"""

CLICK_SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "button-core-double-click.qml")
)
CLICK_SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Window {
    id: root

    property int pressedCount: 0
    property int releasedCount: 0
    property int clickedCount: 0
    property int doubleClickedCount: 0

    width: 320
    height: 160
    visible: true

    Button {
        id: button
        objectName: "rapidClickButton"
        anchors.centerIn: parent
        width: 160
        height: 40
        text: "Rapid click"
        onButtonPressed: root.pressedCount += 1
        onReleased: root.releasedCount += 1
        onClicked: root.clickedCount += 1
        onDoubleClicked: root.doubleClickedCount += 1
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


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
    _pump(20)
    assert warnings == []
    return engine, component, root, warnings


def _create_click_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(CLICK_SCENE_SOURCE, CLICK_SCENE_URL)
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert isinstance(root, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    _pump(50)
    assert root.isVisible()
    assert root.isExposed()
    assert warnings == []
    return engine, component, root, warnings


def _new_visible_windows(windows_before):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
    ]


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


def _mapped_x(item, ancestor):
    return item.mapToItem(ancestor, QPointF()).x()


def _right_gap(left_item, right_item, ancestor):
    return _mapped_x(right_item, ancestor) - (
        _mapped_x(left_item, ancestor) + left_item.width()
    )


def _painted_right_gap(text_item, right_item, ancestor):
    painted_right = _mapped_x(text_item, ancestor) + text_item.property("paintedWidth")
    return _mapped_x(right_item, ancestor) - painted_right


def _matching(root, *properties):
    return [
        child
        for child in _descendants(root)
        if all(child.metaObject().indexOfProperty(name) >= 0 for name in properties)
    ]


def _unique(root, *properties):
    matches = _matching(root, *properties)
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _button(root, name):
    button = root.findChild(QObject, name)
    assert button is not None
    return button


def _active_gradient(button):
    gradients = []
    for child in _descendants(button):
        if not child.metaObject().className().startswith("QQuickRectangle"):
            continue
        if child.metaObject().indexOfProperty("gradient") < 0:
            continue
        candidate = child.property("gradient")
        if candidate.isQObject():
            gradients.append(candidate.toQObject())
    assert len(gradients) == 1
    return gradients[0]


def _content_modules(button):
    return _matching(button, "_ringBorderColor", "countdownRemaining")


def _dropdown_modules(button):
    return _matching(button, "isMenuOpen", "dropHovered", "parentStyle")


def _progress_modules(button):
    return _matching(button, "_progressColor", "showProgress", "progress")


def _set_feature(root, property_name):
    root.setProperty("featureUnderTest", root.property(property_name))
    _pump(50)


def _assert_dropdown_bindings(root, button, dropdown):
    assert dropdown.property("feature") == button.property("feature")
    assert dropdown.property("controlEnabled") == button.property("enabled")
    assert dropdown.property("loading") == button.property("loading")
    assert dropdown.property("parentRadius") == button.property("radius")
    assert dropdown.property("parentStyle") == button.property("style")
    assert dropdown.property("textColor") == root.property("expectedLifecycleText")
    assert dropdown.property("menuItems").toVariant() == button.property(
        "menuItems"
    ).toVariant()
    assert not dropdown.property("isMenuOpen")
    popup = _unique(dropdown, "_itemsHeight", "_needsScroll")
    assert not popup.property("isOpen")


def _assert_progress_bindings(button, progress):
    assert progress.property("feature") == button.property("feature")
    assert progress.property("progress") == pytest.approx(button.property("progress"))
    assert progress.property("showProgress") == button.property("showProgress")


def _assert_initial_colors(root, button):
    assert button.property("_animatedBgColor") == root.property(
        "expectedLifecycleBackground"
    )
    assert button.property("_targetBgColor") == root.property(
        "expectedLifecycleBackground"
    )
    assert button.property("_animatedBorderColor") == root.property(
        "expectedLifecycleBorder"
    )
    assert button.property("_targetBorderColor") == root.property(
        "expectedLifecycleBorder"
    )


@pytest.fixture
def button_core_scene(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, warnings = _create_scene()
    try:
        yield root, warnings, windows_before
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


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
    assert "property bool hasCustomContent: false" in source
    assert "function _syncCustomContentState()" in source
    assert "onChildrenChanged: control._syncCustomContentState()" in source
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
    enums_source = ENUMS_SOURCE.read_text(encoding="utf-8")

    assert gradient_a is gradient_b
    assert "property Gradient _gradientDef" not in button_source
    assert (
        "gradient: style === Enums.button.style_gradient "
        "? Enums._buttonGradientDef : null"
    ) in button_source
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
    assert "sourceComponent: ButtonNeoShadow" in source
    assert "Behavior on _neoPressShift" in source
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
        ("featureSplit", (1, 1, 0), "alignLeft"),
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
            _assert_dropdown_bindings(root, button, dropdown[0])
        if progress:
            _assert_progress_bindings(button, progress[0])
        assert warnings == []
        assert _new_visible_windows(windows_before) == []


def test_button_core_merges_mutually_exclusive_feature_shells():
    source = BUTTON_CORE_SOURCE.read_text(encoding="utf-8")
    assert "id: featureVisualLoader" in source
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


def test_dropdown_and_split_main_content_use_asymmetric_padding(button_core_scene):
    root, warnings, windows_before = button_core_scene
    expected_leading = root.property("menuContentLeadingPadding")
    expected_trailing = root.property("menuContentTrailingPadding")

    for object_name in ("pillDropdownButton", "pillSplitButton"):
        button = _button(root, object_name)
        content = _content_modules(button)
        dropdown = _dropdown_modules(button)
        chevrons = [
            child
            for child in _visual_descendants(button)
            if child.metaObject().indexOfProperty("animated") >= 0
            and child.metaObject().indexOfProperty("isOpen") >= 0
            and child.isVisible()
        ]
        assert len(content) == 1
        assert len(dropdown) == 1
        assert len(chevrons) == 1
        texts = _matching(content[0], "text", "font", "paintedWidth")
        assert len(texts) == 1
        assert _mapped_x(texts[0], button) == pytest.approx(expected_leading)

        if object_name == "pillDropdownButton":
            assert _painted_right_gap(texts[0], chevrons[0], button) == pytest.approx(
                expected_trailing
            )
        else:
            separators = _matching(dropdown[0], "lineLength", "lineColor", "isHorizontal")
            assert len(separators) == 1
            split_gap = _painted_right_gap(texts[0], separators[0], button)
            assert expected_trailing <= split_gap <= (
                expected_trailing + root.property("menuPaddingTolerance")
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
