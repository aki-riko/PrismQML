# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Card Gallery integration contracts. Card Gallery 集成契约。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "examples" / "pages" / "CardPage.qml"
CARD_DEMOS = (
    ("galleryDefaultCard", "galleryDefaultContent", True),
    ("galleryHoverCard", "galleryHoverContent", True),
    ("galleryElevatedCard", "galleryElevatedContent", True),
    ("galleryHeaderCard", "galleryHeaderContent", False),
)


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


@pytest.fixture
def card_gallery(qapp):
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(SOURCE_PATH)))
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert isinstance(root, QQuickItem)
    root.setWidth(1200)
    root.setHeight(900)
    _pump()
    try:
        yield root, warnings
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()


def test_card_gallery_uses_card_content_layout_contract(card_gallery):
    root, warnings = card_gallery

    for card_name, content_name, uses_auto_height in CARD_DEMOS:
        card = root.findChild(QQuickItem, card_name)
        content = root.findChild(QQuickItem, content_name)
        assert card is not None
        assert content is not None
        assert card.property("autoHeight") is uses_auto_height
        assert card.width() == pytest.approx(card.property("contentWidth"))

        content_loader = card.findChild(QQuickItem, "contentLoader")
        assert content_loader is not None
        assert content.parentItem() is content_loader
        assert content.x() == pytest.approx(0)
        assert content.y() == pytest.approx(0)
        assert content.width() == pytest.approx(content_loader.width())
        assert content_loader.x() == pytest.approx(card.property("contentPadding"))

        if uses_auto_height:
            expected_height = max(
                card.property("contentHeight"),
                content.implicitHeight() + card.property("contentPadding") * 2,
            )
            assert card.height() == pytest.approx(expected_height)

    assert warnings == []


def test_card_gallery_source_follows_current_contract_and_conventions():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())

    assert source.count("autoHeight: true") == 3
    assert "anchors.margins: Fluent.Enums.spacing.l" not in source
    assert "width: 280" not in source
    assert "height: 60" not in source
    assert scan_source_text(source, path) == []
