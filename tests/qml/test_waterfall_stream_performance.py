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
        streamModel.clear()
        for (var index = 0; index < count; ++index) {
            streamModel.append({ sequence: index })
        }
    }

    function appendItem() {
        streamModel.append({ sequence: streamModel.count })
    }

    function insertItem(index) {
        streamModel.insert(index, { sequence: -1 })
    }

    function removeItem(index) {
        streamModel.remove(index)
    }

    function useTallDelegate() {
        waterfall.delegate = tallDelegate
    }

    width: 420
    height: 720
    visible: true
    color: Enums.backgroundColor

    ListModel {
        id: streamModel
    }

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

    Component {
        id: tallDelegate

        Rectangle {
            height: 95
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
        model: streamModel
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


def _expected_geometry_hash(
    item_count: int,
    columns: int = 3,
    height_overrides: dict[int, int] | None = None,
) -> str:
    overrides = height_overrides or {}
    spacing = 10
    item_width = (380 - (columns - 1) * spacing) / columns
    heights = [0.0] * columns
    geometry = []
    for item_index in range(item_count):
        target_column = min(range(columns), key=heights.__getitem__)
        target_y = heights[target_column]
        item_height = float(overrides.get(item_index, 40 + item_index % 5 * 10))
        geometry.append(
            (
                item_index,
                target_column,
                round(target_column * (item_width + spacing), 6),
                round(target_y, 6),
                round(item_width, 6),
                round(item_height, 6),
            )
        )
        heights[target_column] = target_y + item_height + spacing
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

        relayouts_before_column_change = waterfall.property("_relayoutCount")
        waterfall.setProperty("columns", 4)
        assert _wait_for(
            lambda: waterfall.property("_relayoutCount")
            > relayouts_before_column_change
        )
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

        assert relayout_delta == 0
        # Geometry hashes stay pinned: computed from item x/y/w/h, so they are
        # deterministic and a change means the layout really moved. Pixel
        # hashes are not reproducible across sessions, so those become
        # relations.
        # 几何哈希继续钉死: 由 item 的 x/y/w/h 算出, 确定性, 变了就是布局真的动了。
        # 像素哈希跨会话不可复现, 故改为断言关系。
        assert stream_geometry_hash == (
            "3aab6bf08f602242c6d0744a1857155a19ffa5f97aa80e92aab38947d6fd9a1f"
        )
        assert four_column_geometry_hash == (
            "6c1871514b8a82e367e943488b3764f8fd4dcf5e91811b12bcfeedfda60bd12c"
        )
        # Streaming must change the render; switching to four columns must
        # change it again; restoring must reproduce the streamed render exactly.
        # 流式加入必须改变渲染; 切到四列必须再次改变; 恢复必须精确重现流式渲染。
        assert stream_hash != initial_hash
        assert four_column_hash != stream_hash
        assert restored_hash == stream_hash
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_waterfall_non_tail_changes_still_force_full_relayout(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, waterfall, warnings = _create_scene()
    try:
        relayouts_before = waterfall.property("_relayoutCount")
        window.insertItem(5)
        assert _wait_for(lambda: len(_item_loaders(waterfall)) == 21)
        assert _wait_for(
            lambda: waterfall.property("_relayoutCount") > relayouts_before
        )
        assert _wait_for(
            lambda: _geometry_hash(waterfall) == _expected_geometry_hash(21)
        )

        relayouts_before = waterfall.property("_relayoutCount")
        window.removeItem(5)
        assert _wait_for(lambda: len(_item_loaders(waterfall)) == 20)
        assert _wait_for(
            lambda: waterfall.property("_relayoutCount") > relayouts_before
        )
        assert _wait_for(
            lambda: _geometry_hash(waterfall) == _expected_geometry_hash(20)
        )

        first_item = _item_loaders(waterfall)[0].property("item")
        relayouts_before = waterfall.property("_relayoutCount")
        first_item.setHeight(95)
        assert _wait_for(
            lambda: waterfall.property("_relayoutCount") > relayouts_before
        )
        assert _wait_for(
            lambda: _geometry_hash(waterfall)
            == _expected_geometry_hash(20, height_overrides={0: 95})
        )

        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_waterfall_delegate_replacement_forces_full_relayout(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, waterfall, warnings = _create_scene()
    try:
        relayouts_before = waterfall.property("_relayoutCount")
        window.useTallDelegate()
        assert _wait_for(
            lambda: waterfall.property("_relayoutCount") > relayouts_before
        )
        assert _wait_for(
            lambda: _geometry_hash(waterfall)
            == "d7aba1f9516e1c51292a6483f624161bd7d3379e8c5561446374e19403bd12c0"
        )

        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []
