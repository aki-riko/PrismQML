# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""ViewportLoader runtime contracts. ViewportLoader 运行时合同。"""

from __future__ import annotations

import time
from pathlib import Path

import pytest
import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent, QObject, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types

ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "viewport-loader.qml"))
SLOT_COUNT = 12
SLOT_HEIGHT = 200
SCENE_SOURCE = f"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {{
    id: root
    objectName: "window"

    property int createdCount: 0
    readonly property real defaultPlaceholder: Enums.controlSize.viewportLoaderPlaceholderHeight

    width: 400
    height: 300
    visible: true

    Flickable {{
        id: flick
        objectName: "flick"
        anchors.fill: parent
        contentWidth: width
        contentHeight: column.height
        clip: true

        Column {{
            id: column
            width: flick.width

            Repeater {{
                model: {SLOT_COUNT}

                ViewportLoader {{
                    required property int index
                    objectName: "slot-" + index
                    width: column.width
                    placeholderHeight: 100

                    Rectangle {{
                        objectName: "content"
                        height: {SLOT_HEIGHT}
                        color: Enums.cardColor
                        Component.onCompleted: root.createdCount += 1
                    }}
                }}
            }}
        }}
    }}

    ViewportLoader {{
        objectName: "outside"
        width: 100
        Rectangle {{ objectName: "outsideContent"; width: 10; height: 40 }}
    }}
}}
""".encode("utf-8")


def _pump(milliseconds: int = 30) -> None:
    end = time.perf_counter() + milliseconds / 1000
    while time.perf_counter() < end:
        QCoreApplication.processEvents()
        time.sleep(0.002)


def _wait_for(predicate, timeout_ms: int = 2000) -> bool:
    deadline = time.perf_counter() + timeout_ms / 1000
    while time.perf_counter() < deadline:
        if predicate():
            return True
        _pump(10)
    return predicate()


@pytest.fixture
def scene(qapp):
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda errors: warnings.extend(e.toString() for e in errors))
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [e.toString() for e in component.errors()]
    try:
        flick = window.findChild(QQuickItem, "flick")
        _pump(200)
        column = flick.property("contentItem").childItems()[0]
        slots = sorted(
            (c for c in column.childItems()
             if c.metaObject().className().startswith("ViewportLoader")),
            key=lambda c: c.property("index"),
        )
        assert len(slots) == SLOT_COUNT
        yield window, flick, slots, warnings
    finally:
        if shiboken6.isValid(window):
            window.close()
            window.deleteLater()
        component.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()


def _created(slots):
    return [bool(s.property("created")) for s in slots]


def test_only_slots_near_the_viewport_are_created(scene):
    window, _flick, slots, warnings = scene

    created = _created(slots)
    # Viewport 300px plus one viewport of buffer below: the first slots up to y < 600.
    # Created slots grow to 200px, uncreated ones stay at the 100px placeholder.
    # 视口 300px 加下方一屏缓冲：创建 y < 600 范围内的前几个槽位。已创建的槽位为 200px，
    # 未创建的保持 100px 占位。
    assert created[0] and created[1] and created[2]
    assert not any(created[4:])
    assert window.property("createdCount") == sum(created)
    for slot, made in zip(slots, created):
        assert slot.height() == (SLOT_HEIGHT if made else 100)
    assert warnings == []


def test_scrolling_creates_slots_and_keeps_created_ones(scene):
    window, flick, slots, warnings = scene

    flick.setProperty("contentY", slots[8].y())
    assert _wait_for(lambda: slots[8].property("created"))
    assert all(_created(slots[:3]))
    created_after_scroll = window.property("createdCount")

    flick.setProperty("contentY", 0)
    _pump(200)
    # Scrolling back never rebuilds what already exists 滚回时不重建已存在的内容
    assert window.property("createdCount") == created_after_scroll
    assert warnings == []


def test_create_forces_an_offscreen_slot(scene):
    _window, _flick, slots, _warnings = scene
    last = slots[-1]
    assert not last.property("created")

    last.metaObject().invokeMethod(last, "create")

    assert _wait_for(lambda: last.property("created"))
    assert last.height() == SLOT_HEIGHT
    item = last.property("item")
    assert item is not None and item.objectName() == "content"


def test_content_follows_the_slot_width(scene):
    window, flick, slots, _warnings = scene

    content = slots[0].property("item")
    assert content.width() == pytest.approx(flick.width())
    # The Flickable fills the window, so resize the window 滚动视图填满窗口，因此改窗口宽度
    window.setWidth(300)
    assert _wait_for(lambda: content.width() == pytest.approx(300))


def test_outside_a_flickable_content_is_created_at_once(scene):
    window, _flick, _slots, _warnings = scene
    outside = window.findChild(QQuickItem, "outside")

    assert _wait_for(lambda: outside.property("created"))
    assert outside.height() == 40


def test_default_placeholder_comes_from_enums(scene):
    window, _flick, _slots, _warnings = scene
    assert window.property("defaultPlaceholder") > 0
