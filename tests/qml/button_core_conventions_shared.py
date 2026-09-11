# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
from button_core_conventions_scenes import (
    SCENE_SOURCE,
)

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

BUTTON_SURFACE_SOURCE = BUTTON_CORE_SOURCE.parent / "_internal" / "ButtonSurface.qml"

BUTTON_CONTENT_LAYER_SOURCE = (
    BUTTON_CORE_SOURCE.parent / "_internal" / "ButtonContentLayer.qml"
)

SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "button-core-conventions.qml")
)

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
    if not _matching(dropdown, "_itemsHeight", "_needsScroll"):
        dropdown._ensureInternalMenu()
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
