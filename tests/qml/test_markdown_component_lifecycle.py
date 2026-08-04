# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Markdown block component lifecycle regressions. Markdown 块组件生命周期回归。"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(
    os.environ.get("PRISMQML_TEST_ROOT", Path(__file__).resolve().parents[2])
).resolve()
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "markdown-component-lifecycle.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 680
    height: 520
    visible: true
    color: Enums.backgroundColor

    MarkdownView {
        objectName: "markdownView"
        x: 24
        y: 24
        width: 632
        markdown: "Intro **bold** paragraph.\\n```py\\nprint('one')\\n```\\nMiddle text.\\n```js\\nconsole.log('two')\\n```\\nTail text."
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1_000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
    ]


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
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    view = window.findChild(QQuickItem, "markdownView")
    assert view is not None
    ready = _wait_for(
        lambda: len(_block_loaders(view)) == 5
        and all(loader.property("item") is not None for loader in _block_loaders(view))
    )
    assert ready, {
        "loaders": [
            (
                loader.property("kind"),
                loader.property("content"),
                loader.property("item") is not None,
            )
            for loader in _block_loaders(view)
        ],
        "classes": [
            child.metaObject().className() for child in view.findChildren(QObject)
        ],
        "model_rows": [
            child.rowCount()
            for child in view.findChildren(QObject)
            if child.metaObject().className().startswith("QQmlListModel")
        ],
        "warnings": warnings,
    }
    return engine, component, window, view, warnings


def _dispose_scene(engine, component, window) -> None:
    window.setVisible(False)
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def _walk_items(root: QQuickItem):
    yield root
    for child in root.childItems():
        yield from _walk_items(child)


def _block_loaders(view: QQuickItem) -> list[QQuickItem]:
    return [
        item
        for item in _walk_items(view)
        if item.metaObject().className().startswith("QQuickLoader")
        and item.metaObject().indexOfProperty("kind") >= 0
        and item.metaObject().indexOfProperty("content") >= 0
    ]


def _component_count(owner: QObject) -> int:
    return sum(
        child.metaObject().className().startswith("QQmlComponent")
        for child in owner.findChildren(QObject)
        if child.parent() is owner
    )


def _object_count(view: QQuickItem) -> int:
    objects = {}
    for item in _walk_items(view):
        for obj in (item, *item.findChildren(QObject)):
            if shiboken6.isValid(obj):
                objects[shiboken6.getCppPointer(obj)[0]] = obj
    return len(objects)


def _image_hash(image: QImage) -> str:
    normalized = image.convertToFormat(QImage.Format.Format_RGBA8888)
    return hashlib.sha256(bytes(normalized.bits())).hexdigest()


def test_markdown_blocks_keep_rendering_while_component_count_is_measured(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, view, warnings = _create_scene()
    try:
        loaders = _block_loaders(view)
        assert [loader.property("kind") for loader in loaders] == [
            "text",
            "code",
            "text",
            "code",
            "text",
        ]
        assert [loader.property("content") for loader in loaders] == [
            "Intro **bold** paragraph.",
            "print('one')",
            "Middle text.",
            "console.log('two')",
            "Tail text.",
        ]
        assert [loader.property("language") for loader in loaders] == [
            "",
            "py",
            "",
            "js",
            "",
        ]

        loaded_items = [loader.property("item") for loader in loaders]
        assert [loaded_items[index].property("text") for index in (0, 2, 4)] == [
            "Intro **bold** paragraph.",
            "Middle text.",
            "Tail text.",
        ]
        assert [loaded_items[index].property("code") for index in (1, 3)] == [
            "print('one')",
            "console.log('two')",
        ]
        assert [loaded_items[index].property("language") for index in (1, 3)] == [
            "py",
            "js",
        ]

        per_loader_components = [_component_count(loader) for loader in loaders]
        object_count = _object_count(view)
        _pump()
        image = window.grabWindow()
        assert not image.isNull()
        image_hash = _image_hash(image)

        print(
            "MARKDOWN_COMPONENTS",
            f"per_loader={per_loader_components}",
            f"objects={object_count}",
            f"hash={image_hash}",
        )

        assert per_loader_components == [2, 2, 2, 2, 2]
        assert object_count == 142
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []
