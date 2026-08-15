# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Window-level hyperlink cursor contracts. 窗口级超链接光标合同。"""

from __future__ import annotations

import math
from pathlib import Path

from PySide6.QtCore import (
    Q_ARG,
    Q_RETURN_ARG,
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QPoint,
    QPointF,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "hyperlink-cursor-contracts.qml")
)
MARKDOWN_URL = "https://example.invalid/markdown-link"
TEXT_EDIT_URL = "prismtest://textedit/link"
UPDATE_URL = "prismtest://update/link"


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1600) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 30
    return predicate()


def _descendants(root):
    result = []
    pending = list(root.children())
    seen = set()
    while pending:
        child = pending.pop()
        identity = id(child)
        if identity in seen:
            continue
        seen.add(identity)
        result.append(child)
        pending.extend(child.children())
        if isinstance(child, QQuickItem):
            pending.extend(child.childItems())
    return result


def _create_scene(source: bytes):
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(source, SCENE_URL)
    for _ in range(60):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    window.requestActivate()
    assert _wait_for(window.isActive)
    return engine, component, window, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump()


def _move_to_item(window: QQuickWindow, item: QQuickItem, local_point: QPointF) -> None:
    QTest.mouseMove(window, QPoint(window.width() - 2, window.height() - 2))
    _pump()
    scene_point = item.mapToItem(window.contentItem(), local_point)
    QTest.mouseMove(window, QPoint(round(scene_point.x()), round(scene_point.y())))
    _pump(80)


def _assert_pointing_cursor(window: QQuickWindow) -> None:
    assert window.cursor().shape() == Qt.CursorShape.PointingHandCursor


def _link_at(item: QQuickItem, x: float, y: float) -> str:
    return QMetaObject.invokeMethod(
        item,
        "linkAt",
        Qt.ConnectionType.DirectConnection,
        Q_RETURN_ARG(str),
        Q_ARG(float, x),
        Q_ARG(float, y),
    )


def _find_link_target(root, expected_url: str):
    for item in _descendants(root):
        if not isinstance(item, QQuickItem):
            continue
        meta_object = item.metaObject()
        has_link_at = any(
            bytes(meta_object.method(index).name()) == b"linkAt"
            for index in range(meta_object.methodOffset(), meta_object.methodCount())
        )
        if not has_link_at:
            continue
        width = max(1, math.ceil(item.width()))
        height = max(1, math.ceil(item.height()))
        for y in range(0, height, 2):
            for x in range(0, width, 2):
                if _link_at(item, float(x), float(y)) == expected_url:
                    return item, QPointF(x, y)
    raise AssertionError(f"link target not found: {expected_url}")


LABEL_HOVER_SCENE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 360
    height: 140
    visible: true

    Label {
        objectName: "labelLink"
        x: 24
        y: 32
        text: "Open documentation"
        type: Enums.label.type_hyperlink
        url: "https://example.invalid/label"
    }
}
"""


DIALOG_SCENE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 640
    height: 420
    visible: true

    component ConsumerDialog: DialogBoxCore {
        Column {
            width: 440
            spacing: 16

            Label {
                objectName: "dialogLink"
                text: "PrismQML"
                type: Enums.label.type_hyperlink
                url: "https://example.invalid/prismqml"
            }

            ButtonCore {
                objectName: "dialogHyperlinkButton"
                width: 120
                height: 32
                text: "Learn more"
                style: Enums.button.style_hyperlink
            }
        }
    }

    ConsumerDialog {
        id: dialog
        objectName: "dialog"
        anchors.fill: parent

        Component.onCompleted: open()
    }
}
"""


MARKDOWN_SCENE = f"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {{
    width: 620
    height: 240
    visible: true

    MarkdownView {{
        objectName: "markdownView"
        x: 24
        y: 24
        width: 560
        markdown: "Read [PrismQML]({MARKDOWN_URL}) documentation."
    }}
}}
""".encode("utf-8")


TEXT_EDIT_SCENE = f"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {{
    width: 620
    height: 240
    visible: true

    TextEdit {{
        objectName: "browser"
        x: 24
        y: 24
        width: 560
        height: 120
        multilineType: Enums.input.multiline_browser
        text: "<b>PrismQML</b> <a href='{TEXT_EDIT_URL}'>documentation</a>"
        openExternalLinks: false
    }}
}}
""".encode("utf-8")


UPDATE_SCENE = f"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {{
    width: 720
    height: 520
    visible: true

    UpdateDialog {{
        objectName: "updateDialog"
        version: "1.2.3.4"
        currentVersion: "1.2.3.3"
        notes: "Read [release notes]({UPDATE_URL}) before installing."
        Component.onCompleted: open()
    }}
}}
""".encode("utf-8")


MASKED_DIALOG_SCENE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 640
    height: 420
    visible: true

    component ConsumerMaskedDialog: MaskedDialog {
        Label {
            objectName: "maskedDialogLink"
            text: "Masked link"
            type: Enums.label.type_hyperlink
            url: "https://example.invalid/masked"
        }
    }

    ConsumerMaskedDialog {
        id: dialog
        objectName: "maskedDialog"
        Component.onCompleted: open()
    }
}
"""


