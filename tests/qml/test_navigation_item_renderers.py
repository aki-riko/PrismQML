# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Navigation item icon renderer lifecycle contracts. 导航项图标渲染器生命周期合同。"""

from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "navigation-item-renderers.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 640
    height: 240
    visible: true

    Row {
        Column {
            NavigationViewItem {
                objectName: "viewSvg"
                width: 240
                text: "SVG"
                icon: Qt.resolvedUrl("../../prismqml/PrismQML/controls/icons/fluent/Settings.svg")
            }
            NavigationViewItem {
                objectName: "viewAvatar"
                width: 240
                text: "Avatar"
                icon: Qt.resolvedUrl("../../examples/resources/image/avatar/avatar.png")
            }
            NavigationViewItem {
                objectName: "viewText"
                width: 240
                text: "Text"
                icon: "A"
            }
        }
        Row {
            NavigationBarItem {
                objectName: "barSvg"
                text: "SVG"
                icon: Qt.resolvedUrl("../../prismqml/PrismQML/controls/icons/fluent/Settings.svg")
            }
            NavigationBarItem {
                objectName: "barAvatar"
                text: "Avatar"
                icon: Qt.resolvedUrl("../../examples/resources/image/avatar/avatar.png")
            }
            NavigationBarItem {
                objectName: "barText"
                text: "Text"
                icon: "A"
            }
        }
    }
}
"""


def _pump(milliseconds: int = 100) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _descendants(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _descendants(child)


def _image_items(item: QQuickItem):
    return [
        child
        for child in _descendants(item)
        if child.metaObject().indexOfProperty("fillMode") >= 0
    ]


def _enabled_mask_count(item: QQuickItem) -> int:
    return sum(
        bool(child.property("maskEnabled"))
        for child in _descendants(item)
        if child.metaObject().indexOfProperty("maskEnabled") >= 0
    )


def _has_text_icon(item: QQuickItem, text: str) -> bool:
    return any(
        child.metaObject().indexOfProperty("text") >= 0
        and child.property("text") == text
        for child in _descendants(item)
    )


def test_navigation_items_load_only_the_active_icon_renderer(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
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
    try:
        _pump()
        for prefix in ("view", "bar"):
            svg_item = window.findChild(QQuickItem, prefix + "Svg")
            avatar_item = window.findChild(QQuickItem, prefix + "Avatar")
            text_item = window.findChild(QQuickItem, prefix + "Text")
            assert len(_image_items(svg_item)) == 1
            assert len(_image_items(avatar_item)) == 1
            assert _image_items(text_item) == []
            assert _enabled_mask_count(svg_item) == 0
            assert _enabled_mask_count(avatar_item) == 1
            assert _has_text_icon(text_item, "A")

            assert svg_item.setProperty("icon", "A")
            _pump()
            assert _image_items(svg_item) == []
            assert _has_text_icon(svg_item, "A")

            avatar_source = QUrl.fromLocalFile(
                str(ROOT / "examples" / "resources" / "image" / "avatar" / "avatar.png")
            ).toString()
            assert svg_item.setProperty("icon", avatar_source)
            _pump()
            assert len(_image_items(svg_item)) == 1
            assert _enabled_mask_count(svg_item) == 1
        assert warnings == []
        assert [
            candidate
            for candidate in QGuiApplication.topLevelWindows()
            if candidate.isVisible()
            and candidate not in windows_before
            and candidate is not window
        ] == []
    finally:
        window.close()
        window.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before
