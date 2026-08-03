# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""ImageCropper runtime regressions. ImageCropper 运行时回归。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QObject,
    QPoint,
    QPointF,
    QRectF,
    QTimer,
    QUrl,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT / "prismqml" / "PrismQML" / "controls" / "inputs" / "ImageCropper.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "image-cropper-runtime.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    readonly property int dialogType: Enums.imageCropper.type_dialog
    readonly property int overlayType: Enums.imageCropper.type_overlay

    width: 800
    height: 600
    visible: true

    ImageCropper {
        objectName: "cropper"
        x: 40
        y: 40
        width: implicitWidth
        height: implicitHeight
        type: Enums.imageCropper.type_overlay
    }
}
"""
IMAGE_URL = QUrl(
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8A"
    "AQUBAScY42YAAAAASUVORK5CYII="
)


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1200) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump(10)
        elapsed += 10
    return predicate()


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
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    window.requestActivate()
    assert _wait_for(window.isActive)
    cropper = window.findChild(QQuickItem, "cropper")
    assert cropper is not None
    return engine, component, window, cropper, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump(20)


def _visual_descendants(root: QQuickItem) -> list[QQuickItem]:
    result = []
    pending = [root]
    while pending:
        item = pending.pop()
        result.append(item)
        pending.extend(item.childItems())
    return result


def _object_descendants(root: QObject) -> list[QObject]:
    result = []
    pending = list(root.children())
    while pending:
        item = pending.pop()
        result.append(item)
        pending.extend(item.children())
    return result


def _preview(cropper: QQuickItem) -> QQuickItem:
    matches = [
        item
        for item in cropper.childItems()
        if item.metaObject().className().startswith("QQuickRectangle")
        and item.width() == pytest.approx(cropper.width())
        and item.height() == pytest.approx(cropper.height())
    ]
    assert len(matches) == 1
    return matches[0]


def _overlay(cropper: QQuickItem) -> QQuickItem:
    matches = [
        item
        for item in _visual_descendants(cropper)
        if item.metaObject().className().startswith("DialogBoxCore")
    ]
    assert len(matches) == 1
    return matches[0]


def _new_visible_windows(windows_before, root_window):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and window is not root_window
        and not any(window is existing for existing in windows_before)
    ]


def test_image_cropper_preserves_preview_geometry_and_source_state(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, cropper, warnings = _create_scene()
    try:
        preview = _preview(cropper)
        preview_items = preview.childItems()
        images = [
            item
            for item in preview_items
            if item.metaObject().className().startswith("QQuickImage")
        ]
        columns = [
            item
            for item in preview_items
            if item.metaObject().className().startswith("QQuickColumn")
        ]
        assert len(images) == 1
        assert len(columns) == 1
        assert (cropper.width(), cropper.height()) == pytest.approx((120, 80))
        assert cropper.property("implicitWidth") == pytest.approx(120)
        assert cropper.property("implicitHeight") == pytest.approx(80)
        assert cropper.property("cropRect") == QRectF(0.1, 0.1, 0.8, 0.8)
        assert not images[0].isVisible()
        assert columns[0].isVisible()

        cropper.setProperty("source", IMAGE_URL)
        _pump(20)
        assert images[0].isVisible()
        assert not columns[0].isVisible()
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)


def test_image_cropper_overlay_open_close_has_no_native_window_leak(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, cropper, warnings = _create_scene()
    try:
        cropper.setProperty("source", IMAGE_URL)
        assert _wait_for(lambda: cropper.property("_overlayHost") is not None)
        overlay = _overlay(cropper)
        assert not overlay.property("_isOpen")
        assert not overlay.isVisible()

        assert QMetaObject.invokeMethod(cropper, "open")
        assert _wait_for(lambda: bool(overlay.property("_isOpen")))
        assert overlay.isVisible()
        assert overlay.parentItem() is window.contentItem()
        assert (overlay.width(), overlay.height()) == pytest.approx((800, 600))
        assert cropper.property("cropRect") == QRectF(0.1, 0.1, 0.8, 0.8)
        assert _new_visible_windows(windows_before, window) == []

        assert QMetaObject.invokeMethod(cropper, "close")
        assert _wait_for(lambda: not bool(overlay.property("_isOpen")))
        assert _wait_for(lambda: not overlay.isVisible())
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)


def test_image_cropper_lazily_prewarms_and_reuses_mode_hosts(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, cropper, warnings = _create_scene()
    try:
        assert cropper.property("_overlayHost") is None
        assert cropper.property("_dialogHost") is None
        assert [
            item
            for item in _object_descendants(cropper)
            if item.metaObject().indexOfProperty("_imgW") >= 0
            and item.metaObject().indexOfProperty("cropRect") >= 0
        ] == []

        QTest.mouseMove(window, QPoint(window.width() - 1, window.height() - 1))
        _pump()
        point = cropper.mapToItem(
            window.contentItem(), QPointF(cropper.width() / 2, cropper.height() / 2)
        )
        QTest.mouseMove(window, point.toPoint())
        assert _wait_for(lambda: cropper.property("_overlayHost") is not None)
        overlay_host = cropper.property("_overlayHost")
        assert overlay_host is not None
        assert cropper.property("_dialogHost") is None
        created_windows = [
            item
            for item in QGuiApplication.topLevelWindows()
            if not any(item is existing for existing in windows_before)
        ]
        assert created_windows == [window]

        contents = [
            item
            for item in _object_descendants(cropper)
            if item.metaObject().indexOfProperty("_imgW") >= 0
            and item.metaObject().indexOfProperty("cropRect") >= 0
        ]
        assert len(contents) == 1

        cropper.setProperty("type", window.property("dialogType"))
        assert _wait_for(lambda: cropper.property("_dialogHost") is not None)
        dialog_host = cropper.property("_dialogHost")
        assert isinstance(dialog_host, QQuickWindow)
        assert not dialog_host.isVisible()
        assert cropper.property("_overlayHost") == overlay_host

        cropper.setProperty("source", IMAGE_URL)
        assert QMetaObject.invokeMethod(cropper, "open")
        assert _wait_for(dialog_host.isVisible)
        assert QMetaObject.invokeMethod(cropper, "close")
        assert _wait_for(lambda: not dialog_host.isVisible())

        cropper.setProperty("type", window.property("overlayType"))
        _pump()
        assert cropper.property("_overlayHost") == overlay_host
        assert cropper.property("_dialogHost") == dialog_host
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)


def test_image_cropper_source_assignment_prewarms_current_host(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, cropper, warnings = _create_scene()
    try:
        assert cropper.property("_overlayHost") is None
        cropper.setProperty("source", IMAGE_URL)
        assert _wait_for(lambda: cropper.property("_overlayHost") is not None)
        assert cropper.property("_dialogHost") is None
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)


def test_image_cropper_source_conventions():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        item for item in violations if item.rule in {"QML008", "QML009"}
    ] == []
