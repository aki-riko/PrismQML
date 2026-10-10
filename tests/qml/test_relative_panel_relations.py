# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""RelativePanel relation contracts. RelativePanel 关系式布局合同。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QTimer,
    QUrl,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
LAYOUT_DIR = (
    ROOT / "prismqml" / "PrismQML" / "controls" / "containers" / "Layout"
)
SOURCE_PATHS = [
    LAYOUT_DIR / "RelativePanel.qml",
    LAYOUT_DIR / "_internal" / "RelativePanelContent.qml",
    LAYOUT_DIR / "_internal" / "RelativePanelEngine.js",
]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "relative-panel-relations.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/controls/containers/Layout"

Window {
    id: root
    objectName: "window"
    width: 700
    height: 500
    visible: false

    property int layoutUpdates: 0
    property bool apiPassed: false

    function verifyApi() {
        apiPassed = panel.count() === 5
            && panel.itemAt(0) === header
            && panel.itemAt(1) === body
            && panel.indexOf(body) === 1
            && panel.indexOf(badge) === 4
            && panel.itemAt(-1) === null
            && panel.itemAt(9) === null
    }

    function stretchBody() { body.width = 150 }

    function retargetFooter() {
        panel.relations = [
            { item: header, alignLeftWithPanel: true, alignTopWithPanel: true },
            { item: body, below: header, alignLeftWith: header },
            { item: footer, below: body, alignRightWithPanel: true }
        ]
    }

    function forceRelayout() { panel.relayout() }

    RelativePanel {
        id: panel
        objectName: "relativePanel"
        x: 20
        y: 20
        width: 400
        height: 300

        onLayoutUpdated: root.layoutUpdates++

        Rectangle { id: header; objectName: "header"; width: 120; height: 30 }
        Rectangle { id: body; objectName: "body"; width: 80; height: 40 }
        Rectangle { id: footer; objectName: "footer"; width: 60; height: 20 }
        Rectangle { id: banner; objectName: "banner"; width: 10; height: 10 }
        Rectangle { id: badge; objectName: "badge"; width: 50; height: 50 }

        relations: [
            { item: header, alignLeftWithPanel: true,
              alignRightWithPanel: true, alignTopWithPanel: true },
            { item: body, below: header, alignLeftWith: header },
            { item: footer, rightOf: body, alignTopWith: body },
            { item: banner, alignLeftWithPanel: true,
              alignRightWithPanel: true, alignBottomWithPanel: true },
            { item: badge, alignHorizontalCenterWithPanel: true,
              alignVerticalCenterWithPanel: true }
        ]
    }

    RelativePanel {
        id: circularPanel
        objectName: "circularPanel"
        x: 20
        y: 340
        width: 200
        height: 100

        Rectangle { id: loopA; objectName: "loopA"; width: 40; height: 20 }
        Rectangle { id: loopB; objectName: "loopB"; width: 40; height: 20 }

        relations: [
            { item: loopA, below: loopB },
            { item: loopB, below: loopA }
        ]
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 900) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is accepted for accepted in allowed)
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
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow)
    assert _wait_for(lambda: window.property("layoutUpdates") > 0)
    _pump()
    return engine, component, window, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


@pytest.fixture
def panel_scene(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, warnings = _create_scene()
    try:
        yield window, warnings, windows_before
    finally:
        _dispose_scene(engine, component, window)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def _geometry(window, name):
    item = window.findChild(QQuickItem, name)
    assert item is not None
    return [item.x(), item.y(), item.width(), item.height()]


def test_relative_panel_sources_follow_conventions():
    for source_path in SOURCE_PATHS:
        source = source_path.read_text(encoding="utf-8")
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        assert scan_source_text(source, path) == []


def test_relative_panel_keeps_the_visual_tree_in_internal():
    entry = SOURCE_PATHS[0].read_text(encoding="utf-8")
    content = SOURCE_PATHS[1].read_text(encoding="utf-8")
    assert len(entry.splitlines()) < 300
    assert "required property Item host" in content
    assert "required property Item host" not in entry
    for marker in ("Rectangle {", "MouseArea {"):
        assert marker not in entry


def test_relative_panel_resolves_relations(panel_scene):
    window, warnings, windows_before = panel_scene
    panel = window.findChild(QQuickItem, "relativePanel")
    assert panel is not None

    assert _geometry(window, "header") == pytest.approx([0, 0, 400, 30])
    assert _geometry(window, "body") == pytest.approx([0, 30, 80, 40])
    assert _geometry(window, "footer") == pytest.approx([80, 30, 60, 20])
    assert _geometry(window, "banner") == pytest.approx([0, 290, 400, 10])
    assert _geometry(window, "badge") == pytest.approx([175, 125, 50, 50])
    assert panel.property("itemCount") == 5
    assert panel.property("unresolvedCount") == 0
    assert window.property("layoutUpdates") > 0
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_relative_panel_public_api(panel_scene):
    window, warnings, windows_before = panel_scene
    assert QMetaObject.invokeMethod(window, "verifyApi")
    assert window.property("apiPassed")
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_relative_panel_follows_child_natural_size_changes(panel_scene):
    window, warnings, windows_before = panel_scene
    assert _geometry(window, "footer") == pytest.approx([80, 30, 60, 20])
    assert QMetaObject.invokeMethod(window, "stretchBody")
    assert _wait_for(
        lambda: _geometry(window, "footer")[0] == pytest.approx(150)
    )
    assert _geometry(window, "body") == pytest.approx([0, 30, 150, 40])
    assert _geometry(window, "footer") == pytest.approx([150, 30, 60, 20])
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_relative_panel_reacts_to_relation_changes(panel_scene):
    window, warnings, windows_before = panel_scene
    assert QMetaObject.invokeMethod(window, "retargetFooter")
    assert _wait_for(
        lambda: _geometry(window, "footer") == pytest.approx([340, 70, 60, 20])
    )
    assert _geometry(window, "header") == pytest.approx([0, 0, 120, 30])
    assert _geometry(window, "body") == pytest.approx([0, 30, 80, 40])
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_relative_panel_reports_unresolvable_relations(panel_scene):
    window, warnings, windows_before = panel_scene
    circular = window.findChild(QQuickItem, "circularPanel")
    assert circular is not None
    assert circular.property("unresolvedCount") == 2
    assert _geometry(window, "loopA") == pytest.approx([0, 0, 40, 20])
    assert _geometry(window, "loopB") == pytest.approx([0, 0, 40, 20])
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []
