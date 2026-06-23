# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是PrismQML的一部分，采用MIT许可证授权。
"""Regression test for Carousel.itemDelegate.

Carousel 原本仅支持 image/color/text 三种内容形态；本次新增 itemDelegate
属性允许业务方传入自定义 Component 渲染每页内容。该测试同时覆盖：
  - 默认情况下（未设置 itemDelegate）行为不变；
  - 设置 itemDelegate 后，Loader 使用业务 delegate 并能读取 itemData。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import prismqml  # noqa: F401  确保资源/导入路径生效


@pytest.fixture(scope="module")
def app():
    existing = QGuiApplication.instance()
    if existing is not None:
        yield existing
        return
    instance = QGuiApplication(sys.argv)
    yield instance


def _load_qml(app, source: str):
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))

    tmp = ROOT / "tests" / "_tmp_carousel_test.qml"
    tmp.write_text(source, encoding="utf-8")
    try:
        engine.load(QUrl.fromLocalFile(str(tmp)))
        roots = engine.rootObjects()
        assert roots, "QML failed to load: " + source
        return engine, roots[0]
    finally:
        # 引擎仍会持有 QML，所以即使删除文件也无影响
        try:
            tmp.unlink()
        except OSError:
            pass


def _find_by_object_name(root, name):
    if root.objectName() == name:
        return root
    for child in root.findChildren(object, name):
        if child.objectName() == name:
            return child
    return None


def test_carousel_default_renders_without_item_delegate(app):
    qml = """
    import QtQuick
    import "../prismqml/PrismQML/controls/data/Carousel"

    Item {
        id: root
        width: 320; height: 180

        Carousel {
            id: c
            objectName: "carousel"
            anchors.fill: parent
            model: [{ color: "#e74c3c", text: "A" }, { color: "#3498db", text: "B" }]
        }
    }
    """
    _, root = _load_qml(app, qml)
    carousel = _find_by_object_name(root, "carousel")
    assert carousel is not None
    assert carousel.property("itemDelegate") is None
    # 默认渲染下能正常切换索引而不报错
    carousel.setProperty("currentIndex", 1)
    app.processEvents()
    assert carousel.property("currentIndex") == 1


def test_carousel_border_radius_and_shadow(app):
    """Carousel 暴露的 borderRadius / shadowLevel 应可配置且不破坏加载。"""
    qml = """
    import QtQuick
    import PrismQML as Fluent
    import "../prismqml/PrismQML/controls/data/Carousel"

    Item {
        id: root
        width: 480; height: 240

        Carousel {
            id: c
            objectName: "carousel"
            anchors.fill: parent
            model: ["a", "b", "c"]
            borderRadius: 16
            shadowLevel: Fluent.Enums.shadow.level4
        }
    }
    """
    _, root = _load_qml(app, qml)
    carousel = _find_by_object_name(root, "carousel")
    assert carousel is not None
    assert carousel.property("borderRadius") == 16
    assert carousel.property("shadowLevel") is not None
    app.processEvents()


def test_carousel_uses_custom_item_delegate(app):
    qml = """
    import QtQuick
    import "../prismqml/PrismQML/controls/data/Carousel"

    Item {
        id: root
        width: 320; height: 180
        property int instCount: 0
        property bool sawValidTitle: false

        Component {
            id: bannerDelegate
            Item {
                anchors.fill: parent
                Component.onCompleted: {
                    // itemData 由宿主 Loader 通过 contextual property 注入。
                    // peek(PathView)会同时实例化中心+相邻项，故用计数 + 合法性校验，
                    // 不依赖"仅实例化第一项"的旧 ListView 假设。
                    if (itemData && itemData.title) {
                        root.instCount += 1
                        if (itemData.title === "first" || itemData.title === "second") {
                            root.sawValidTitle = true
                        }
                    }
                }
                Rectangle {
                    anchors.fill: parent
                    color: itemData && itemData.color ? itemData.color : "transparent"
                }
            }
        }

        Carousel {
            id: c
            objectName: "carousel"
            anchors.fill: parent
            model: [{ color: "#222", title: "first" }, { color: "#444", title: "second" }]
            itemDelegate: bannerDelegate
        }
    }
    """
    engine_keepalive, root = _load_qml(app, qml)  # 接住 engine 保活，避免 root C++ 对象被 GC
    carousel = _find_by_object_name(root, "carousel")
    assert carousel is not None
    assert carousel.property("itemDelegate") is not None

    for _ in range(20):
        app.processEvents()
    # itemDelegate 被真实例化，且注入的 itemData.title 来自 model
    assert root.property("instCount") > 0
    assert root.property("sawValidTitle") is True
    assert engine_keepalive is not None


def test_peek_carousel_instantiates_delegates(app):
    """露边轮播(PathView slide+peek)在两个 orientation 下都应实例化 delegate 并注入正确 itemData。

    旧实现是"横向压扁变形"双 Item；重写为 Fluent 商店式 PathView 后，
    PathView 会按 pathItemCount 实例化中心+相邻项。本测试确认：
      - Qt.Horizontal / Qt.Vertical 两个方向下 delegate 都被真实例化(实例数 > 0)；
      - 中心项(currentIndex)的 itemData 正确注入(读到对应 tag)。
    """
    _engines = []  # 保活：防止上一轮迭代的 engine 被 GC 带走其 root 的 C++ 对象
    for orient in ("Qt.Horizontal", "Qt.Vertical"):
        qml = """
        import QtQuick
        import PrismQML as Fluent
        import "../prismqml/PrismQML/controls/data/Carousel"

        Item {
            id: root
            width: 480; height: 240
            property int instCount: 0
            property string centerTag: ""

            Component {
                id: pageDelegate
                Item {
                    anchors.fill: parent
                    Component.onCompleted: {
                        root.instCount += 1
                        // itemData.idx 标识页序；记录中心项(currentIndex=1)的 tag
                        if (itemData && itemData.idx === 1) {
                            root.centerTag = itemData.tag
                        }
                    }
                    Rectangle { anchors.fill: parent; color: itemData ? itemData.color : "transparent" }
                }
            }

            Carousel {
                id: c
                objectName: "carousel"
                anchors.fill: parent
                currentIndex: 1
                orientation: __ORIENT__
                model: [
                    { idx: 0, tag: "A", color: "#e74c3c" },
                    { idx: 1, tag: "B", color: "#2ecc71" },
                    { idx: 2, tag: "C", color: "#3498db" },
                    { idx: 3, tag: "D", color: "#f1c40f" }
                ]
                itemDelegate: pageDelegate
            }
        }
        """.replace("__ORIENT__", orient)

        engine_keepalive, root = _load_qml(app, qml)
        _engines.append(engine_keepalive)
        carousel = _find_by_object_name(root, "carousel")
        assert carousel is not None, orient

        # PathView 实例化是异步 polish 驱动，泵几轮事件循环
        for _ in range(20):
            app.processEvents()

        inst = root.property("instCount")
        center = root.property("centerTag")
        # PathView 至少实例化中心项；正常 pathItemCount=3 会实例化 3 个
        assert inst > 0, f"{orient}: delegate 未实例化 (instCount={inst})"
        assert center == "B", f"{orient}: 中心项 itemData 注入错误 (centerTag={center!r})"


def test_peek_geometry_is_visible():
    """纯 JS 几何断言：peek(相邻项露出量)应在合理区间。

    不依赖渲染，直接按 CarouselContent 里的公式计算：
      cardLen   = axisLen * centerRatio                       中心卡主轴长度
      slotOffset= axisLen*(centerRatio + scale*centerRatio)/2 + axisLen*spacing
    要求：中心卡占满大部分视图(peek 不喧宾夺主)，但两侧确有可见 peek。
    """
    axis_len = 480.0
    center_ratio = 0.82
    scale = 0.85       # FluentEnums.carousel.peekScale
    spacing = 0.02     # FluentEnums.carousel.peekSpacing

    card_len = axis_len * center_ratio
    slot_offset = axis_len * (center_ratio + scale * center_ratio) / 2 + axis_len * spacing

    # 中心卡左右边缘
    center_half = card_len / 2
    # 相邻卡(同尺寸)靠内边缘相对视图中心的位置
    neighbor_inner_edge = slot_offset - card_len / 2

    # 1) peek 必须为正(相邻卡内边缘越过中心卡外边缘才露得出来)
    peek = center_half - neighbor_inner_edge
    assert peek > 0, f"两侧 peek 不可见: peek={peek:.1f}"
    # 2) peek 不能过大(中心项仍是主角)：露出量 < 中心卡的 20%
    assert peek < card_len * 0.2, f"peek 过大喧宾夺主: peek={peek:.1f}, card={card_len:.1f}"
    # 3) 中心卡占视图主轴 80%~85% 区间
    assert 0.78 <= card_len / axis_len <= 0.86


def test_carousel_effect_slide_instantiates_delegate(app):
    """effect_slide(普通滑动 / ListView 路径)应实例化 delegate 并注入 itemData。

    effect 与 orientation 正交：本测试覆盖非挤压(effect_slide)路径，
    确认恢复的 ListView 实现仍能渲染 itemDelegate 内容。
    """
    qml = """
    import QtQuick
    import PrismQML as Fluent
    import "../prismqml/PrismQML/controls/data/Carousel"

    Item {
        id: root
        width: 320; height: 180
        property int instCount: 0

        Component {
            id: pageDelegate
            Item {
                anchors.fill: parent
                Component.onCompleted: { if (itemData) root.instCount += 1 }
                Rectangle { anchors.fill: parent; color: itemData ? itemData.color : "transparent" }
            }
        }

        Carousel {
            objectName: "carousel"
            anchors.fill: parent
            effect: Fluent.Enums.carousel.effect_slide
            model: [{ color: "#222" }, { color: "#444" }, { color: "#666" }]
            itemDelegate: pageDelegate
        }
    }
    """
    engine_keepalive, root = _load_qml(app, qml)  # 接住 engine 保活
    carousel = _find_by_object_name(root, "carousel")
    assert carousel is not None
    # effect 属性确实被设为 slide
    assert carousel.property("effect") == 1

    for _ in range(20):
        app.processEvents()
    # ListView 路径下 delegate 被实例化
    assert root.property("instCount") > 0
    assert engine_keepalive is not None
