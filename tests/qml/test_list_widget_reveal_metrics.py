# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""ListWidget reveal metric regressions. ListWidget 悬浮光晕度量回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
METRICS_SOURCE = ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "Metrics.qml"
LIST_ITEM_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "data"
    / "List"
    / "ListWidgetItem.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "list-widget-reveal-metrics.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    width: 320
    height: 80

    ListWidgetItem {
        objectName: "listItem"
        width: 300
        itemIndex: 0
        itemData: ({ text: "Audit row" })
        hovered: true
    }
}
"""


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_scene():
    engine = QQmlApplicationEngine()
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
    return engine, component, root


def _walk_visual_tree(root: QQuickItem):
    stack = [root]
    while stack:
        item = stack.pop()
        yield item
        stack.extend(reversed(item.childItems()))


def _find_reveal_glow(item: QQuickItem) -> QQuickItem:
    matches = [
        child
        for child in _walk_visual_tree(item)
        if child.metaObject().indexOfProperty("radius") >= 0
        and child.width() == pytest.approx(120)
        and child.height() == pytest.approx(120)
    ]
    assert len(matches) == 1, [
        (
            child.metaObject().className(),
            child.width(),
            child.height(),
            child.property("radius"),
        )
        for child in matches
    ]
    return matches[0]


def test_list_widget_reveal_preserves_runtime_geometry(qapp):
    engine, component, root = _create_scene()
    try:
        item = root.findChild(QQuickItem, "listItem")
        assert item is not None
        glow = _find_reveal_glow(item)

        assert item.height() == pytest.approx(36)
        assert glow.width() == pytest.approx(120)
        assert glow.height() == pytest.approx(120)
        assert glow.property("radius") == pytest.approx(60)
        assert glow.x() == pytest.approx(-60)
        assert glow.y() == pytest.approx(-60)
        assert glow.isVisible()
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_list_widget_reveal_uses_one_diameter_token():
    metrics_source = METRICS_SOURCE.read_text(encoding="utf-8")
    list_item_source = LIST_ITEM_SOURCE.read_text(encoding="utf-8")
    reveal_props = list_item_source.split("id: revealGlow", 1)[1].split(
        "Behavior on opacity", 1
    )[0]

    assert "readonly property int listRevealDiameter: 120" in metrics_source
    assert "width: Enums.controlSize.listRevealDiameter" in reveal_props
    assert "height: width" in reveal_props
    assert "radius: width / 2" in reveal_props
    assert "x: itemArea.mouseX - width / 2" in reveal_props
    assert "y: itemArea.mouseY - height / 2" in reveal_props
    assert "width: 120" not in reveal_props
    assert "height: 120" not in reveal_props
    assert "radius: 60" not in reveal_props
    assert "mouseX - 60" not in reveal_props
    assert "mouseY - 60" not in reveal_props
