# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Default combo box convention regressions. 默认下拉框规范回归。"""

from pathlib import Path, PurePosixPath

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "ComboBox"
    / "ComboBoxDefault.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "combo-box-default-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property int defaultStyle: Enums.comboBox.style_default
    readonly property int primaryStyle: Enums.comboBox.style_primary
    readonly property int featureNone: Enums.comboBox.feature_none
    readonly property int featureEditable: Enums.comboBox.feature_editable

    width: 280
    height: 80

    ComboBox {
        id: combo
        objectName: "combo"
        width: 180
        model: ["Alpha", "Beta"]
        currentIndex: 0
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


def _default_combo(combo):
    matches = [
        child
        for child in _descendants(combo)
        if child.metaObject().indexOfProperty("editable") >= 0
        and child.metaObject().indexOfProperty("useDefaultContent") >= 0
        and child.metaObject().indexOfProperty("isOpen") >= 0
        and child.metaObject().indexOfProperty("currentIndex") >= 0
    ]
    assert len(matches) == 1, [
        child.metaObject().className() for child in matches
    ]
    return matches[0]


def _assert_initial_state(root, default_combo):
    assert default_combo.property("style") == root.property("defaultStyle")
    assert default_combo.property("feature") == root.property("featureNone")
    assert not default_combo.property("editable")
    assert not default_combo.property("isOpen")
    assert default_combo.property("currentIndex") == 0
    assert default_combo.property("currentText") == "Alpha"


def _assert_updated_state(root, default_combo):
    assert default_combo.property("style") == root.property("primaryStyle")
    assert default_combo.property("feature") == root.property("featureEditable")
    assert default_combo.property("editable")
    assert default_combo.property("currentIndex") == 1
    assert default_combo.property("currentText") == "Beta"
    assert not default_combo.property("enabled")
    assert not default_combo.property("isOpen")


def test_combo_box_default_parent_bindings(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, warnings = _create_scene()
    try:
        combo = root.findChild(QObject, "combo")
        assert combo is not None
        default_combo = _default_combo(combo)
        _assert_initial_state(root, default_combo)
        combo.setProperty("style", root.property("primaryStyle"))
        combo.setProperty("feature", root.property("featureEditable"))
        combo.setProperty("currentIndex", 1)
        combo.setProperty("enabled", False)
        _pump()
        _assert_updated_state(root, default_combo)
        assert warnings == []
        assert _new_visible_windows(windows_before) == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_combo_box_default_source_conventions():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        item
        for item in violations
        if item.rule in {"QML008", "QML009"}
    ] == []
