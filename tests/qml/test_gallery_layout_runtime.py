# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from examples.resources import register_gallery_resources
from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
PAGE_PATHS = tuple(sorted((ROOT / "examples" / "pages").glob("*.qml")))


def _pump(milliseconds: int = 80) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _dispose(obj) -> None:
    if obj is None:
        return
    obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def test_gallery_flows_fit_their_content_width_at_standard_gallery_size(qapp):
    """Responsive demo flows must keep direct cards inside a 960px content area."""
    register_gallery_resources()
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    host = QQuickWindow()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )

    try:
        for page_path in PAGE_PATHS:
            component = QQmlComponent(engine, QUrl.fromLocalFile(str(page_path)))
            page = component.create(engine.rootContext())
            assert page is not None, [error.toString() for error in component.errors()]
            assert isinstance(page, QQuickItem)
            page.setParentItem(host.contentItem())
            page.setWidth(960)
            page.setHeight(720)
            _pump()

            flows = [
                item
                for item in page.findChildren(QQuickItem)
                if "GalleryFlow" in item.metaObject().className()
            ]
            for flow in flows:
                for child in flow.childItems():
                    assert child.x() >= -0.5, f"{page_path.name}: negative child x"
                    assert child.x() + child.width() <= flow.width() + 0.5, (
                        f"{page_path.name}: child exceeds GalleryFlow width"
                    )

            _dispose(page)
            _dispose(component)

        assert warnings == []
    finally:
        _dispose(host)
        engine.collectGarbage()
        engine.clearComponentCache()
        _dispose(engine)