DRAWER_SCENE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 640
    height: 420
    visible: true

    component ConsumerDrawer: Drawer {
        drawerWidth: 280

        Label {
            objectName: "drawerLink"
            text: "Drawer link"
            type: Enums.label.type_hyperlink
            url: "https://example.invalid/drawer"
        }
    }

    ConsumerDrawer {
        objectName: "drawer"
        Component.onCompleted: open()
    }
}
"""


SETTINGS_CARD_SCENE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 520
    height: 240
    visible: true

    SettingsCard {
        objectName: "settingsCard"
        x: 24
        y: 24
        width: 460
        title: "Documentation"
        content: "Read the online guide"
        type: Enums.settingCard.type_hyperlink
        linkText: "Open docs"
        url: "https://example.invalid/settings"
    }
}
"""


def test_dialog_content_preserves_hyperlink_cursors(qapp) -> None:
    engine, component, window, warnings = _create_scene(DIALOG_SCENE)
    try:
        dialog = window.findChild(QQuickItem, "dialog")
        link = window.findChild(QQuickItem, "dialogLink")
        hyperlink_button = window.findChild(QQuickItem, "dialogHyperlinkButton")
        assert dialog is not None
        assert link is not None
        assert hyperlink_button is not None

        for draggable in (False, True):
            assert dialog.setProperty("draggable", draggable)
            _move_to_item(window, link, link.boundingRect().center())
            _assert_pointing_cursor(window)
            _move_to_item(
                window, hyperlink_button, hyperlink_button.boundingRect().center()
            )
            _assert_pointing_cursor(window)

        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_label_hyperlink_hover_surface_is_scoped_to_hover(qapp) -> None:
    engine, component, window, warnings = _create_scene(LABEL_HOVER_SCENE)
    try:
        label = window.findChild(QQuickItem, "labelLink")
        surface = window.findChild(QQuickItem, "hyperlinkHoverSurface")
        assert label is not None
        assert surface is not None
        assert surface.opacity() == 0

        _move_to_item(window, label, label.boundingRect().center())
        assert label.property("hovered") is True
        _pump(140)
        assert surface.opacity() > 0.95
        assert surface.scale() > 0.99

        QTest.mouseMove(window, QPoint(window.width() - 2, window.height() - 2))
        _pump(140)
        assert label.property("hovered") is False
        assert surface.opacity() < 0.05
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_markdown_view_link_uses_pointing_cursor(qapp) -> None:
    engine, component, window, warnings = _create_scene(MARKDOWN_SCENE)
    try:
        item, point = _find_link_target(window, MARKDOWN_URL)
        _move_to_item(window, item, point)
        _assert_pointing_cursor(window)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_text_edit_browser_link_uses_pointing_cursor(qapp) -> None:
    engine, component, window, warnings = _create_scene(TEXT_EDIT_SCENE)
    try:
        item, point = _find_link_target(window, TEXT_EDIT_URL)
        _move_to_item(window, item, point)
        _assert_pointing_cursor(window)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_update_dialog_markdown_link_uses_pointing_cursor(qapp) -> None:
    engine, component, window, warnings = _create_scene(UPDATE_SCENE)
    try:
        item, point = _find_link_target(window, UPDATE_URL)
        _move_to_item(window, item, point)
        _assert_pointing_cursor(window)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_masked_dialog_content_preserves_hyperlink_cursor(qapp) -> None:
    engine, component, window, warnings = _create_scene(MASKED_DIALOG_SCENE)
    try:
        dialog = window.findChild(QQuickItem, "maskedDialog")
        link = window.findChild(QQuickItem, "maskedDialogLink")
        assert dialog is not None
        assert link is not None

        for draggable in (False, True):
            assert dialog.setProperty("draggable", draggable)
            _move_to_item(window, link, link.boundingRect().center())
            _assert_pointing_cursor(window)

        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_drawer_content_preserves_hyperlink_cursor(qapp) -> None:
    engine, component, window, warnings = _create_scene(DRAWER_SCENE)
    try:
        link = window.findChild(QQuickItem, "drawerLink")
        assert link is not None
        _pump(400)
        _move_to_item(window, link, link.boundingRect().center())
        _assert_pointing_cursor(window)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_settings_card_hyperlink_uses_pointing_cursor(qapp) -> None:
    engine, component, window, warnings = _create_scene(SETTINGS_CARD_SCENE)
    try:
        hyperlink_button = next(
            item
            for item in _descendants(window)
            if isinstance(item, QQuickItem)
            and item.metaObject().indexOfProperty("text") >= 0
            and item.metaObject().indexOfProperty("style") >= 0
            and item.property("text") == "Open docs"
        )
        _move_to_item(
            window, hyperlink_button, hyperlink_button.boundingRect().center()
        )
        _assert_pointing_cursor(window)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
