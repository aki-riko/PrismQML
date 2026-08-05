# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Card Gallery integration contracts. Card Gallery 集成契约。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QPoint,
    QPointF,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtGui import QGuiApplication, QWheelEvent
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickView

from examples.resources import register_gallery_resources
from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "examples" / "pages" / "CardPage.qml"
BUTTON_PAGE_PATH = ROOT / "examples" / "pages" / "ButtonPage.qml"
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


def _send_wheel(view: QQuickView, item: QQuickItem) -> QWheelEvent:
    position = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    event = QWheelEvent(
        position,
        QPointF(view.x() + position.x(), view.y() + position.y()),
        QPoint(0, 0),
        QPoint(0, -120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    assert QGuiApplication.sendEvent(view, event)
    return event


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


@pytest.fixture
def button_gallery(qapp):
    assert register_gallery_resources()
    view = QQuickView()
    warnings = []
    view.engine().warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(view.engine())
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
    view.resize(1000, 700)
    view.setSource(QUrl.fromLocalFile(str(BUTTON_PAGE_PATH)))
    assert view.status() == QQuickView.Status.Ready, [
        error.toString() for error in view.errors()
    ]
    view.show()
    _pump(800)
    try:
        yield view, view.rootObject(), warnings
    finally:
        view.close()
        view.deleteLater()
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


def test_example_card_culling_keeps_button_page_geometry_stable(button_gallery):
    view, root, warnings = button_gallery
    items = root.findChildren(QQuickItem)
    area = next(
        item
        for item in items
        if item.metaObject().className().startswith("ScrollArea_QMLTYPE")
        and item.isVisible()
    )
    cards = [
        item
        for item in items
        if item.metaObject().className().startswith("ExampleCard_QMLTYPE")
    ]
    card_columns = [
        next(
            child
            for child in card.childItems()
            if "Column" in child.metaObject().className()
        )
        for card in cards
    ]
    assert {float(column.opacity()) for column in card_columns} == {0.0, 1.0}
    initial_content_height = float(area.property("contentHeight"))
    initial_card_heights = [float(card.implicitHeight()) for card in cards]
    content_heights = []
    area.contentHeightChanged.connect(
        lambda: content_heights.append(float(area.property("contentHeight")))
    )

    for _ in range(51):
        event = _send_wheel(view, area)
        assert event.isAccepted()
        _pump(40)
    _pump(1200)

    assert content_heights == []
    assert float(area.property("contentHeight")) == pytest.approx(
        initial_content_height
    )
    assert [float(card.implicitHeight()) for card in cards] == pytest.approx(
        initial_card_heights
    )
    assert {float(column.opacity()) for column in card_columns} == {0.0, 1.0}
    assert warnings == []
