# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""FlowLayout stream append regressions. 流式布局尾增回归。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QObject,
    QTimer,
    QUrl,
)
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "flow-layout-stream-performance.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: host

    property int nextIndex: 0

    function appendItem() {
        var item = cardComponent.createObject(flow, { itemIndex: nextIndex })
        flow.addWidget(item)
        nextIndex++
    }

    function seedItems(count) {
        for (var index = 0; index < count; index++) appendItem()
    }

    function appendAcrossSearchThreshold() {
        seedItems(75)
    }

    function appendZeroSizedItem() {
        var item = zeroSizedComponent.createObject(flow)
        flow.addWidget(item)
    }

    function useHorizontalMode() {
        flow.mode = Enums.flow.horizontal
    }

    function useVerticalMode() {
        flow.mode = Enums.flow.vertical
    }

    function useDefaultMode() {
        flow.mode = Enums.flow.default_
    }

    function forceFullLayout() {
        flow._cacheAllOriginalSizes()
        flow._invalidateLayout()
    }

    width: 420
    height: 720
    visible: true
    color: Enums.backgroundColor

    FlowLayout {
        id: flow

        objectName: "flow"
        x: 20
        y: 20
        width: 380
        spacing: 10
        rowSpacing: 6
    }

    Component {
        id: cardComponent

        Rectangle {
            required property int itemIndex

            width: 32 + itemIndex % 7 * 9
            height: 24 + itemIndex % 5 * 7
            color: Enums.accentColor
            radius: Enums.radius.small
            border.width: Enums.border.thin
            border.color: Enums.borderColor
        }
    }

    Component {
        id: zeroSizedComponent

        Item { objectName: "zeroSizedItem" }
    }

    Component.onCompleted: seedItems(30)
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2_000) -> bool:
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
        and not any(window is expected for expected in allowed)
    ]


def _layout_items(flow: QQuickItem) -> list[QQuickItem]:
    content_item = flow.findChild(QQuickItem, "contentItem")
    assert content_item is not None
    return sorted(
        (
            item
            for item in content_item.childItems()
            if item.metaObject().indexOfProperty("itemIndex") >= 0
        ),
        key=lambda item: int(item.property("itemIndex")),
    )


def _geometry_hash(flow: QQuickItem) -> str:
    geometry = [
        (
            int(item.property("itemIndex")),
            round(item.x(), 6),
            round(item.y(), 6),
            round(item.width(), 6),
            round(item.height(), 6),
        )
        for item in _layout_items(flow)
    ]
    payload = json.dumps(geometry, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _image_hash(image: QImage) -> str:
    normalized = image.convertToFormat(QImage.Format.Format_RGBA8888)
    return hashlib.sha256(bytes(normalized.bits())).hexdigest()


def _grab_hash(window: QQuickWindow) -> str:
    _pump(80)
    image = window.grabWindow()
    assert not image.isNull()
    return _image_hash(image)


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
    flow = window.findChild(QQuickItem, "flow")
    assert flow is not None
    assert _wait_for(lambda: len(_layout_items(flow)) == 30)
    assert _wait_for(lambda: flow.property("implicitHeight") > 0)
    _pump(80)
    return engine, component, window, flow, warnings


def _dispose_scene(engine, component, window) -> None:
    window.setVisible(False)
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def test_flow_layout_tail_append_preserves_geometry_and_pixels(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, flow, warnings = _create_scene()
    try:
        cache_changes = []
        flow._originalSizesChanged.connect(lambda: cache_changes.append(None))
        initial_hash = _grab_hash(window)

        for _ in range(20):
            window.appendItem()
            _pump(1)

        assert _wait_for(lambda: len(_layout_items(flow)) == 50)
        _pump(80)
        cache_delta = len(cache_changes)
        stream_geometry_hash = _geometry_hash(flow)
        stream_hash = _grab_hash(window)

        flow.setWidth(220)
        assert _wait_for(lambda: len(cache_changes) > cache_delta)
        assert _wait_for(lambda: _geometry_hash(flow) != stream_geometry_hash)
        narrow_geometry_hash = _geometry_hash(flow)
        narrow_hash = _grab_hash(window)

        flow.setWidth(380)
        assert _wait_for(lambda: _geometry_hash(flow) == stream_geometry_hash)
        restored_hash = _grab_hash(window)

        cache_changes_before_removal = len(cache_changes)
        flow.removeWidget(flow.itemAt(5))
        assert _wait_for(lambda: len(_layout_items(flow)) == 49)
        assert _wait_for(
            lambda: len(cache_changes) > cache_changes_before_removal
        )

        print(
            "FLOW_LAYOUT_STREAM",
            f"cache_changes={cache_delta}",
            f"initial_hash={initial_hash}",
            f"stream_geometry={stream_geometry_hash}",
            f"stream_hash={stream_hash}",
            f"narrow_geometry={narrow_geometry_hash}",
            f"narrow_hash={narrow_hash}",
            f"restored_hash={restored_hash}",
        )

        assert cache_delta == 0
        assert initial_hash == (
            "69bad6081e30c3cb87c5d31b2c8faeff4b86f3d621a34d6973b849092b36e77f"
        )
        assert stream_geometry_hash == (
            "57fea50304cd2e5d6ddbb3bb0c8900c9bdc257f4d4dbab54254f0f730549b11f"
        )
        assert stream_hash == (
            "1d672ca5cd820c1ae808ea0041c0fa5de410177a7c5a200a771935f6a32ff2a2"
        )
        assert narrow_geometry_hash == (
            "a561404bab5b1a34a88b002f46ff244381940dbddca37331a564b3c20ba28936"
        )
        assert narrow_hash == (
            "f4f9fe50281bc2fc97d241fbc866f0526218fbf53c85c1495657bc61a48368b3"
        )
        assert restored_hash == stream_hash
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_flow_layout_batch_append_matches_full_layout_across_search_threshold(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, flow, warnings = _create_scene()
    try:
        cache_changes = []
        flow._originalSizesChanged.connect(lambda: cache_changes.append(None))

        assert QMetaObject.invokeMethod(window, "appendAcrossSearchThreshold")
        assert _wait_for(lambda: len(_layout_items(flow)) == 105)
        assert _wait_for(lambda: int(flow.property("_laidOutItemCount")) == 105)
        _pump(80)
        incremental_geometry_hash = _geometry_hash(flow)
        incremental_pixel_hash = _grab_hash(window)

        assert cache_changes == []
        assert QMetaObject.invokeMethod(window, "forceFullLayout")
        assert _wait_for(lambda: len(cache_changes) == 1)
        _pump(80)

        assert _geometry_hash(flow) == incremental_geometry_hash
        assert _grab_hash(window) == incremental_pixel_hash
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_flow_layout_tail_fast_path_and_mode_fallback_boundaries(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, flow, warnings = _create_scene()
    try:
        cache_changes = []
        flow._originalSizesChanged.connect(lambda: cache_changes.append(None))
        initial_geometry_hash = _geometry_hash(flow)
        initial_height = float(flow.property("implicitHeight"))

        assert QMetaObject.invokeMethod(window, "appendZeroSizedItem")
        _pump(40)
        assert cache_changes == []
        assert _geometry_hash(flow) == initial_geometry_hash
        assert float(flow.property("implicitHeight")) == initial_height

        window.appendItem()
        assert _wait_for(lambda: len(_layout_items(flow)) == 31)
        assert _wait_for(lambda: int(flow.property("_laidOutItemCount")) == 31)
        assert cache_changes == []

        assert QMetaObject.invokeMethod(window, "useHorizontalMode")
        _pump(40)
        window.appendItem()
        assert _wait_for(lambda: len(cache_changes) == 1)
        assert _wait_for(lambda: len(_layout_items(flow)) == 32)

        assert QMetaObject.invokeMethod(window, "useVerticalMode")
        _pump(40)
        window.appendItem()
        assert _wait_for(lambda: len(cache_changes) == 2)
        assert _wait_for(lambda: len(_layout_items(flow)) == 33)

        assert QMetaObject.invokeMethod(window, "useDefaultMode")
        assert _wait_for(lambda: int(flow.property("_laidOutItemCount")) == 33)
        flow.setProperty("spacing", int(flow.property("spacing")) + 1)
        _pump(40)
        window.appendItem()
        assert _wait_for(lambda: len(_layout_items(flow)) == 34)
        assert _wait_for(lambda: int(flow.property("_laidOutItemCount")) == 34)
        assert len(cache_changes) == 2

        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []
