# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Rich text block trimming, columns and overflow runtime contracts.

富文本块裁剪、多列与溢出运行时合同。
"""

from hashlib import sha256
from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QTimer,
    QUrl,
)
from PySide6.QtGui import QImage
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlEngine, QQmlExpression
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "rich-text-block-overflow.qml")
)

LONG_LINE = "Alpha bravo charlie delta echo foxtrot golf hotel india juliet"
LONG_BLOCK = " ".join([LONG_LINE] * 12) + " " + "Z" * 120

SCENE_SOURCE = f"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {{
    id: root
    objectName: "window"
    width: 640
    height: 420
    visible: true

    readonly property int elideNone: Text.ElideNone
    readonly property int elideRight: Text.ElideRight
    readonly property int wordWrap: Text.WordWrap
    readonly property int wrapAnywhere: Text.WrapAnywhere
    readonly property int trimNone: Enums.label.trim_none
    readonly property int trimCharacter: Enums.label.trim_character_ellipsis
    readonly property int trimWord: Enums.label.trim_word_ellipsis
    readonly property int trimClip: Enums.label.trim_clip

    TextEdit {{
        id: browser
        objectName: "browser"
        x: 20
        y: 20
        width: 200
        height: 100
        multilineType: Enums.input.multiline_browser
        wrapMode: TextEdit.WordWrap
        text: "{LONG_BLOCK}"
    }}

    TextEdit {{
        id: shortBrowser
        objectName: "shortBrowser"
        x: 20
        y: 140
        width: 200
        height: 100
        multilineType: Enums.input.multiline_browser
        text: "short"
    }}

    TextEdit {{
        id: tallBrowser
        objectName: "tallBrowser"
        x: 20
        y: 260
        width: 200
        height: 100
        multilineType: Enums.input.multiline_browser
        text: "{LONG_BLOCK}"
    }}

    TextEdit {{
        id: columnBrowser
        objectName: "columnBrowser"
        x: 300
        y: 20
        width: 300
        height: 120
        multilineType: Enums.input.multiline_browser
        text: "{LONG_BLOCK}"
    }}

    TextEdit {{
        id: plainBlock
        objectName: "plainBlock"
        x: 300
        y: 160
        width: 200
        height: 80
        wrapMode: TextEdit.WordWrap
        text: "{LONG_BLOCK}"
    }}
}}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 30
    return predicate()


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE.encode("utf-8"), SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    window.requestActivate()
    assert _wait_for(window.isExposed)
    _pump(60)
    return engine, component, window, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump(1)


def _item(window, name) -> QQuickItem:
    item = window.findChild(QQuickItem, name)
    assert item is not None, name
    return item


def _part(control: QQuickItem, name: str) -> QQuickItem:
    item = control.findChild(QQuickItem, name)
    assert item is not None, name
    return item


def _qml_value(item: QQuickItem, expression: str):
    expr = QQmlExpression(QQmlEngine.contextForObject(item), item, expression)
    result = expr.evaluate()
    assert not expr.hasError(), expr.error().toString()
    if isinstance(result, tuple):
        result = result[0]
    return result


def _native_editor(control: QQuickItem) -> QQuickItem:
    matches = [
        child
        for child in control.findChildren(QQuickItem)
        if child.metaObject().className().startswith("QQuickTextEdit")
        and child.metaObject().indexOfProperty("textFormat") >= 0
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _visual_descendants(root: QQuickItem):
    result = []
    pending = list(root.childItems())
    while pending:
        item = pending.pop()
        result.append(item)
        pending.extend(item.childItems())
    return result


def _stable_image_hash(window: QQuickWindow) -> str:
    previous = QImage()
    stable = 0
    for _ in range(40):
        current = window.grabWindow()
        assert not current.isNull()
        if current == previous:
            stable += 1
            if stable == 3:
                rgba = current.convertToFormat(QImage.Format.Format_RGBA8888)
                return sha256(bytes(rgba.constBits())).hexdigest()
        else:
            stable = 0
        previous = current
        _pump(20)
    raise AssertionError("window frames never stabilised")


def test_default_single_column_presentation_is_untouched(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        browser = _item(window, "browser")
        loader = _part(browser, "textEditColumnsLoader")
        trimming = _part(browser, "textEditTrimmingLoader")
        assert loader.property("active") is False
        assert trimming.property("active") is False
        assert browser.property("columnCount") == 1
        assert browser.property("textTrimming") == window.property("trimNone")
        editor = _native_editor(browser)
        assert editor.property("text") == browser.property("text")
        classic = [
            child
            for child in browser.childItems()
            if child.metaObject().indexOfProperty("contentY") >= 0
            and child.metaObject().indexOfProperty("boundsBehavior") >= 0
        ]
        assert len(classic) == 1
        assert classic[0].property("visible") is True
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_text_trimming_swaps_presentation_and_changes_pixels(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        browser = _item(window, "browser")
        trimming = _part(browser, "textEditTrimmingLoader")
        plain_hash = _stable_image_hash(window)

        browser.setProperty("textTrimming", window.property("trimCharacter"))
        assert _wait_for(lambda: trimming.property("active"))
        trim_view = trimming.property("item")
        assert trim_view is not None
        label = _part(trim_view, "richTextTrimLabel")
        assert _qml_value(label, "elide") == window.property("elideRight")
        assert _qml_value(label, "wrapMode") == window.property("wrapAnywhere")
        assert _wait_for(lambda: trim_view.property("hasOverflow") is True)
        assert browser.property("hasOverflowContent") is True
        trimmed_hash = _stable_image_hash(window)
        assert trimmed_hash != plain_hash

        browser.setProperty("textTrimming", window.property("trimWord"))
        _pump(60)
        assert _qml_value(
            _part(trimming.property("item"), "richTextTrimLabel"), "wrapMode"
        ) == window.property("wordWrap")
        word_hash = _stable_image_hash(window)
        assert word_hash != trimmed_hash

        browser.setProperty("textTrimming", window.property("trimClip"))
        assert _wait_for(lambda: not trimming.property("active"))
        clip_hash = _stable_image_hash(window)
        assert clip_hash != trimmed_hash
        assert clip_hash == plain_hash

        browser.setProperty("textTrimming", window.property("trimNone"))
        _pump(60)
        assert trimming.property("active") is False
        assert _stable_image_hash(window) == plain_hash
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_has_overflow_content_tracks_the_viewport(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        short_browser = _item(window, "shortBrowser")
        tall_browser = _item(window, "tallBrowser")
        assert short_browser.property("hasOverflowContent") is False
        assert tall_browser.property("hasOverflowContent") is True

        tall_browser.setProperty("height", 2000)
        _pump(60)
        assert tall_browser.property("hasOverflowContent") is False
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_plain_text_block_clamps_to_the_viewport(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        block = _item(window, "plainBlock")
        trimming = _part(block, "textEditTrimmingLoader")
        assert trimming.property("active") is False

        block.setProperty("textTrimming", window.property("trimWord"))
        assert _wait_for(lambda: trimming.property("active"))
        trim_view = trimming.property("item")
        assert _wait_for(lambda: trim_view.property("truncated") is True)
        assert block.property("hasOverflowContent") is True
        # The clamped label is shorter than the natural layout 裁剪标签短于自然排版
        label = _part(trim_view, "richTextTrimLabel")
        assert label.property("contentHeight") < trim_view.property("naturalHeight")
        assert trim_view.property("_maxLines") >= 1

        block.setProperty("textTrimming", window.property("trimNone"))
        assert _wait_for(lambda: not trimming.property("active"))
        assert block.property("hasOverflowContent") is True
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_multi_column_creates_one_viewport_per_column(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        browser = _item(window, "columnBrowser")
        loader = _part(browser, "textEditColumnsLoader")
        assert loader.property("active") is False
        assert browser.findChild(QQuickItem, "textEditColumnsLoader") is not None

        browser.setProperty("columnCount", 3)
        assert _wait_for(lambda: loader.property("active"))
        columns = loader.property("item")
        assert columns is not None
        assert columns.property("_columnCount") == 3

        viewports = [
            child
            for child in _visual_descendants(columns)
            if child.metaObject().indexOfProperty("clip") >= 0
            and child.property("clip")
        ]
        assert len(viewports) == 3
        # Every viewport shows the same document, sliced by one column height
        # 每个视口展示同一份文档, 按一列高度切分
        editors = [
            child
            for child in _visual_descendants(columns)
            if child.metaObject().className().startswith("QQuickTextEdit")
            and child.property("text") == browser.property("text")
        ]
        assert len(editors) == 4  # 1 measuring editor + 3 viewports 1 个测量 + 3 个视口
        widths = sorted(round(item.width()) for item in viewports)
        assert widths[0] == widths[-1]

        # The classic viewport steps aside while columns own the area
        # 多列接管区域时经典视口让位
        classic = [
            child
            for child in browser.childItems()
            if child.metaObject().indexOfProperty("contentY") >= 0
            and child.metaObject().indexOfProperty("boundsBehavior") >= 0
        ]
        assert len(classic) == 1
        assert classic[0].property("visible") is False
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_multi_column_overflow_and_single_column_fallback(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        browser = _item(window, "columnBrowser")
        loader = _part(browser, "textEditColumnsLoader")

        browser.setProperty("columnCount", 3)
        assert _wait_for(lambda: loader.property("active"))
        columns = loader.property("item")
        assert _wait_for(lambda: columns.property("_textHeight") > 0)
        assert columns.property("hasOverflow") is True
        assert browser.property("hasOverflowContent") is True

        browser.setProperty("columnCount", 1)
        assert _wait_for(lambda: not loader.property("active"))
        assert browser.property("hasOverflowContent") is True
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
