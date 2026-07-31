# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Shared icon renderer contracts. 共享图标渲染器合同。"""

from pathlib import Path

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
QML_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    Icon { objectName: "emptyIcon" }
    Icon { objectName: "textIcon"; icon: "A" }
    Icon { objectName: "svgIcon"; icon: Enums.icon.settings }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _loader(icon: QQuickItem) -> QObject:
    matches = [
        child
        for child in icon.findChildren(QObject)
        if child.metaObject().className().startswith("QQuickLoader")
    ]
    assert len(matches) == 1
    return matches[0]


def _renderer(icon: QQuickItem) -> QQuickItem | None:
    item = _loader(icon).property("item")
    return item if isinstance(item, QQuickItem) else None


def _local_components(icon: QQuickItem) -> list[QObject]:
    return [
        child
        for child in icon.findChildren(QObject)
        if child.metaObject().className() == "QQmlComponent"
    ]


def test_icons_share_renderer_components_and_keep_runtime_switching(qapp):
    engine = QQmlEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(QML_SOURCE, QUrl("inline:icon-renderer-sharing.qml"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    root = component.create()
    assert isinstance(root, QQuickItem), [
        error.toString() for error in component.errors()
    ]
    try:
        empty_icon = root.findChild(QQuickItem, "emptyIcon")
        text_icon = root.findChild(QQuickItem, "textIcon")
        svg_icon = root.findChild(QQuickItem, "svgIcon")
        assert empty_icon is not None
        assert text_icon is not None
        assert svg_icon is not None

        assert _renderer(empty_icon) is None
        assert _renderer(text_icon).metaObject().className().startswith("QQuickText")
        assert _renderer(svg_icon).metaObject().className().startswith("QQuickImage")
        assert _local_components(empty_icon) == []
        assert _local_components(text_icon) == []
        assert _local_components(svg_icon) == []

        assert empty_icon.setProperty("icon", "A")
        _pump()
        assert _renderer(empty_icon).metaObject().className().startswith("QQuickText")
        assert empty_icon.setProperty("icon", "Settings")
        _pump()
        assert _renderer(empty_icon).metaObject().className().startswith("QQuickImage")
        assert empty_icon.setProperty("icon", "")
        _pump()
        assert _renderer(empty_icon) is None
        assert warnings == []
    finally:
        root.deleteLater()
        engine.deleteLater()
        _pump(1)
