# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Spin box button convention regressions. 微调框按钮规范回归。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SPIN_BOX_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "SpinBox"
    / "SpinBox.qml"
)
SOURCE_PATHS = (
    SPIN_BOX_PATH,
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "SpinBox"
    / "SpinBoxButton.qml",
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "SpinBox"
    / "MiniSpinButton.qml",
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "spin-box-button-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property int transparentStyle: Enums.button.style_transparent
    readonly property int microIconSize: Enums.iconSize.micro
    readonly property real smallRadius: Enums.radius.small
    readonly property real tinyRadius: Enums.radius.tiny
    readonly property real spacingXs: Enums.spacing.xs
    readonly property real miniButtonWidth: Enums.spacing.xl + Enums.spacing.xs
    readonly property string subtractIcon: Enums.icon.subtract
    readonly property string addIcon: Enums.icon.add
    readonly property string upIcon: Enums.icon.chevron_up
    readonly property string downIcon: Enums.icon.chevron_down

    width: 360
    height: 96

    SpinBox {
        id: normalSpin
        objectName: "normalSpin"
        width: 160
        height: 48
        value: 5
    }

    SpinBox {
        id: compactSpin
        objectName: "compactSpin"
        x: 200
        width: 96
        height: 28
        type: Enums.input.spinbox_compact
        value: 5
    }

    SpinBox { objectName: "typeNormal"; value: 1.25 }
    SpinBox {
        objectName: "typeDouble"
        type: Enums.input.spinbox_double
        value: 1.25
    }
    SpinBox {
        objectName: "typeCompact"
        type: Enums.input.spinbox_compact
        value: 1.25
    }
    SpinBox {
        objectName: "typeCompactDouble"
        type: Enums.input.spinbox_compact_double
        value: 1.25
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
    _pump()
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


def _button_with_icon(spin_box, icon):
    matches = [
        child
        for child in _descendants(spin_box)
        if child.metaObject().indexOfProperty("preferredHeight") >= 0
        and child.metaObject().indexOfProperty("style") >= 0
        and child.metaObject().indexOfProperty("icon") >= 0
        and child.property("icon") == icon
    ]
    assert len(matches) == 1, [
        child.metaObject().className() for child in matches
    ]
    return matches[0]


def _assert_normal_buttons(root, spin_box):
    buttons = [
        _button_with_icon(spin_box, root.property("subtractIcon")),
        _button_with_icon(spin_box, root.property("addIcon")),
    ]
    expected_size = spin_box.property("height") * 0.75
    for button in buttons:
        assert button.property("style") == root.property("transparentStyle")
        assert button.property("radius") == root.property("smallRadius")
        assert button.property("preferredHeight") == expected_size
        assert button.property("preferredWidth") == expected_size
        assert button.property("width") == expected_size
        assert button.property("height") == expected_size
        assert button.property("visible")


def _assert_compact_buttons(root, spin_box):
    buttons = [
        _button_with_icon(spin_box, root.property("upIcon")),
        _button_with_icon(spin_box, root.property("downIcon")),
    ]
    expected_width = root.property("miniButtonWidth")
    expected_height = (spin_box.property("height") - root.property("spacingXs")) / 2
    for button in buttons:
        assert button.property("style") == root.property("transparentStyle")
        assert button.property("iconSize") == root.property("microIconSize")
        assert button.property("radius") == root.property("tinyRadius")
        assert button.property("width") == expected_width
        assert button.property("height") == expected_height
        assert button.property("visible")


@pytest.fixture
def spin_box_scene(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, warnings = _create_scene()
    try:
        yield root
        assert warnings == []
        assert _new_visible_windows(windows_before) == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_spin_box_button_parent_bindings(spin_box_scene):
    root = spin_box_scene
    normal = root.findChild(QObject, "normalSpin")
    compact = root.findChild(QObject, "compactSpin")
    assert normal is not None
    assert compact is not None
    _assert_normal_buttons(root, normal)
    _assert_compact_buttons(root, compact)
    normal.setProperty("height", 56)
    compact.setProperty("height", 32)
    _pump()
    _assert_normal_buttons(root, normal)
    _assert_compact_buttons(root, compact)


def test_spin_box_type_runtime_contract(spin_box_scene):
    expected = {
        "typeNormal": (0, 1.0, False, 130, 32, "1"),
        "typeDouble": (2, 0.1, False, 130, 32, "1.25"),
        "typeCompact": (0, 1.0, True, 80, 28, "1"),
        "typeCompactDouble": (2, 0.1, True, 90, 28, "1.25"),
    }
    for name, contract in expected.items():
        spin_box = spin_box_scene.findChild(QObject, name)
        assert spin_box is not None
        actual = (
            spin_box.property("decimals"),
            spin_box.property("stepSize"),
            spin_box.property("compactMode"),
            spin_box.property("implicitWidth"),
            spin_box.property("implicitHeight"),
            spin_box.property("displayValue"),
        )
        assert actual == contract


def test_spin_box_uses_enum_tokens():
    source = SPIN_BOX_PATH.read_text(encoding="utf-8")
    assert "Enums.input.spinBoxIntegerDecimals" in source
    assert "Enums.input.spinBoxDoubleDecimals" in source
    assert "Enums.input.spinBoxIntegerStep" in source
    assert "Enums.input.spinBoxDoubleStep" in source
    assert "Enums.controlSize.spinBoxCompactDoubleExtraWidth" in source
    assert "Enums.controlSize.inputHeightCompact" in source


@pytest.mark.parametrize("source_path", SOURCE_PATHS, ids=lambda path: path.stem)
def test_spin_box_button_source_conventions(source_path):
    source = source_path.read_text(encoding="utf-8")
    path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        item
        for item in violations
        if item.rule in {"QML008", "QML009"}
    ] == []
