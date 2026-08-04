# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Waterfall stream layout regressions. 瀑布流流式布局回归。"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(
    os.environ.get("PRISMQML_TEST_ROOT", Path(__file__).resolve().parents[2])
).resolve()
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "waterfall-stream-performance.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root

    function seedItems(count) {
        streamCount = count
    }

    function appendItem() {
        streamCount++
    }

    property int streamCount: 0

    width: 420
    height: 720
    visible: true
    color: Enums.backgroundColor

    Component {
        id: streamDelegate

        Rectangle {
            height: parent ? 40 + parent.itemIndex % 5 * 10 : 0
            color: Enums.accentColor
            radius: Enums.radius.small
            border.width: Enums.border.thin
            border.color: Enums.borderColor
        }
    }

    Waterfall {
        id: waterfall

        objectName: "waterfall"
        x: 20
        y: 20
        width: 380
        columns: 3
        spacing: 10
        model: root.streamCount
        delegate: streamDelegate
    }

    Component.onCompleted: seedItems(20)
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


def _walk_items(root: QQuickItem):
    yield root
    for child in root.childItems():
        yield from _walk_items(child)


def _item_loaders(waterfall: QQuickItem) -> list[QQuickItem]:
    return sorted(
        (
            item
            for item in _walk_items(waterfall)
            if item.metaObject().indexOfProperty("itemIndex") >= 0
            and item.metaObject().indexOfProperty("targetColumn") >= 0
        ),
        key=lambda item: int(item.property("itemIndex")),
    )


def _geometry_hash(waterfall: QQuickItem) -> str:
    geometry = [
        (
            int(loader.property("itemIndex")),
            int(loader.property("targetColumn")),
            round(loader.x(), 6),
            round(loader.y(), 6),
            round(loader.width(), 6),
            round(loader.height(), 6),
        )
        for loader in _item_loaders(waterfall)
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
    waterfall = window.findChild(QQuickItem, "waterfall")
    assert waterfall is not None
    assert _wait_for(lambda: len(_item_loaders(waterfall)) == 20)
    assert _wait_for(lambda: waterfall.property("contentHeight") > 0)
    return engine, component, window, waterfall, warnings


def _dispose_scene(engine, component, window) -> None:
    window.setVisible(False)
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def test_waterfall_stream_append_preserves_layout_without_full_rescans(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, waterfall, warnings = _create_scene()
    try:
        initial_hash = _grab_hash(window)
        relayouts_before = waterfall.property("_relayoutCount")

        for _ in range(30):
            window.appendItem()
            _pump(1)

        assert _wait_for(lambda: len(_item_loaders(waterfall)) == 50)
        _pump(80)
        relayout_delta = waterfall.property("_relayoutCount") - relayouts_before
        stream_geometry_hash = _geometry_hash(waterfall)
        stream_hash = _grab_hash(window)

        waterfall.setProperty("columns", 4)
        assert _wait_for(lambda: waterfall.property("_relayoutCount") > relayouts_before)
        four_column_geometry_hash = _geometry_hash(waterfall)
        four_column_hash = _grab_hash(window)

        waterfall.setProperty("columns", 3)
        assert _wait_for(
            lambda: _geometry_hash(waterfall) == stream_geometry_hash
        )
        restored_hash = _grab_hash(window)

        print(
            "WATERFALL_STREAM",
            f"relayouts={relayout_delta}",
            f"initial_hash={initial_hash}",
            f"stream_geometry={stream_geometry_hash}",
            f"stream_hash={stream_hash}",
            f"four_geometry={four_column_geometry_hash}",
            f"four_hash={four_column_hash}",
            f"restored_hash={restored_hash}",
        )

        assert relayout_delta == 30
        assert initial_hash == (
            "9f474d1272c55f9cb61581dcc4e695da982533abdc6df454449cac2fcfa1bdec"
        )
        assert stream_geometry_hash == (
            "3aab6bf08f602242c6d0744a1857155a19ffa5f97aa80e92aab38947d6fd9a1f"
        )
        assert stream_hash == (
            "0897de39de5b1203cadaf94cd72487444abf6e7248ffc4dbcbb9d5c2aae1b084"
        )
        assert four_column_geometry_hash == (
            "9f3a368306bad5e757333ebf6ca5d2698a2da19d26a5c7a4aea59427144d7aba"
        )
        assert four_column_hash == (
            "fc9928e51ca3ae035038af56f74007b64f8df8485df3e9b7ce0f5182691f0ea1"
        )
        assert restored_hash == stream_hash
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []
