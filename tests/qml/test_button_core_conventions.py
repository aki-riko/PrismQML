# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""ButtonCore convention and parent-chain regressions. ButtonCore 规范与父链回归。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

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
    readonly property real aliasBorderWidth: aliasButton.border.width
    readonly property color aliasBorderColor: aliasButton.border.color
    readonly property real expectedBorderWidth: Enums.border.thick
    readonly property color expectedBorderColor: Enums.accentColor
    readonly property color expectedLifecycleBackground: lifecycleButton.color
    readonly property color expectedLifecycleBorder: lifecycleButton.styleHelper.borderColor
    readonly property color expectedLifecycleText: lifecycleButton.getTextColor()

    width: 500
    height: 180

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


def _content_modules(button):
    return _matching(button, "_ringBorderColor", "countdownRemaining")


def _dropdown_modules(button):
    return _matching(button, "isMenuOpen", "dropHovered", "parentStyle")


def _progress_modules(button):
    return _matching(button, "_progressColor", "showProgress", "parentRadius")


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
    popup = _unique(dropdown, "_contentHeight", "_needsScroll")
    assert not popup.property("isOpen")


def _assert_progress_bindings(button, progress):
    assert progress.property("feature") == button.property("feature")
    assert progress.property("progress") == pytest.approx(button.property("progress"))
    assert progress.property("showProgress") == button.property("showProgress")
    assert progress.property("parentRadius") == button.property("radius")


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
    assert custom_button.property("hasCustomContent")
    assert payload in _descendants(custom_button)
    assert payload.parentItem() is not custom_button
    assert len(_content_modules(alias_button)) == 1
    assert _content_modules(custom_button) == []
    assert warnings == []
    assert _new_visible_windows(windows_before) == []


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


def test_button_core_feature_loader_lifecycle(button_core_scene):
    root, warnings, windows_before = button_core_scene
    button = _button(root, "lifecycleButton")
    scenarios = (
        ("featureNone", (1, 0, 0)),
        ("featureDropdown", (1, 1, 0)),
        ("featureSplit", (1, 1, 0)),
        ("featureProgress", (1, 0, 1)),
        ("featureNone", (1, 0, 0)),
    )
    for feature_name, expected in scenarios:
        _set_feature(root, feature_name)
        content = _content_modules(button)
        dropdown = _dropdown_modules(button)
        progress = _progress_modules(button)
        assert (len(content), len(dropdown), len(progress)) == expected
        if dropdown:
            _assert_dropdown_bindings(root, button, dropdown[0])
        if progress:
            _assert_progress_bindings(button, progress[0])
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
