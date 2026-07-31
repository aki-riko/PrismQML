# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Markdown streaming model regressions. Markdown 流式模型回归测试。"""

import json

import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QObject,
    QTimer,
    QUrl,
)
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression

from prismqml import register_types


PROBE_SOURCE = b"""import QtQuick
import PrismQML
MarkdownView { width: 600 }
"""
BLOCK_CASES = (
    ("", []),
    ("alpha\nbeta", [{"kind": "text", "content": "alpha\nbeta"}]),
    (
        "paragraph\n```py\nx = 1\n```\ntail",
        [
            {"kind": "text", "content": "paragraph"},
            {"kind": "code", "language": "py", "content": "x = 1"},
            {"kind": "text", "content": "tail"},
        ],
    ),
    ("```py", []),
    ("```py\n", [{"kind": "code", "language": "py", "content": ""}]),
    (
        "```c++\nx",
        [{"kind": "text", "content": "```c++\nx"}],
    ),
    (
        "before\n```\na\n",
        [
            {"kind": "text", "content": "before"},
            {"kind": "code", "language": "", "content": "a\n"},
        ],
    ),
)


def _pump(milliseconds: int = 0) -> None:
    if milliseconds <= 0:
        QCoreApplication.processEvents()
        return
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_probe() -> tuple[QQmlEngine, QQmlComponent, QQuickItem]:
    engine = QQmlEngine()
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(PROBE_SOURCE, QUrl("inline:markdown-stream-contract.qml"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert not component.isError(), [error.toString() for error in component.errors()]
    probe = component.create(engine.rootContext())
    assert isinstance(probe, QQuickItem), [
        error.toString() for error in component.errors()
    ]
    return engine, component, probe


def _delete_probe(keep: tuple[QQmlEngine, QQmlComponent, QQuickItem]) -> None:
    engine, component, probe = keep
    probe.deleteLater()
    component.deleteLater()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def _evaluate_blocks(probe: QQuickItem) -> list[dict]:
    expression = QQmlExpression(
        QQmlEngine.contextForObject(probe), probe, "JSON.stringify(_blocks)"
    )
    result = expression.evaluate()
    assert not expression.hasError(), expression.error().toString()
    if isinstance(result, tuple):
        result, is_undefined = result
        assert is_undefined is False
    return json.loads(result)


def _evaluate_block_model(probe: QQuickItem) -> list[dict]:
    matches = [
        child
        for child in probe.findChildren(QObject)
        if "QQmlListModel" in child.metaObject().className()
    ]
    assert len(matches) == 1, [
        child.metaObject().className() for child in probe.findChildren(QObject)
    ]
    model = matches[0]
    source = """(function() {
        var rows = []
        for (var index = 0; index < count; ++index) {
            var row = get(index)
            rows.push({
                kind: row.kind,
                content: row.content,
                language: row.language
            })
        }
        return JSON.stringify(rows)
    })()"""
    expression = QQmlExpression(QQmlEngine.contextForObject(model), model, source)
    result = expression.evaluate()
    assert not expression.hasError(), expression.error().toString()
    if isinstance(result, tuple):
        result, is_undefined = result
        assert is_undefined is False
    return json.loads(result)


def _normalized_blocks(blocks: list[dict]) -> list[dict]:
    return [
        {
            "kind": block["kind"],
            "content": block["content"],
            "language": block.get("language", ""),
        }
        for block in blocks
    ]


def _walk_items(root: QQuickItem):
    yield root
    for child in root.childItems():
        yield from _walk_items(child)


def _only_text_item(probe: QQuickItem) -> QQuickItem:
    matches = [
        item
        for item in _walk_items(probe)
        if item.metaObject().indexOfProperty("text") >= 0
    ]
    assert len(matches) == 1, [
        (item.metaObject().className(), item.property("text")) for item in matches
    ]
    return matches[0]


def _loader_items(probe: QQuickItem) -> list[QQuickItem]:
    matches = [
        item
        for item in _walk_items(probe)
        if "QQuickLoader" in item.metaObject().className()
        and item.metaObject().indexOfProperty("kind") >= 0
        and item.metaObject().indexOfProperty("content") >= 0
        and item.metaObject().indexOfProperty("language") >= 0
    ]
    return matches


def _only_loader_item(probe: QQuickItem) -> QQuickItem:
    matches = _loader_items(probe)
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def test_markdown_block_parser_contract_is_unchanged(qapp):
    keep = _create_probe()
    try:
        probe = keep[-1]
        property_index = probe.metaObject().indexOfProperty("_blocks")
        assert property_index >= 0
        meta_property = probe.metaObject().property(property_index)
        assert meta_property.isWritable() is False
        for markdown, expected in BLOCK_CASES:
            assert probe.setProperty("markdown", markdown)
            _pump()
            assert _evaluate_blocks(probe) == expected
            assert _evaluate_block_model(probe) == _normalized_blocks(expected)
    finally:
        _delete_probe(keep)


def test_plain_text_append_reuses_loader_and_rebuilds_render_item(qapp):
    keep = _create_probe()
    try:
        probe = keep[-1]
        assert probe.setProperty("markdown", "alpha")
        _pump()
        first_loader = _only_loader_item(probe)
        first = _only_text_item(probe)
        first_loader_pointer = shiboken6.getCppPointer(first_loader)[0]
        first_destroyed = []
        first.destroyed.connect(lambda *_: first_destroyed.append(True))

        assert probe.setProperty("markdown", "alpha beta\nsecond")
        _pump()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        second_loader = _only_loader_item(probe)
        second = _only_text_item(probe)
        second_loader_pointer = shiboken6.getCppPointer(second_loader)[0]

        assert second.property("text") == "alpha beta\nsecond"
        assert second_loader_pointer == first_loader_pointer
        assert first_destroyed == [True]
    finally:
        _delete_probe(keep)


def test_tail_append_preserves_completed_block_render_items(qapp):
    keep = _create_probe()
    try:
        probe = keep[-1]
        prefix = "intro\n```py\nx = 1\n```\n"
        assert probe.setProperty("markdown", prefix + "tail")
        _pump()
        first_loaders = _loader_items(probe)
        assert len(first_loaders) == 3
        first_loader_pointers = [
            shiboken6.getCppPointer(loader)[0] for loader in first_loaders
        ]
        first_items = [loader.property("item") for loader in first_loaders]
        first_item_pointers = [shiboken6.getCppPointer(item)[0] for item in first_items]
        tail_destroyed = []
        first_items[2].destroyed.connect(lambda *_: tail_destroyed.append(True))

        assert probe.setProperty("markdown", prefix + "tail grows")
        _pump()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        second_loaders = _loader_items(probe)
        assert [
            shiboken6.getCppPointer(loader)[0] for loader in second_loaders
        ] == first_loader_pointers
        second_item_pointers = [
            shiboken6.getCppPointer(loader.property("item"))[0]
            for loader in second_loaders
        ]
        assert second_item_pointers[:2] == first_item_pointers[:2]
        assert tail_destroyed == [True]
    finally:
        _delete_probe(keep)
