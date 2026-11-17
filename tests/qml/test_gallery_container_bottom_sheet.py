# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Gallery bottom sheet demo contracts. Gallery 底部弹层展示合同。"""

import time
from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, QUrl
from PySide6.QtQuick import QQuickItem

from _viewport_loader_support import create_all_viewport_loaders
from tests.qml.test_bottom_sheet import _create_scene, _dispose_scene


ROOT = Path(__file__).resolve().parents[2]
PAGE_URL = QUrl.fromLocalFile(str(ROOT / "examples" / "pages" / "ContainerPage.qml"))
SCENE_SOURCE = f"""
import QtQuick
import QtQuick.Window

Window {{
    width: 1_200
    height: 800
    visible: true

    Loader {{
        objectName: "pageLoader"
        anchors.fill: parent
        source: "{PAGE_URL.toString()}"
    }}
}}
""".encode("utf-8")
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "gallery-bottom-sheet.qml"))
SHEET_NAMES = ("galleryFirstSheet", "gallerySecondSheet", "galleryThirdSheet")


def _wait_for(qapp, predicate, timeout_ms=3_000):
    deadline = time.perf_counter() + timeout_ms / 1_000
    while time.perf_counter() < deadline:
        qapp.processEvents()
        if predicate():
            return True
        time.sleep(0.005)
    return predicate()


def test_gallery_bottom_sheet_demo_stacks_three_levels(qapp):
    engine, component, window, warnings = _create_scene(SCENE_SOURCE, SCENE_URL)
    try:
        loader = window.findChild(QObject, "pageLoader")
        # Loader.status has no Python converter; wait on the loaded item instead
        # Loader.status 没有 Python 转换器，改为等待加载出的 item
        assert _wait_for(qapp, lambda: loader.property("item") is not None), warnings
        page = loader.property("item")
        create_all_viewport_loaders(page)
        sheets = [page.findChild(QQuickItem, name) for name in SHEET_NAMES]
        assert all(sheets), sheets
        button = page.findChild(QQuickItem, "galleryBottomSheetOpenButton")
        assert button is not None

        QMetaObject.invokeMethod(button, "clicked")
        for sheet in sheets[1:]:
            QMetaObject.invokeMethod(sheet, "open")

        assert _wait_for(qapp, lambda: all(s.property("opened") for s in sheets))
        assert [s.property("stackIndex") for s in sheets] == [0, 1, 2]
        # Same detent on every level, so each covered sheet shows only its top edge
        # 各层停靠高度一致，被覆盖层只露出顶边
        assert len({s.property("detent") for s in sheets}) == 1
        assert all(s.parentItem() is window.contentItem() for s in sheets)

        QMetaObject.invokeMethod(sheets[0], "close")
        assert _wait_for(qapp, lambda: not any(s.isVisible() for s in sheets))
        assert not [w for w in warnings if "BottomSheet" in w or "Sheet" in w]
    finally:
        _dispose_scene(engine, component, window)
