# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Toggle leaf convention regressions. Toggle 叶组件规范回归。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
TOGGLE_SOURCES = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "Toggle"
    / "ToggleDefaultContent.qml",
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "Toggle"
    / "ToggleSubtitleContent.qml",
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "toggle-leaf-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property int expectedDefaultType: Enums.toggle.type_default
    readonly property int expectedSubtitleType: Enums.toggle.type_subtitle
    readonly property int expectedCheckboxType: Enums.toggle.control_checkbox
    readonly property int expectedBodyType: Enums.label.type_body
    readonly property int expectedCaptionType: Enums.label.type_caption
    readonly property int expectedIconSize: Enums.iconSize.l
    readonly property real expectedSpacingS: Enums.spacing.s
    readonly property real expectedSpacingXxs: Enums.spacing.xxs

    width: 400
    height: 160

    Toggle {
        id: defaultToggle
        objectName: "defaultToggle"
        type: Enums.toggle.type_default
        controlType: Enums.toggle.control_checkbox
        text: "Default title"
        icon: Enums.icon.checkmark
        iconSize: Enums.iconSize.l
    }

    Toggle {
        id: subtitleToggle
        objectName: "subtitleToggle"
        y: 80
        type: Enums.toggle.type_subtitle
        controlType: Enums.toggle.control_checkbox
        text: "Subtitle title"
        subtitle: "Subtitle detail"
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


def _leaf(toggle, required_properties):
    matches = [
        child
        for child in _descendants(toggle)
        if all(
            child.metaObject().indexOfProperty(name) >= 0
            for name in required_properties
        )
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _direct_labels(content, expected_count):
    labels = [
        child
        for child in content.childItems()
        if child.metaObject().indexOfProperty("type") >= 0
        and child.metaObject().indexOfProperty("text") >= 0
        and child.metaObject().indexOfProperty("color") >= 0
        and child.metaObject().indexOfProperty("visible") >= 0
    ]
    assert len(labels) == expected_count, [
        item.metaObject().className() for item in content.childItems()
    ]
    return labels


def _direct_loader(content):
    matches = [
        child
        for child in content.childItems()
        if child.metaObject().indexOfProperty("active") >= 0
        and child.metaObject().indexOfProperty("sourceComponent") >= 0
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


@pytest.fixture
def toggle_scene(qapp):
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


def test_default_content_parent_chain(toggle_scene):
    root = toggle_scene
    toggle = root.findChild(QObject, "defaultToggle")
    assert toggle is not None
    content = _leaf(toggle, ("text", "icon", "iconSize", "textColor", "showIcon"))
    label = _direct_labels(content, 1)[0]
    loader = _direct_loader(content)
    assert toggle.property("type") == root.property("expectedDefaultType")
    assert toggle.property("controlType") == root.property("expectedCheckboxType")
    assert content.property("text") == "Default title"
    assert content.property("icon") == toggle.property("icon")
    assert content.property("iconSize") == root.property("expectedIconSize")
    assert content.property("textColor") == toggle.property("_textColor")
    assert content.property("showIcon")
    assert content.property("spacing") == root.property("expectedSpacingS")
    assert loader.property("active")
    assert label.property("type") == root.property("expectedBodyType")
    assert label.property("text") == content.property("text")


def test_default_content_dynamic_bindings(toggle_scene):
    root = toggle_scene
    toggle = root.findChild(QObject, "defaultToggle")
    content = _leaf(toggle, ("text", "icon", "iconSize", "textColor", "showIcon"))
    label = _direct_labels(content, 1)[0]
    loader = _direct_loader(content)
    toggle.setProperty("text", "Updated title")
    toggle.setProperty("icon", "")
    _pump()
    assert content.property("text") == "Updated title"
    assert content.property("icon") == ""
    assert content.property("spacing") == 0.0
    assert not loader.property("active")
    assert label.property("text") == "Updated title"


def test_subtitle_content_parent_chain(toggle_scene):
    root = toggle_scene
    toggle = root.findChild(QObject, "subtitleToggle")
    assert toggle is not None
    content = _leaf(toggle, ("text", "subtitle", "textColor"))
    labels = {item.property("type"): item for item in _direct_labels(content, 2)}
    assert toggle.property("type") == root.property("expectedSubtitleType")
    assert toggle.property("controlType") == root.property("expectedCheckboxType")
    assert content.property("text") == "Subtitle title"
    assert content.property("subtitle") == "Subtitle detail"
    assert content.property("textColor") == toggle.property("_textColor")
    assert content.property("spacing") == root.property("expectedSpacingXxs")
    assert labels[root.property("expectedBodyType")].property("text") == content.property("text")
    assert labels[root.property("expectedCaptionType")].property("text") == content.property("subtitle")


def test_subtitle_content_dynamic_bindings(toggle_scene):
    root = toggle_scene
    toggle = root.findChild(QObject, "subtitleToggle")
    content = _leaf(toggle, ("text", "subtitle", "textColor"))
    labels = {item.property("type"): item for item in _direct_labels(content, 2)}
    toggle.setProperty("text", "Updated subtitle title")
    toggle.setProperty("subtitle", "")
    _pump()
    assert content.property("text") == "Updated subtitle title"
    assert content.property("subtitle") == ""
    assert labels[root.property("expectedBodyType")].property("text") == content.property("text")
    assert not labels[root.property("expectedCaptionType")].property("visible")


def test_toggle_leaf_sources_use_standard_sections():
    for source_path in TOGGLE_SOURCES:
        source = source_path.read_text(encoding="utf-8")
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        violations = scan_source_text(source, path)
        assert [
            item
            for item in violations
            if item.rule in {"QML008", "QML009"}
        ] == []
