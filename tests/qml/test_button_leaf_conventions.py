# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Button leaf convention regressions. 按钮叶组件规范回归。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
BUTTON_SOURCES = (
    ROOT / "prismqml" / "PrismQML" / "controls" / "buttons" / "CloseButton.qml",
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "buttons"
    / "InputActionButton.qml",
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "buttons"
    / "Button"
    / "ButtonProgress.qml",
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "button-leaf-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML
import "../../prismqml/PrismQML/controls/buttons" as Buttons
import "../../prismqml/PrismQML/controls/buttons/Button" as ButtonParts

Item {
    readonly property real closeWidth: closeButton.width
    readonly property real closeHeight: closeButton.height
    readonly property bool closeHovered: closeButton.hovered
    readonly property bool closePressed: closeButton.pressed
    readonly property real actionWidth: actionButton.preferredWidth
    readonly property real actionHeight: actionButton.preferredHeight
    readonly property int actionStyle: actionButton.style
    readonly property int actionShape: actionButton.shape
    readonly property int transparentStyle: Enums.button.style_transparent
    readonly property int defaultShape: Enums.button.shape_default
    readonly property real progressWidth: progressFeature.width
    readonly property real progressHeight: progressFeature.height
    readonly property int progressFeatureType: progressFeature.feature
    readonly property real progressValue: progressFeature.progress
    readonly property bool progressVisible: progressFeature.showProgress
    readonly property int expectedProgressFeature: Enums.button.feature_progress_bar

    width: 400
    height: 200

    Buttons.CloseButton {
        id: closeButton
    }

    Item {
        width: 100
        height: 40

        Buttons.InputActionButton {
            id: actionButton
        }
    }

    Item {
        width: 200
        height: 10

        ButtonParts.ButtonProgress {
            id: progressFeature
            feature: Enums.button.feature_progress_bar
            style: Enums.button.style_primary
            progress: 0.4
            showProgress: true
            parentRadius: Enums.radius.small
        }
    }
}
"""


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_scene():
    engine = QQmlApplicationEngine()
    qml_warnings = []
    engine.warnings.connect(
        lambda errors: qml_warnings.extend(error.toString() for error in errors)
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
    assert qml_warnings == []
    return engine, component, root


def _new_visible_windows(windows_before):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
    ]


@pytest.fixture
def button_leaf_scene(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root = _create_scene()
    try:
        yield root, windows_before
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_button_leaf_runtime_defaults_remain_stable(button_leaf_scene):
    root, windows_before = button_leaf_scene
    assert (root.property("closeWidth"), root.property("closeHeight")) == (28, 28)
    assert not root.property("closeHovered")
    assert not root.property("closePressed")
    assert (root.property("actionWidth"), root.property("actionHeight")) == (30, 30)
    assert root.property("actionStyle") == root.property("transparentStyle")
    assert root.property("actionShape") == root.property("defaultShape")
    assert (root.property("progressWidth"), root.property("progressHeight")) == (
        200,
        3,
    )
    assert root.property("progressFeatureType") == root.property(
        "expectedProgressFeature"
    )
    assert root.property("progressValue") == pytest.approx(0.4)
    assert root.property("progressVisible")
    assert _new_visible_windows(windows_before) == []


def test_button_leaf_sources_use_standard_sections():
    for source_path in BUTTON_SOURCES:
        source = source_path.read_text(encoding="utf-8")
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        violations = scan_source_text(source, path)
        assert [
            violation
            for violation in violations
            if violation.rule in {"QML008", "QML009"}
        ] == []
