# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Viewbox stretch and scaling contracts. Viewbox 拉伸与缩放合同。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QPointF,
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
    LAYOUT_DIR / "Viewbox.qml",
    LAYOUT_DIR / "_internal" / "ViewboxContent.qml",
]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "viewbox-scaling.qml")
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

    function growUniformFit() {
        uniformFit.width = 400
        uniformFit.height = 400
    }

    Viewbox {
        id: uniformFit
        objectName: "uniformFit"
        x: 10
        y: 10
        width: 200
        height: 100
        stretch: Image.PreserveAspectFit

        Rectangle { objectName: "uniformFitContent"; width: 100; height: 100 }
    }

    Viewbox {
        id: uniformCrop
        objectName: "uniformCrop"
        x: 220
        y: 10
        width: 200
        height: 100
        stretch: Image.PreserveAspectCrop

        Rectangle { objectName: "uniformCropContent"; width: 100; height: 100 }
    }

    Viewbox {
        id: fillBox
        objectName: "fillBox"
        x: 430
        y: 10
        width: 200
        height: 100
        stretch: Image.Stretch

        Rectangle { objectName: "fillContent"; width: 100; height: 100 }
    }

    Viewbox {
        id: padBox
        objectName: "padBox"
        x: 10
        y: 130
        width: 200
        height: 100
        stretch: Image.Pad

        Rectangle { objectName: "padContent"; width: 100; height: 100 }
    }

    Viewbox {
        id: naturalBox
        objectName: "naturalBox"
        x: 220
        y: 130

        Rectangle { objectName: "naturalContent"; width: 100; height: 50 }
    }

    Viewbox {
        id: clippedBox
        objectName: "clippedBox"
        x: 430
        y: 130
        width: 200
        height: 100
        stretch: Image.PreserveAspectCrop
        clipContent: true

        Rectangle { objectName: "clippedContent"; width: 100; height: 100 }
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
def viewbox_scene(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, warnings = _create_scene()
    try:
        yield window, warnings, windows_before
    finally:
        _dispose_scene(engine, component, window)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def _viewbox(window, name) -> QQuickItem:
    viewbox = window.findChild(QQuickItem, name)
    assert viewbox is not None
    return viewbox


def _rendered_rect(window, viewbox_name, content_name):
    viewbox = _viewbox(window, viewbox_name)
    content = window.findChild(QQuickItem, content_name)
    assert content is not None
    top_left = content.mapToItem(viewbox, QPointF(0, 0))
    bottom_right = content.mapToItem(
        viewbox, QPointF(content.width(), content.height())
    )
    return [
        top_left.x(), top_left.y(), bottom_right.x(), bottom_right.y()
    ]


def test_viewbox_sources_follow_conventions():
    for source_path in SOURCE_PATHS:
        source = source_path.read_text(encoding="utf-8")
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        assert scan_source_text(source, path) == []


def test_viewbox_keeps_the_visual_tree_in_internal():
    entry = SOURCE_PATHS[0].read_text(encoding="utf-8")
    content = SOURCE_PATHS[1].read_text(encoding="utf-8")
    assert len(entry.splitlines()) < 300
    assert "required property Item host" in content
    assert "required property Item host" not in entry
    for marker in ("Rectangle {", "MouseArea {"):
        assert marker not in entry


def test_viewbox_stretch_modes_resolve_axis_scales(viewbox_scene):
    window, warnings, windows_before = viewbox_scene
    uniform_fit = _viewbox(window, "uniformFit")
    uniform_crop = _viewbox(window, "uniformCrop")
    fill_box = _viewbox(window, "fillBox")
    pad_box = _viewbox(window, "padBox")

    assert (uniform_fit.property("naturalWidth"),
            uniform_fit.property("naturalHeight")) == pytest.approx((100, 100))
    assert uniform_fit.property("scaleX") == pytest.approx(1)
    assert uniform_fit.property("scaleY") == pytest.approx(1)

    assert uniform_crop.property("scaleX") == pytest.approx(2)
    assert uniform_crop.property("scaleY") == pytest.approx(2)

    assert fill_box.property("scaleX") == pytest.approx(2)
    assert fill_box.property("scaleY") == pytest.approx(1)

    assert pad_box.property("scaleX") == pytest.approx(1)
    assert pad_box.property("scaleY") == pytest.approx(1)

    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_viewbox_implicit_size_follows_content(viewbox_scene):
    window, warnings, windows_before = viewbox_scene
    natural = _viewbox(window, "naturalBox")
    assert natural.property("naturalWidth") == pytest.approx(100)
    assert natural.property("naturalHeight") == pytest.approx(50)
    assert natural.width() == pytest.approx(100)
    assert natural.height() == pytest.approx(50)
    assert natural.property("scaleX") == pytest.approx(1)
    assert natural.property("scaleY") == pytest.approx(1)
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_viewbox_renders_scaled_and_centered_content(viewbox_scene):
    window, warnings, windows_before = viewbox_scene
    assert _rendered_rect(
        window, "uniformFit", "uniformFitContent"
    ) == pytest.approx([50, 0, 150, 100])
    assert _rendered_rect(
        window, "uniformCrop", "uniformCropContent"
    ) == pytest.approx([0, -50, 200, 150])
    assert _rendered_rect(
        window, "fillBox", "fillContent"
    ) == pytest.approx([0, 0, 200, 100])
    assert _rendered_rect(
        window, "padBox", "padContent"
    ) == pytest.approx([50, 0, 150, 100])
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_viewbox_rescales_when_the_box_changes(viewbox_scene):
    window, warnings, windows_before = viewbox_scene
    assert QMetaObject.invokeMethod(window, "growUniformFit")
    assert _wait_for(
        lambda: _viewbox(window, "uniformFit").property("scaleX")
        == pytest.approx(4)
    )
    assert _viewbox(window, "uniformFit").property("scaleY") == pytest.approx(4)
    assert _rendered_rect(
        window, "uniformFit", "uniformFitContent"
    ) == pytest.approx([0, 0, 400, 400])
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_viewbox_clip_flag_reaches_the_surface(viewbox_scene):
    window, warnings, windows_before = viewbox_scene
    clipped_surface = _viewbox(window, "clippedBox").findChild(
        QQuickItem, "viewboxSurface"
    )
    plain_surface = _viewbox(window, "uniformFit").findChild(
        QQuickItem, "viewboxSurface"
    )
    assert clipped_surface is not None and plain_surface is not None
    assert clipped_surface.property("clip") is True
    assert plain_surface.property("clip") is False
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []
