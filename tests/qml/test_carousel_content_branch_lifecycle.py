# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Carousel content branch lifecycle regressions. 轮播内容分支生命周期回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "carousel-content-branch-lifecycle.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    readonly property int peekEffect: Enums.carousel.effect_peek
    readonly property int slideEffect: Enums.carousel.effect_slide

    width: 360
    height: 220
    visible: true

    Carousel {
        id: carousel
        objectName: "carousel"
        x: 20
        y: 20
        width: 320
        height: 180
        showIndicator: false
        showNavButtons: false
        model: [
            { color: "#d83b01", text: "A" },
            { color: "#107c10", text: "B" },
            { color: "#005fb8", text: "C" }
        ]
    }
}
"""
IMAGE_URL = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8A"
    "AQUBAScY42YAAAAASUVORK5CYII="
)
TEXT_MODEL = [
    {"color": "#d83b01", "text": "A"},
    {"color": "#107c10", "text": "B"},
    {"color": "#005fb8", "text": "C"},
]
IMAGE_MODEL = [IMAGE_URL, IMAGE_URL, IMAGE_URL]


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1600) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _visual_descendants(root: QQuickItem) -> list[QQuickItem]:
    result = []
    pending = list(root.childItems())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.childItems())
    return result


def _content(carousel: QQuickItem) -> QQuickItem:
    matches = [
        child
        for child in carousel.findChildren(QObject)
        if isinstance(child, QQuickItem)
        and child.metaObject().indexOfProperty("isPeek") >= 0
        and child.metaObject().indexOfProperty("borderRadius") >= 0
    ]
    assert len(matches) == 1
    return matches[0]


def _branch_counts(content: QQuickItem) -> tuple[int, int]:
    descendants = _visual_descendants(content)
    image_count = sum(
        child.metaObject().className().startswith("QQuickImage")
        for child in descendants
    )
    label_count = sum(
        child.metaObject().indexOfProperty("type") >= 0
        and child.metaObject().indexOfProperty("text") >= 0
        for child in descendants
    )
    return image_count, label_count


def _create_scene(effect_property: str):
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
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    window.requestActivate()
    assert _wait_for(window.isActive)
    carousel = window.findChild(QQuickItem, "carousel")
    assert carousel is not None
    carousel.setProperty("effect", window.property(effect_property))
    content = _content(carousel)
    assert _wait_for(lambda: _branch_counts(content)[1] > 0)
    return engine, component, window, carousel, content, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump()


@pytest.mark.parametrize("effect_property", ["peekEffect", "slideEffect"])
def test_carousel_instantiates_only_the_active_builtin_content_branch(
    qapp, effect_property
):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, carousel, content, warnings = _create_scene(
        effect_property
    )
    try:
        assert _branch_counts(content)[0] == 0

        carousel.setProperty("model", IMAGE_MODEL)
        assert _wait_for(lambda: _branch_counts(content)[0] > 0)
        assert _branch_counts(content)[1] == 0

        carousel.setProperty("model", TEXT_MODEL)
        assert _wait_for(lambda: _branch_counts(content)[1] > 0)
        assert _branch_counts(content)[0] == 0
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
        assert [
            top
            for top in QGuiApplication.topLevelWindows()
            if top.isVisible()
            and not any(top is existing for existing in windows_before)
        ] == []
