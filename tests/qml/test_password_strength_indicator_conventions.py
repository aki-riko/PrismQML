# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Password strength convention regressions. 密码强度组件规范回归。"""

from pathlib import Path, PurePosixPath

import pytest
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
    / "PasswordStrengthIndicator.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "password-strength-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property int expectedCaptionType: Enums.label.type_caption

    width: 320
    height: 80
    Component.onCompleted: Translator.setLanguage(Enums.lang.en)

    PasswordStrengthIndicator {
        id: indicator
        objectName: "indicator"
        width: 280
    }
}
"""
PASSWORD_CASES = (
    ("", 0, ""),
    ("abc", 0, "Very Weak"),
    ("abcdefgh1", 1, "Weak"),
    ("Abcdefgh1", 2, "Fair"),
    ("Abcdefgh1!", 3, "Strong"),
    ("Abcdefghijk1!", 4, "Very Strong"),
)


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


def _strength_label(indicator):
    matches = [
        child
        for child in indicator.childItems()
        if child.metaObject().indexOfProperty("type") >= 0
        and child.metaObject().indexOfProperty("text") >= 0
        and child.metaObject().indexOfProperty("color") >= 0
    ]
    assert len(matches) == 1, [
        item.metaObject().className() for item in indicator.childItems()
    ]
    return matches[0]


@pytest.fixture
def password_strength_scene(qapp):
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


def test_password_strength_dynamic_bindings(password_strength_scene):
    root = password_strength_scene
    indicator = root.findChild(QObject, "indicator")
    assert indicator is not None
    label = _strength_label(indicator)
    assert label.property("type") == root.property("expectedCaptionType")
    for password, expected_strength, expected_text in PASSWORD_CASES:
        indicator.setProperty("password", password)
        _pump()
        assert indicator.property("strength") == expected_strength
        assert label.property("text") == expected_text


def test_password_strength_source_uses_standard_member_order():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        item
        for item in violations
        if item.rule in {"QML008", "QML009"}
    ] == []
