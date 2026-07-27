# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Gallery outside Drawer interaction contracts. Gallery 外层抽屉交互合同。"""

import time
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QMetaObject, QObject, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "examples" / "pages" / "ContainerPage.qml"
PAGE_URL = QUrl.fromLocalFile(str(SOURCE_PATH))


def _wait_for(qapp, predicate, timeout_ms=2_000):
    deadline = time.monotonic() + timeout_ms / 1_000
    while time.monotonic() < deadline:
        qapp.processEvents()
        if predicate():
            return True
        time.sleep(0.005)
    return predicate()


def _load_page():
    engine = QQmlEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.loadUrl(PAGE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create()
    assert isinstance(root, QQuickItem), [
        error.toString() for error in component.errors()
    ]
    return engine, component, root


def test_gallery_uses_one_outside_drawer_per_edge():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    drawer_ids = (
        "outsideLeftDrawer",
        "outsideRightDrawer",
        "outsideTopDrawer",
        "outsideBottomDrawer",
    )

    assert "outsideDrawer.position" not in source
    for drawer_id in drawer_ids:
        assert f"id: {drawer_id}" in source
        assert f"onClicked: {drawer_id}.open()" in source


def test_gallery_can_animate_two_outside_drawers_together(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root = _load_page()
    window = QQuickWindow()
    window.resize(1_200, 800)
    root.setParentItem(window.contentItem())
    root.setSize(window.size())
    window.show()
    left = root.findChild(QObject, "galleryOutsideLeftDrawer")
    top = root.findChild(QObject, "galleryOutsideTopDrawer")
    try:
        assert left is not None
        assert top is not None
        left.setProperty("animationDuration", 240)
        top.setProperty("animationDuration", 240)

        assert QMetaObject.invokeMethod(left, "open")
        assert QMetaObject.invokeMethod(top, "open")
        assert _wait_for(
            qapp,
            lambda: (
                1 < left.property("_outsideExtent") < left.property("drawerWidth")
                and 1 < top.property("_outsideExtent") < top.property("drawerHeight")
            ),
        )
        assert left.property("opened") is True
        assert top.property("opened") is True
        assert _wait_for(
            qapp,
            lambda: left.property("_outsideExtent") == left.property("drawerWidth")
            and top.property("_outsideExtent") == top.property("drawerHeight"),
        )
        visible_drawers = [
            candidate
            for candidate in QGuiApplication.topLevelWindows()
            if candidate not in windows_before
            and candidate is not window
            and candidate.objectName() == "outsideDrawerWindow"
            and candidate.isVisible()
        ]
        assert len(visible_drawers) == 2
    finally:
        if left is not None:
            QMetaObject.invokeMethod(left, "close")
        if top is not None:
            QMetaObject.invokeMethod(top, "close")
        _wait_for(
            qapp,
            lambda: not any(
                candidate.isVisible()
                for candidate in QGuiApplication.topLevelWindows()
                if candidate.objectName() == "outsideDrawerWindow"
            ),
        )
        window.close()
        window.deleteLater()
        root.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()
        assert not [
            candidate
            for candidate in QGuiApplication.topLevelWindows()
            if not any(candidate is existing for existing in windows_before)
        ]
