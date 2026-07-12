# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Multi-select token color convention regressions. 多选标签颜色规范回归。"""

from pathlib import Path, PurePosixPath

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import Skin, Theme, register_types, setSkin, setTheme
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "ComboBox"
    / "_internal"
    / "MultiSelectToken.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "multi-select-token-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property color expectedDefaultText: Enums.accentColor
    readonly property color expectedLightText: "#000000"
    readonly property color expectedDarkText: "#ffffff"

    width: 720
    height: 180

    ComboBoxMulti {
        objectName: "comboMulti"
        width: 220
        model: ["Combo token"]
        selectedIndices: [0]
    }

    ComboBoxMultiTree {
        objectName: "comboTree"
        x: 240
        width: 220
        model: [{"text": "Root", "children": [{"text": "Tree token"}]}]
        selectedPaths: [["Root", "Tree token"]]
    }

    LineEdit {
        objectName: "tagInput"
        y: 72
        width: 520
        inputType: Enums.input.type_tag
        tags: ["Light token", "Dark token"]
        tagColors: ({"Light token": "#f5f5f5", "Dark token": "#d13438"})
    }
}
"""
CONSTANTS_SOURCE = b"""
import QtQuick
import PrismQML

QtObject {
    readonly property color textOnLight: Enums.chipColors.textOnLight
    readonly property color textOnDark: Enums.chipColors.textOnDark
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create(engine: QQmlApplicationEngine, source: bytes, url: QUrl):
    component = QQmlComponent(engine)
    component.setData(source, url)
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    instance = component.create(engine.rootContext())
    assert instance is not None, [error.toString() for error in component.errors()]
    _pump()
    return component, instance


def _create_engine():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    return engine, warnings


def _new_visible_windows(windows_before):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
    ]


def _descendants(root):
    result = []
    assert isinstance(root, QQuickItem)
    pending = list(root.childItems())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.childItems())
    return result


def _tokens(root):
    return [
        child
        for child in _descendants(root)
        if child.metaObject().indexOfProperty("tokenIndex") >= 0
        and child.metaObject().indexOfProperty("bgColorOverride") >= 0
        and child.metaObject().indexOfProperty("_tintFg") >= 0
    ]


def _token_parts(token):
    descendants = _descendants(token)
    labels = [
        child
        for child in descendants
        if child.metaObject().indexOfProperty("type") >= 0
        and child.metaObject().indexOfProperty("color") >= 0
        and child.property("text") == token.property("text")
    ]
    close_buttons = [
        child
        for child in descendants
        if child.metaObject().indexOfProperty("normalIconColor") >= 0
        and child.metaObject().indexOfProperty("hoverIconColor") >= 0
    ]
    assert len(labels) == 1
    assert len(close_buttons) == 1
    return labels[0], close_buttons[0]


def _assert_token_foreground(token, expected: QColor) -> None:
    label, close_button = _token_parts(token)
    icons = [
        child
        for child in close_button.childItems()
        if child.metaObject().indexOfProperty("iconSize") >= 0
        and child.metaObject().indexOfProperty("color") >= 0
    ]
    assert len(icons) == 1
    assert token.property("_tintFg") == expected
    assert label.property("color") == expected
    assert close_button.property("normalIconColor") == expected
    assert close_button.property("hoverIconColor") == expected
    assert icons[0].property("color") == expected


def _assert_tinted_token(token, override: str, expected: QColor) -> None:
    assert token.property("_tinted")
    assert token.property("bgColorOverride") == override
    _assert_token_foreground(token, expected)


def _assert_default_parent(root, name: str) -> None:
    parent = root.findChild(QObject, name)
    assert parent is not None
    tokens = _tokens(parent)
    assert len(tokens) == 1
    assert not parent.property("isOpen")
    assert not tokens[0].property("_tinted")
    assert tokens[0].property("bgColorOverride") == ""
    _assert_token_foreground(tokens[0], root.property("expectedDefaultText"))


def test_multi_select_token_public_parent_chains(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, warnings = _create_engine()
    component = root = None
    try:
        component, root = _create(engine, SCENE_SOURCE, SCENE_URL)
        _assert_default_parent(root, "comboMulti")
        _assert_default_parent(root, "comboTree")
        tag_input = root.findChild(QObject, "tagInput")
        assert tag_input is not None
        tags = {token.property("text"): token for token in _tokens(tag_input)}
        assert set(tags) == {"Light token", "Dark token"}
        _assert_tinted_token(
            tags["Light token"], "#f5f5f5", root.property("expectedLightText")
        )
        _assert_tinted_token(
            tags["Dark token"], "#d13438", root.property("expectedDarkText")
        )
        assert warnings == []
        assert _new_visible_windows(windows_before) == []
    finally:
        if root is not None:
            root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_chip_text_tokens_stay_fixed_across_themes(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, warnings = _create_engine()
    component = instance = None
    try:
        component, instance = _create(engine, CONSTANTS_SOURCE, SCENE_URL)
        for skin in (Skin.FLUENT, Skin.NEOBRUTALISM):
            for theme in (Theme.LIGHT, Theme.DARK):
                setSkin(skin)
                setTheme(theme)
                _pump(1)
                assert instance.property("textOnLight") == QColor("black")
                assert instance.property("textOnDark") == QColor("white")
        assert warnings == []
        assert _new_visible_windows(windows_before) == []
    finally:
        setSkin(Skin.FLUENT)
        setTheme(Theme.LIGHT)
        if instance is not None:
            instance.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_multi_select_token_source_uses_chip_color_tokens():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [item for item in violations if item.rule == "QML010"] == []
    assert "Enums.chipColors.textOnLight" in source
    assert "Enums.chipColors.textOnDark" in source
    assert ".hslLightness > 0.6" in source
