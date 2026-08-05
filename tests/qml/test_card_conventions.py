# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Card geometry and interaction contracts. Card 几何与交互合同。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QPoint,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "containers"
    / "Card"
    / "Card.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "card-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"

    readonly property int cardMinimumHeight: Enums.controlSize.cardHeight
    readonly property real fixedHeight: fixedCard.height
    readonly property real tallHeight: tallCard.height
    readonly property real shortHeight: shortCard.height
    readonly property real headerHeight: headerCard.height
    readonly property real headerContentHeight: headerContent.height
    readonly property real noPaddingHeaderHeight: noPaddingHeader.height
    readonly property real elevatedOffset: elevatedCard.transform[0].y
    readonly property bool elevatedHovered: elevatedCard.hovered
    readonly property bool elevatedPressed: elevatedCard.pressed
    readonly property real cardElevate: Enums.spacing.cardElevate
    readonly property int mediumDuration: Enums.duration.medium
    readonly property real defaultContentPadding: Enums.spacing.l
    readonly property real headerContentPadding: Enums.spacing.xxxl

    width: 680
    height: 560
    visible: false

    Card {
        id: fixedCard
        objectName: "fixedCard"
        x: 20
        y: 20
        width: 220
        height: 80
        clickEnabled: false

        Rectangle { anchors.fill: parent }
    }

    Card {
        id: tallCard
        objectName: "tallCard"
        x: 260
        y: 20
        width: 220
        autoHeight: true

        Column {
            width: parent.width
            spacing: 6
            Repeater { model: 6; Rectangle { width: 100; height: 16 } }
        }
    }

    Card {
        id: shortCard
        objectName: "shortCard"
        x: 20
        y: 140
        width: 220
        autoHeight: true
        cardType: Enums.card.type_hover

        Rectangle { width: 100; height: 16 }
    }

    Card {
        id: headerCard
        objectName: "headerCard"
        x: 260
        y: 140
        width: 240
        cardType: Enums.card.type_header
        title: "Header title"

        Rectangle {
            id: headerContent
            objectName: "headerContent"
            width: parent.width
            height: 40
        }
    }

    Card {
        id: noPaddingHeader
        objectName: "noPaddingHeader"
        x: 520
        y: 140
        width: 140
        cardType: Enums.card.type_header
        contentPadding: Enums.spacing.none
        title: "Compact"

        Rectangle {
            width: parent.width
            height: 40
        }
    }

    Card {
        id: elevatedCard
        objectName: "elevatedCard"
        x: 20
        y: 320
        width: 220
        height: 90
        cardType: Enums.card.type_elevated
        clickEnabled: true
    }

    ExampleCard {
        id: exampleCard
        objectName: "exampleCard"
        x: 260
        y: 320
        width: 300
        title: "Example"
        description: "Description"

        Rectangle { width: 100; height: 24 }
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 30
    return predicate()


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is accepted for accepted in allowed)
    ]


def _descendants(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _descendants(child)


def _neo_shadows(item: QQuickItem) -> list[QQuickItem]:
    return [
        child
        for child in _descendants(item)
        if child.metaObject().className().startswith("NeoShadow_QMLTYPE_")
    ]


def _stable_window_image(window: QQuickWindow) -> QImage:
    previous = QImage()
    stable_frames = 0
    for _ in range(40):
        current = window.grabWindow()
        assert not current.isNull()
        if current == previous:
            stable_frames += 1
            if stable_frames == 3:
                return current
        else:
            stable_frames = 0
        previous = current
        _pump()
    raise AssertionError("Card frame did not stabilize within 1.2 seconds")


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow)
    _pump()
    return engine, component, window, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


@pytest.fixture
def card_scene(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, warnings = _create_scene()
    try:
        yield window, warnings, windows_before
    finally:
        _dispose_scene(engine, component, window)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_card_fixed_auto_and_header_heights(card_scene):
    window, warnings, windows_before = card_scene
    minimum_height = window.property("cardMinimumHeight")
    fixed = window.findChild(QQuickItem, "fixedCard")
    content_loader = fixed.findChild(QQuickItem, "contentLoader")
    assert window.property("fixedHeight") == pytest.approx(80)
    assert fixed.property("contentPadding") == pytest.approx(
        window.property("defaultContentPadding")
    )
    assert content_loader.x() == pytest.approx(window.property("defaultContentPadding"))
    assert content_loader.y() == pytest.approx(window.property("defaultContentPadding"))
    assert content_loader.width() == pytest.approx(
        fixed.width() - window.property("defaultContentPadding") * 2
    )
    assert window.property("shortHeight") == pytest.approx(minimum_height)
    assert window.property("tallHeight") > minimum_height
    assert window.property("tallHeight") > window.property("shortHeight")
    assert window.property("headerHeight") > window.property("headerContentHeight")
    assert window.property("headerHeight") - window.property(
        "noPaddingHeaderHeight"
    ) == pytest.approx(window.property("headerContentPadding") * 2)
    header = window.findChild(QQuickItem, "headerCard")
    no_padding_header = window.findChild(QQuickItem, "noPaddingHeader")
    no_padding_loader = no_padding_header.findChild(QQuickItem, "contentLoader")
    assert no_padding_header.property("contentPadding") == 0
    assert no_padding_loader.x() == pytest.approx(0)
    assert no_padding_loader.width() == pytest.approx(no_padding_header.width())
    labels = [
        item
        for item in header.findChildren(QQuickItem)
        if item.property("text") == "Header title"
    ]
    assert len(labels) == 1
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_card_real_hover_press_and_click(card_scene):
    window, warnings, windows_before = card_scene
    elevated = window.findChild(QQuickItem, "elevatedCard")
    clicks = []
    elevated.clicked.connect(lambda: clicks.append(True))
    window.show()
    _pump()

    QTest.mouseMove(window, QPoint(100, 360))
    assert _wait_for(lambda: window.property("elevatedHovered"))
    assert _wait_for(
        lambda: window.property("elevatedOffset")
        == pytest.approx(-window.property("cardElevate"))
    )

    QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=QPoint(100, 360))
    assert window.property("elevatedPressed")
    QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=QPoint(100, 360))
    assert _wait_for(lambda: clicks == [True])
    assert not window.property("elevatedPressed")

    window.hide()
    _pump()
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_example_card_creates_neo_shadow_only_for_neo_skin(card_scene):
    from prismqml.python.core.theme import Skin, ThemeManager

    window, warnings, windows_before = card_scene
    example_card = window.findChild(QQuickItem, "exampleCard")
    manager = ThemeManager()
    original_skin = manager.getSkin()

    try:
        manager.setSkin(Skin.FLUENT)
        assert _wait_for(lambda: _neo_shadows(example_card) == [])

        manager.setSkin(Skin.NEOBRUTALISM)
        assert _wait_for(lambda: len(_neo_shadows(example_card)) == 1)

        manager.setSkin(Skin.FLUENT)
        assert _wait_for(lambda: _neo_shadows(example_card) == [])
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        manager.setSkin(original_skin)


def test_card_neo_shadow_lifecycle_baseline(card_scene):
    """Lock Card skin shadow counts and full-window pixels before lazy loading.

    延迟加载前固化 Card 皮肤阴影对象数与整窗像素。
    """
    from prismqml.python.core.theme import Skin, ThemeManager

    window, warnings, windows_before = card_scene
    manager = ThemeManager()
    original_skin = manager.getSkin()
    cards = [
        window.findChild(QQuickItem, name)
        for name in (
            "fixedCard",
            "tallCard",
            "shortCard",
            "headerCard",
            "noPaddingHeader",
            "elevatedCard",
        )
    ]
    assert all(cards)
    try:
        window.show()
        assert _wait_for(window.isExposed)
        QTest.mouseMove(window, QPoint(670, 550))

        manager.setSkin(Skin.FLUENT)
        _pump(int(window.property("mediumDuration")) + 50)
        assert all(len(_neo_shadows(card)) == 1 for card in cards)
        assert all(not _neo_shadows(card)[0].isVisible() for card in cards)
        fluent_image = _stable_window_image(window)

        manager.setSkin(Skin.NEOBRUTALISM)
        _pump(int(window.property("mediumDuration")) + 50)
        assert all(len(_neo_shadows(card)) == 1 for card in cards)
        assert all(_neo_shadows(card)[0].isVisible() for card in cards)
        neo_image = _stable_window_image(window)
        assert neo_image != fluent_image

        manager.setSkin(Skin.FLUENT)
        _pump(int(window.property("mediumDuration")) + 50)
        assert all(len(_neo_shadows(card)) == 1 for card in cards)
        assert _stable_window_image(window) == fluent_image

        manager.setSkin(Skin.NEOBRUTALISM)
        _pump(int(window.property("mediumDuration")) + 50)
        assert all(len(_neo_shadows(card)) == 1 for card in cards)
        assert _stable_window_image(window) == neo_image
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        manager.setSkin(original_skin)
        window.hide()
        _pump()


def test_example_card_creates_component_label_only_for_text(card_scene):
    window, warnings, windows_before = card_scene
    example_card = window.findChild(QQuickItem, "exampleCard")

    def component_labels():
        return [
            child
            for child in _descendants(example_card)
            if child.metaObject().indexOfProperty("text") >= 0
            and child.property("text") == "Engine component"
        ]

    assert component_labels() == []
    assert example_card.setProperty("componentName", "Engine component")
    assert _wait_for(lambda: len(component_labels()) == 1)
    assert example_card.setProperty("componentName", "")
    assert _wait_for(lambda: component_labels() == [])
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_card_source_follows_conventions():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
