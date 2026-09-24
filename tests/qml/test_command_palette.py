# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""CommandPalette contracts. 命令面板契约回归。"""

import time
from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QObject,
    QPoint,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import configure_qml_environment, register_types


SCENE_URL = QUrl.fromLocalFile(
    str(Path(__file__).resolve().parent / "command-palette.qml")
)

SCENE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"

    property string lastCommand: ""
    property int triggerCount: 0
    property var lastItem: null

    width: 820
    height: 620
    visible: true

    function setPaletteQuery(text) { palette.setQuery(text) }
    function openPalette() { palette.open() }
    function closePalette() { palette.close() }

    CommandPalette {
        id: palette
        objectName: "palette"
        shortcut: "Ctrl+K"
        placeholderText: "Type a command"
        hintText: "Up/Down navigate  Enter run  Esc close"
        items: [
            { key: "open-file", title: "Open File", subtitle: "File",
              section: "File", icon: Enums.iconPath + "Folder.svg" },
            { key: "save-file", title: "Save File", subtitle: "File",
              section: "File", icon: Enums.iconPath + "Document.svg" },
            { key: "toggle-theme", title: "Toggle Theme", subtitle: "View",
              section: "View", icon: Enums.iconPath + "Settings.svg" },
            { key: "open-doc", title: "Open Documents", subtitle: "Go",
              section: "Go", keywords: ["docs", "manual"],
              icon: Enums.iconPath + "Document.svg" }
        ]
        onCommandTriggered: (key, item) => {
            root.lastCommand = key
            root.lastItem = item
            root.triggerCount++
        }
    }
}
"""


def _pump(milliseconds: int = 12) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump(10)
        elapsed += 10
    return predicate()


def _create_scene(qapp):
    configure_qml_environment()
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE, SCENE_URL)
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    window.show()
    # Active focus needs an activated window; the offscreen platform honours it too
    # 活动焦点需要窗口被激活; 离屏平台同样遵循
    window.requestActivate()
    _pump(120)
    return engine, component, window, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump(20)


def _type_text(window, text: str) -> None:
    """Send one key event per character.

    QTest.keyClicks only accepts QWidget, so a QQuickWindow gets per-key events.
    QTest.keyClicks 只接受 QWidget, 因此对 QQuickWindow 逐键发送。
    """
    for character in text:
        QTest.keyClick(window, Qt.Key(ord(character.upper())))
        _pump(6)


def _result_list(window: QQuickWindow):
    """The palette's SearchResultList, located by its own properties.

    通过自身属性定位面板的结果列表。
    """
    palette = _palette(window)
    pending = list(palette.childItems())
    while pending:
        item = pending.pop(0)
        pending.extend(item.childItems())
        if (
            item.metaObject().indexOfProperty("hitCount") >= 0
            and item.metaObject().indexOfProperty("_itemCursor") >= 0
        ):
            return item
    raise AssertionError("palette result list not found")


def _palette(window: QQuickWindow):
    palette = window.findChild(QQuickItem, "palette")
    assert palette is not None
    return palette


def _search_edit(window: QQuickWindow):
    """The palette's search field, found through the visual tree.

    通过视觉树定位面板搜索框。
    """
    palette = _palette(window)
    pending = list(palette.childItems())
    while pending:
        item = pending.pop(0)
        pending.extend(item.childItems())
        if (
            item.metaObject().indexOfProperty("placeholderText") >= 0
            and item.metaObject().indexOfProperty("inputType") >= 0
        ):
            return item
    raise AssertionError("palette search field not found")


def test_palette_opens_takes_focus_and_closes(qapp):
    """Opening must show the modal, focus the search field, and close again.

    打开必须显示模态、把焦点收进搜索框，并且能再次关闭。
    """
    engine, component, window, warnings = _create_scene(qapp)
    try:
        palette = _palette(window)
        assert palette.property("isOpen") is False

        window.openPalette()
        assert _wait_for(lambda: palette.property("isOpen") is True)
        field = _search_edit(window)
        # Focus lands on the LineEdit's inner TextInput, so ask the control
        # 焦点落在 LineEdit 内部 TextInput 上, 因此问控件本身
        assert _wait_for(lambda: field.inputHasFocus()), (
            f"search field lost focus: open={palette.property('isOpen')} "
            f"visible={field.isVisible()} enabled={field.isEnabled()} "
            f"windowActive={window.isActive()}"
        )
        # The palette reparents to the window overlay when it opens
        # 打开时面板会重挂到窗口覆盖层
        assert palette.parentItem() is window.contentItem()
        assert field.property("placeholderText") == "Type a command"

        window.closePalette()
        assert _wait_for(lambda: palette.property("isOpen") is False)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_palette_filters_and_runs_the_highlighted_command(qapp):
    """Typing must filter the list, and Enter must run the top hit.

    输入必须过滤列表，回车必须执行当前命中项。
    """
    engine, component, window, warnings = _create_scene(qapp)
    try:
        palette = _palette(window)
        window.openPalette()
        assert _wait_for(lambda: palette.property("isOpen") is True)
        assert _wait_for(
            lambda: palette.property("resultCount") == 4
        ), f"unfiltered count: {palette.property('resultCount')}"

        # Typing must not race the focus hand-off 打字不能和焦点交接抢跑
        field = _search_edit(window)
        assert _wait_for(lambda: field.inputHasFocus())
        _type_text(window, "doc")

        assert _wait_for(
            lambda: str(palette.property("query")).lower() == "doc"
        ), f"typed query: {palette.property('query')!r}"
        assert _wait_for(lambda: palette.property("resultCount") == 1), (
            f"filtered count: {palette.property('resultCount')} "
            f"query={palette.property('query')!r}"
        )

        QTest.keyClick(window, Qt.Key.Key_Return)
        assert _wait_for(lambda: window.property("triggerCount") == 1)
        assert window.property("lastCommand") == "open-doc"
        assert palette.property("isOpen") is False
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_palette_keyboard_navigation_picks_the_next_hit(qapp):
    """Arrow keys must move the highlight before Enter runs it.

    方向键必须移动高亮项，回车再执行它。
    """
    engine, component, window, warnings = _create_scene(qapp)
    try:
        palette = _palette(window)
        window.openPalette()
        assert _wait_for(lambda: palette.property("resultCount") == 4)
        field = _search_edit(window)
        assert _wait_for(lambda: field.inputHasFocus())

        # Two discrete presses: each needs its own event-loop turn
        # 两次独立按键: 每次都要有自己的事件循环轮次
        results = _result_list(window)
        QTest.keyClick(window, Qt.Key.Key_Down)
        assert _wait_for(lambda: results.property("_itemCursor") == 1), (
            f"first Down left cursor at {results.property('_itemCursor')}"
        )
        QTest.keyClick(window, Qt.Key.Key_Down)
        assert _wait_for(lambda: results.property("_itemCursor") == 2), (
            f"second Down left cursor at {results.property('_itemCursor')}"
        )

        # A re-ranking that leaves the visible hits unchanged must not steal the
        # cursor: the host reads the list's implicit height, which re-runs the filter,
        # and an unconditional reset there silently undoes the arrows before Enter.
        # 不影响可见命中的重新排名不得夺走光标: 宿主会读列表隐式高度从而重跑过滤, 那里若
        # 无条件重置, 方向键会在回车前被静默撤销。
        results.setProperty("maxSuggestions", 10)
        _pump(60)
        assert results.property("hitCount") == 4, "the visible hit set changed"
        assert results.property("_itemCursor") == 2, (
            f"cursor stolen by a re-ranking: {results.property('_itemCursor')}"
        )

        QTest.keyClick(window, Qt.Key.Key_Return)
        assert _wait_for(lambda: window.property("triggerCount") == 1)
        # Third entry of the unfiltered list 未过滤列表的第 3 项
        assert window.property("lastCommand") == "toggle-theme"
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_palette_escape_and_scrim_click_dismiss(qapp):
    """Escape and a scrim click must both close the palette.

    Esc 与点击遮罩都必须关闭面板。
    """
    engine, component, window, warnings = _create_scene(qapp)
    try:
        palette = _palette(window)
        window.openPalette()
        assert _wait_for(lambda: palette.property("isOpen") is True)
        QTest.keyClick(window, Qt.Key.Key_Escape)
        assert _wait_for(lambda: palette.property("isOpen") is False)

        window.openPalette()
        assert _wait_for(lambda: palette.property("isOpen") is True)
        # Click near the bottom of the window: outside the panel, on the scrim
        # 点击窗口底部: 面板之外, 落在遮罩上
        QTest.mouseClick(
            window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
            QPoint(20, window.height() - 20),
        )
        assert _wait_for(lambda: palette.property("isOpen") is False)
        assert window.property("triggerCount") == 0
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_palette_shortcut_opens_it(qapp):
    """The configured shortcut must open the palette from the host window.

    配置的快捷键必须能从宿主窗口打开面板。
    """
    engine, component, window, warnings = _create_scene(qapp)
    try:
        palette = _palette(window)
        QTest.keyClick(window, Qt.Key.Key_K, Qt.KeyboardModifier.ControlModifier)
        assert _wait_for(lambda: palette.property("isOpen") is True), (
            "Ctrl+K did not open the palette"
        )
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
