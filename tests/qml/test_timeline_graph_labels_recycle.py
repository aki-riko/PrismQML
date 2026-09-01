# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Timeline graph-mode label runtime coverage. 时间线图模式标签运行期覆盖。

Adds first runtime coverage for the graph-mode ``cardData.labels`` path, which
previously had none: rows are scrolled so delegates are pooled and reused
between header rows (no ``cardData``) and card rows (with ``cardData``), and the
model is then replaced, asserting no QML warning appears.
为此前零运行期覆盖的图模式 ``cardData.labels`` 路径补第一份覆盖: 滚动使
delegate 在标题行(无 ``cardData``)与卡片行(有 ``cardData``)之间池化复用,
随后替换模型, 断言不出现 QML warning。

Scope limit 覆盖边界:
This does NOT reproduce the reported ``TimelineVirtualRow.qml:279`` TypeError
from a real desktop session. That binding takes its guard from the separate
``visible`` binding, so triggering it depends on QML binding re-evaluation
order, which this offscreen, programmatic-scroll harness did not hit. Do not
treat this test as a regression guard for that defect.
本测试**不能**复现真机会话里报出的 ``TimelineVirtualRow.qml:279`` TypeError。
该绑定从独立的 ``visible`` 绑定取守卫, 触发与 QML 绑定重算顺序相关, 本
offscreen + 程序化滚动装配未命中。不得把它当该缺陷的回归门禁。
"""

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QTimer,
    QUrl,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem

from prismqml import configure_qml_environment, register_types


# Graph mode plus labelled cards, so TimelineGraphLabels binds cardData.labels.
# 图模式加带标签卡片, 使 TimelineGraphLabels 绑定到 cardData.labels。
GRAPH_LABEL_SCENE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    width: 480
    height: 240
    visible: true

    // Many groups so rows exceed the viewport and delegates get pooled and
    // reused across header/card kinds while scrolling.
    readonly property var labelledItems: {
        var groups = []
        for (var g = 0; g < 12; g++) {
            var cards = []
            for (var c = 0; c < 3; c++) {
                cards.push({
                    "text": "change " + g + "-" + c,
                    "labels": ["alpha" + g, "beta" + c],
                    "commit": "c" + g + "-" + c
                })
            }
            groups.push({
                "title": "Group " + g,
                "status": "info",
                "cards": cards
            })
        }
        return groups
    }

    // Replacement groups keep header rows only, so every recycled row model
    // loses its cardData field.
    readonly property var headerOnlyItems: [{
        "title": "Yesterday",
        "status": "info",
        "cards": []
    }, {
        "title": "Earlier",
        "status": "info",
        "cards": []
    }]

    function useHeaderOnlyItems() {
        timeline.items = root.headerOnlyItems
    }

    TimelineCore {
        id: timeline
        objectName: "timeline"
        anchors.fill: parent
        type: Enums.timeline.type_graph
        virtualized: true
        showScrollBar: false
        items: root.labelledItems
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _visual_descendants(item):
    """Walk the visual tree; delegates hang off contentItem, not findChildren.

    遍历可视树: 行委托挂在 contentItem 下, findChildren 取不到。
    """
    descendants = []
    for child in item.childItems():
        descendants.append(child)
        descendants.extend(_visual_descendants(child))
    return descendants


def test_graph_label_rows_survive_reuse_and_model_replacement(qapp):
    """图模式行经池化复用与模型替换后不产生 QML warning。"""
    configure_qml_environment()
    engine = QQmlApplicationEngine()
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(
        GRAPH_LABEL_SCENE,
        QUrl("inline:timeline-graph-labels-recycle.qml"),
    )
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    try:
        _pump(150)
        timeline = root.findChild(QQuickItem, "timeline")
        assert timeline is not None
        # A real render pass is required, otherwise ListView never creates the
        # row delegates and the label bindings are never evaluated.
        # 必须真实渲染一次, 否则 ListView 不会创建行委托, 标签绑定不会求值。
        assert not root.grabWindow().isNull()
        _pump(200)

        label_hosts = [
            item
            for item in _visual_descendants(timeline)
            if item.metaObject().indexOfProperty("labels") >= 0
        ]
        # Guard the probe itself: without live label hosts the recycle
        # assertion below would pass vacuously.
        # 自我保护: 没有活的标签宿主时, 下面的回收断言会空过。
        assert label_hosts, "no live label hosts, scene not exercising labels"
        # Baseline must be clean, otherwise the recycle assertion is meaningless.
        # 基线必须干净, 否则回收断言没有意义。
        assert warnings == [], warnings

        # TimelineCore does not expose its ListView, so reach it by class name
        # the same way test_timeline_graph_pixels.py does.
        # TimelineCore 不对外暴露 ListView, 按类名取, 与既有像素测试同法。
        list_view = next(
            item
            for item in _visual_descendants(timeline)
            if "ListView" in item.metaObject().className()
        )
        content_height = list_view.property("contentHeight")
        view_height = list_view.property("height")
        # Rows must overflow the viewport, otherwise nothing is ever pooled.
        # 行必须溢出视口, 否则不会发生任何 delegate 池化复用。
        assert content_height > view_height, (content_height, view_height)

        # Scroll across the whole list so delegates are pooled and reused
        # between header rows (no cardData) and card rows (with cardData).
        # 全程滚动, 使 delegate 在标题行(无 cardData)与卡片行(有 cardData)
        # 之间池化复用。
        step = max(1.0, float(view_height) / 3.0)
        offset = 0.0
        while offset < float(content_height):
            list_view.setProperty("contentY", offset)
            _pump(40)
            assert not root.grabWindow().isNull()
            offset += step
        # Scroll back up as well; reuse happens in both directions.
        # 反向滚回, 两个方向都会发生复用。
        while offset > 0.0:
            list_view.setProperty("contentY", offset)
            _pump(40)
            assert not root.grabWindow().isNull()
            offset -= step
        _pump(200)

        # Also exercise the model-replacement path, which destroys rows.
        # 同时走模型替换路径, 该路径销毁行。
        assert QMetaObject.invokeMethod(root, "useHeaderOnlyItems")
        _pump(250)
        assert not root.grabWindow().isNull()
        _pump(250)

        type_errors = [text for text in warnings if "TypeError" in text]
        assert type_errors == [], type_errors
        assert warnings == [], warnings
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()
