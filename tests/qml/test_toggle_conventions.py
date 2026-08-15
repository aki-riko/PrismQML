# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Toggle interaction contracts. Toggle 交互合同。"""

from pathlib import Path, PurePosixPath

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QPoint,
    QPointF,
    QTimer,
    Qt,
    QUrl,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
UNCHECKED = 0
PARTIAL = 1
CHECKED = 2
TOKEN_SOURCES = (
    ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "Toggle.qml",
    ROOT / "prismqml" / "PrismQML" / "controls" / "inputs" / "Toggle" / "Toggle.qml",
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "Toggle"
    / "ToggleCheckIndicator.qml",
    ROOT / "prismqml" / "PrismQML" / "controls" / "icons" / "CheckIcon.qml",
)
TOGGLE_CONTENT_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "Toggle"
    / "_internal"
    / "ToggleContent.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "toggle-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    readonly property int stateUnchecked: Enums.toggle.state_unchecked
    readonly property int statePartiallyChecked: Enums.toggle.state_partially_checked
    readonly property int stateChecked: Enums.toggle.state_checked

    width: 620
    height: 300
    visible: true

    CheckBox {
        id: tri
        objectName: "tri"
        x: 40
        y: 40
        text: "Tri-state"
        tristate: true
    }

    CheckBox {
        id: normal
        objectName: "normal"
        x: 40
        y: 110
        text: "Normal"
    }

    Item {
        x: 240
        y: 30
        width: 220
        height: 100

        RadioButton {
            id: radioOne
            objectName: "radioOne"
            text: "One"
            checked: true
        }

        RadioButton {
            id: radioTwo
            objectName: "radioTwo"
            y: 50
            text: "Two"
        }
    }

    ToggleSwitch {
        id: switchControl
        objectName: "switchControl"
        x: 240
        y: 170
        text: "Switch"
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1600) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _visual_descendants(root: QQuickItem) -> list[QQuickItem]:
    result = []
    pending = list(root.childItems())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.childItems())
    return result


def _switch_indicator(control: QQuickItem) -> QQuickItem:
    matches = [
        child
        for child in _visual_descendants(control)
        if child.metaObject().indexOfProperty("_trackColor") >= 0
        and child.metaObject().indexOfProperty("checkedColor") >= 0
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _point_for(window: QQuickWindow, item: QQuickItem) -> QPoint:
    point = item.mapToItem(
        window.contentItem(), QPointF(item.width() / 2, item.height() / 2)
    )
    return QPoint(round(point.x()), round(point.y()))


def _click(window: QQuickWindow, item: QQuickItem) -> None:
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _point_for(window, item),
    )
    _pump()


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
    ]


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
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    window.requestActivate()
    assert _wait_for(window.isActive)
    controls = {
        name: window.findChild(QQuickItem, name)
        for name in ("tri", "normal", "radioOne", "radioTwo", "switchControl")
    }
    assert all(controls.values())
    assert _wait_for(lambda: len(_visual_descendants(controls["tri"])) > 0)
    return engine, component, window, controls, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump()


def _assert_tristate_cycle(window, tri) -> None:
    toggled = []
    states = []
    tri.toggled.connect(toggled.append)
    tri.stateModified.connect(states.append)
    assert (tri.property("checkState"), tri.property("checked")) == (UNCHECKED, False)
    expected = (
        (PARTIAL, False, False),
        (CHECKED, True, True),
        (UNCHECKED, False, False),
    )
    for state, checked, toggled_value in expected:
        _click(window, tri)
        assert (tri.property("checkState"), tri.property("checked")) == (
            state,
            checked,
        )
        assert toggled[-1] is toggled_value
        assert states[-1] == state
    tri.setProperty("enabled", False)
    _click(window, tri)
    assert tri.property("checkState") == UNCHECKED


def _assert_public_state_values(window) -> None:
    assert window.property("stateUnchecked") == UNCHECKED
    assert window.property("statePartiallyChecked") == PARTIAL
    assert window.property("stateChecked") == CHECKED


def _assert_normal_and_radio(window, controls) -> None:
    normal = controls["normal"]
    normal.toggleChecked()
    assert (normal.property("checkState"), normal.property("checked")) == (
        CHECKED,
        True,
    )
    normal.toggleChecked()
    assert (normal.property("checkState"), normal.property("checked")) == (
        UNCHECKED,
        False,
    )
    _click(window, controls["radioTwo"])
    assert not controls["radioOne"].property("checked")
    assert controls["radioTwo"].property("checked")


def _assert_switch_click(window, switch_control) -> None:
    toggled = []
    checked_states = []
    switch_control.toggled.connect(toggled.append)
    switch_control.checkedStateChanged.connect(checked_states.append)
    _click(window, _switch_indicator(switch_control))
    assert switch_control.property("checked")
    assert toggled == [True]
    assert checked_states == [True]


def test_toggle_interaction_and_tristate_contracts(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_scene()
    try:
        _assert_public_state_values(window)
        _assert_tristate_cycle(window, controls["tri"])
        _assert_normal_and_radio(window, controls)
        _assert_switch_click(window, controls["switchControl"])
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_toggle_check_states_use_public_enum_tokens():
    sources = [path.read_text(encoding="utf-8") for path in TOKEN_SOURCES]
    enum_source, toggle_source, indicator_source, icon_source = sources
    assert "state_unchecked: 0" in enum_source
    assert "state_partially_checked: 1" in enum_source
    assert "state_checked: 2" in enum_source
    for source in (toggle_source, indicator_source, icon_source):
        assert "Enums.toggle.state_unchecked" in source
    assert "Enums.toggle.state_checked" in toggle_source
    assert "Enums.toggle.state_checked" in icon_source
    assert "Enums.toggle.state_partially_checked" in toggle_source
    assert "Enums.toggle.state_partially_checked" in icon_source
    assert "% 3" not in toggle_source
    assert "checkState === 2" not in toggle_source
    assert "checkState > 0" not in indicator_source


def test_toggle_source_conventions():
    for source_path in (TOKEN_SOURCES[1], TOGGLE_CONTENT_SOURCE):
        source = source_path.read_text(encoding="utf-8")
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        violations = scan_source_text(source, path)
        assert [
            violation
            for violation in violations
            if violation.rule in {"QML008", "QML009"}
        ] == []


def test_toggle_external_checked_and_check_state_resynchronize(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_scene()
    try:
        normal = controls["normal"]
        normal.toggleChecked()
        assert normal.property("checkState") == CHECKED
        normal.setProperty("checked", False)
        assert normal.property("checkState") == UNCHECKED

        tri = controls["tri"]
        _click(window, tri)
        assert tri.property("checkState") == PARTIAL
        tri.setProperty("checked", True)
        assert tri.property("checkState") == CHECKED
        tri.setProperty("checkState", PARTIAL)
        assert not tri.property("checked")
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []
