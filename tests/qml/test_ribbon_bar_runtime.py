# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""RibbonBar runtime contracts. 功能区运行时合同。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QPointF,
    QTimer,
    Qt,
    QUrl,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
NAV_DIR = ROOT / "prismqml" / "PrismQML" / "navigation"
SOURCE_PATHS = (
    NAV_DIR / "RibbonBar.qml",
    NAV_DIR / "RibbonTab.qml",
    NAV_DIR / "RibbonGroup.qml",
    NAV_DIR / "_internal" / "RibbonTabButton.qml",
    NAV_DIR / "_internal" / "AppBarDisplayStateResolver.js",
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "ribbon-bar-runtime.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML
import "../../prismqml/PrismQML/navigation"

Item {
    id: scene

    readonly property int appBarInherit: Enums.commandBar.appBar_inherit
    readonly property int appBarSticky: Enums.commandBar.appBar_sticky
    readonly property int appBarCompact: Enums.commandBar.appBar_compact
    readonly property int appBarExpanded: Enums.commandBar.appBar_expanded
    readonly property int compactHeight: Enums.controlSize.commandBarButtonSize
    readonly property int largeHeight: Enums.controlSize.commandBarButtonSize * 2
    readonly property int stripHeight: Enums.controlSize.tabBarHeight
    readonly property int groupSpacing: Enums.spacing.xs

    function addDynamicTab() {
        var tab = dynamicTabFactory.createObject(scene, {})
        ribbon.tabData.push(tab)
    }

    width: 900
    height: 320

    RibbonBar {
        id: ribbon
        objectName: "ribbon"
        x: 10
        y: 10
        width: 880

        RibbonTab {
            id: homeTab
            objectName: "homeTab"
            title: "Home"
            key: "home"
            icon: Enums.icon.ribbon

            RibbonGroup {
                id: clipboardGroup
                objectName: "clipboardGroup"
                title: "Clipboard"

                AppBarButton {
                    objectName: "pasteButton"
                    text: "Paste"
                    icon: Enums.icon.clipboard
                    menuItems: [
                        {"text": "Paste", "icon": Enums.icon.clipboard},
                        {"text": "Paste special", "icon": Enums.icon.copy}
                    ]
                }

                AppBarToggleButton {
                    objectName: "boldToggle"
                    text: "Bold"
                    icon: Enums.icon.text_bold
                }

                AppBarButton {
                    objectName: "stickyButton"
                    text: "Pinned"
                    icon: Enums.icon.pin
                    displayState: Enums.commandBar.appBar_sticky
                }

                AppBarSeparator {
                    objectName: "clipboardSeparator"
                }
            }

            RibbonGroup {
                id: editGroup
                objectName: "editGroup"
                title: "Edit"

                AppBarButton {
                    objectName: "cutButton"
                    text: "Cut"
                    icon: Enums.icon.cut
                }

                AppBarButton {
                    objectName: "copyButton"
                    text: "Copy"
                    icon: Enums.icon.copy
                }
            }
        }

        RibbonTab {
            id: insertTab
            objectName: "insertTab"
            title: "Insert"
            key: "insert"

            RibbonGroup {
                id: insertGroup
                objectName: "insertGroup"
                title: "Insert"

                AppBarButton {
                    objectName: "tableButton"
                    text: "Table"
                    icon: Enums.icon.table
                }
            }

            RibbonGroup {
                id: mediaGroup
                objectName: "mediaGroup"
                title: "Media"

                AppBarButton {
                    objectName: "pictureButton"
                    text: "Picture"
                    icon: Enums.icon.image
                }
            }
        }
    }

    Component {
        id: dynamicTabFactory

        RibbonTab {
            objectName: "dynamicTab"
            title: "Dynamic"
            key: "dynamic"

            RibbonGroup {
                objectName: "dynamicGroup"
                title: "Dynamic"

                AppBarButton {
                    objectName: "dynamicButton"
                    text: "Dynamic"
                    icon: Enums.icon.add
                }
            }
        }
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2400) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump(20)
        elapsed += 20
    return predicate()


def _create_scene(qapp):
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
    root = component.create()
    assert root is not None, [error.toString() for error in component.errors()]

    window = QQuickWindow()
    window.setWidth(900)
    window.setHeight(320)
    root.setParentItem(window.contentItem())
    window.show()
    window.requestActivate()
    _pump(120)
    return engine, component, window, root, warnings


def _dispose_scene(engine, component, window, root) -> None:
    window.close()
    root.setParentItem(None)
    root.deleteLater()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump(20)


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is accepted for accepted in allowed)
    ]


def _item(root, name):
    item = root.findChild(QQuickItem, name)
    assert item is not None, name
    return item


def _strip_buttons(ribbon):
    strip = _item(ribbon, "ribbonTabStrip")
    return [
        child
        for child in strip.childItems()
        if child.objectName().startswith("ribbonTabButton_")
    ]


def _click(window, item) -> None:
    point = item.mapToScene(
        QPointF(item.width() / 2, item.height() / 2)
    ).toPoint()
    QTest.mouseMove(window, point)
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point
    )
    _pump(60)


def _visual_descendants(item):
    found = []
    pending = list(item.childItems())
    while pending:
        child = pending.pop()
        found.append(child)
        pending.extend(child.childItems())
    return found


def test_ribbon_bar_tab_strip_and_group_geometry(qapp):
    """条带与分组必须真实排布, 且隐藏标签页切回后仍保有排布。"""
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, root, warnings = _create_scene(qapp)
    try:
        ribbon = _item(root, "ribbon")
        home_tab = _item(root, "homeTab")
        insert_tab = _item(root, "insertTab")
        panel = _item(root, "ribbonPanelHost")
        assert ribbon.property("tabCount") == 2
        assert ribbon.property("currentIndex") == 0
        assert home_tab.property("selected") is True
        assert insert_tab.property("selected") is False
        assert home_tab.isVisible()
        assert not insert_tab.isVisible()

        buttons = _strip_buttons(ribbon)
        assert len(buttons) == 2
        assert buttons[0].property("selected") is True
        assert buttons[1].property("selected") is False
        assert buttons[0].width() > 0 and buttons[1].width() > 0
        assert buttons[0].height() == pytest.approx(
            root.property("stripHeight")
        )
        assert buttons[0].x() == pytest.approx(0)
        assert buttons[1].x() == pytest.approx(
            buttons[0].x() + buttons[0].width()
        )

        clipboard = _item(root, "clipboardGroup")
        edit = _item(root, "editGroup")
        assert panel.height() > 0
        assert clipboard.width() > 0 and edit.width() > 0
        assert clipboard.height() == pytest.approx(panel.height())
        assert clipboard.x() == pytest.approx(0)
        assert edit.x() == pytest.approx(clipboard.x() + clipboard.width())
        assert clipboard.property("_isLastGroup") is False
        assert edit.property("_isLastGroup") is True
        assert edit.x() + edit.width() <= ribbon.width()

        paste = _item(root, "pasteButton")
        bold = _item(root, "boldToggle")
        sticky = _item(root, "stickyButton")
        separator = _item(root, "clipboardSeparator")
        spacing = root.property("groupSpacing")
        assert paste.x() == pytest.approx(0)
        assert bold.x() == pytest.approx(paste.x() + paste.width() + spacing)
        assert sticky.x() == pytest.approx(bold.x() + bold.width() + spacing)
        assert separator.x() == pytest.approx(
            sticky.x() + sticky.width() + spacing
        )
        assert paste.height() == pytest.approx(root.property("largeHeight"))
        assert bold.height() == pytest.approx(root.property("largeHeight"))

        ribbon.setProperty("currentIndex", 1)
        assert _wait_for(lambda: insert_tab.isVisible() and not home_tab.isVisible())
        insert_group = _item(root, "insertGroup")
        media_group = _item(root, "mediaGroup")
        assert insert_group.isVisible() and media_group.isVisible()
        assert not clipboard.isVisible()
        assert insert_group.width() > 0 and media_group.width() > 0
        assert insert_group.x() == pytest.approx(0)
        # A tab that starts hidden must still settle into the same row layout.
        # 初始隐藏的标签页切回后仍必须收敛到同一行排布。
        assert _wait_for(
            lambda: media_group.x()
            == pytest.approx(insert_group.x() + insert_group.width())
        )
        assert insert_group.property("_isLastGroup") is False
        assert media_group.property("_isLastGroup") is True
        assert _item(root, "tableButton").isVisible()
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window, root)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_ribbon_bar_real_click_switches_tabs(qapp):
    """真实点击标签按钮必须切换当前标签页并派发 currentChanged。"""
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, root, warnings = _create_scene(qapp)
    try:
        ribbon = _item(root, "ribbon")
        home_tab = _item(root, "homeTab")
        insert_tab = _item(root, "insertTab")
        changed = []
        ribbon.currentChanged.connect(changed.append)
        buttons = _strip_buttons(ribbon)

        _click(window, buttons[1])
        assert _wait_for(lambda: ribbon.property("currentIndex") == 1)
        assert changed == [1]
        assert _wait_for(lambda: insert_tab.isVisible() and not home_tab.isVisible())
        assert _item(root, "insertGroup").isVisible()
        assert not _item(root, "clipboardGroup").isVisible()
        assert buttons[1].property("selected") is True

        _click(window, buttons[0])
        assert _wait_for(lambda: ribbon.property("currentIndex") == 0)
        assert changed == [1, 0]
        assert _wait_for(lambda: home_tab.isVisible() and not insert_tab.isVisible())
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window, root)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_ribbon_bar_real_click_minimizes_and_expands(qapp):
    """真实点击折叠按钮必须收起面板, 再次点击恢复。"""
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, root, warnings = _create_scene(qapp)
    try:
        ribbon = _item(root, "ribbon")
        panel = _item(root, "ribbonPanelHost")
        minimize_button = _item(root, "ribbonMinimizeButton")
        expansion = []
        ribbon.expansionChanged.connect(expansion.append)
        open_height = panel.height()
        open_bar_height = ribbon.height()
        assert open_height > 0

        _click(window, minimize_button)
        assert _wait_for(lambda: ribbon.property("minimized") is True)
        assert expansion == [True]
        assert ribbon.property("appBarStateName") == "compact"
        assert _wait_for(lambda: panel.height() == 0)
        assert ribbon.height() == pytest.approx(root.property("stripHeight"))
        assert _item(root, "clipboardGroup").isVisible() is True

        _click(window, minimize_button)
        assert _wait_for(lambda: ribbon.property("minimized") is False)
        assert expansion == [True, False]
        assert ribbon.property("appBarStateName") == "expanded"
        assert _wait_for(
            lambda: panel.height() == pytest.approx(open_height)
        )
        assert ribbon.height() == pytest.approx(open_bar_height)

        assert QMetaObject.invokeMethod(ribbon, "minimize")
        assert ribbon.property("minimized") is True
        assert QMetaObject.invokeMethod(ribbon, "expand")
        assert ribbon.property("minimized") is False
        assert QMetaObject.invokeMethod(ribbon, "pin")
        assert ribbon.property("sticky") is True
        assert ribbon.property("appBarStateName") == "sticky"
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window, root)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_ribbon_bar_keyboard_reaches_tabs_and_minimize(qapp):
    """键盘必须能切标签、激活当前标签并折叠/展开。"""
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, root, warnings = _create_scene(qapp)
    try:
        ribbon = _item(root, "ribbon")
        clicked = []
        ribbon.tabClicked.connect(clicked.append)
        ribbon.forceActiveFocus()
        assert _wait_for(ribbon.hasActiveFocus)

        QTest.keyClick(window, Qt.Key_Right)
        assert _wait_for(lambda: ribbon.property("currentIndex") == 1)
        QTest.keyClick(window, Qt.Key_Right)
        assert _wait_for(lambda: ribbon.property("currentIndex") == 0)
        QTest.keyClick(window, Qt.Key_Left)
        assert _wait_for(lambda: ribbon.property("currentIndex") == 1)
        QTest.keyClick(window, Qt.Key_Return)
        assert clicked == [1]

        QTest.keyClick(window, Qt.Key_F1)
        _pump(80)
        assert ribbon.property("minimized") is False
        QTest.keyClick(window, Qt.Key_F1, Qt.KeyboardModifier.ControlModifier)
        assert _wait_for(lambda: ribbon.property("minimized") is True)
        QTest.keyClick(window, Qt.Key_F1, Qt.KeyboardModifier.ControlModifier)
        assert _wait_for(lambda: ribbon.property("minimized") is False)
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window, root)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_ribbon_bar_display_state_reaches_buttons(qapp):
    """折叠宿主必须让按钮继承紧凑态, 显式固定态必须压过宿主。"""
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, root, warnings = _create_scene(qapp)
    try:
        ribbon = _item(root, "ribbon")
        paste = _item(root, "pasteButton")
        sticky = _item(root, "stickyButton")
        assert ribbon.property("displayState") == root.property("appBarExpanded")
        assert paste.property("resolvedDisplayState") == root.property(
            "appBarExpanded"
        )
        assert paste.property("appBarStateName") == "expanded"
        assert paste.property("labelVisible") is True
        assert paste.height() == pytest.approx(root.property("largeHeight"))
        assert sticky.property("appBarStateName") == "sticky"

        ribbon.setProperty("displayState", root.property("appBarCompact"))
        assert _wait_for(lambda: ribbon.property("minimized") is True)
        assert _wait_for(
            lambda: paste.property("appBarStateName") == "compact"
        )
        assert paste.property("labelVisible") is False
        assert paste.height() == pytest.approx(root.property("compactHeight"))
        # Sticky ignores the collapsed host 固定态无视折叠宿主
        assert sticky.property("resolvedDisplayState") == root.property(
            "appBarSticky"
        )
        assert sticky.property("labelVisible") is True
        assert sticky.height() == pytest.approx(root.property("largeHeight"))
        assert _item(root, "boldToggle").property("labelVisible") is False

        ribbon.setProperty("displayState", root.property("appBarSticky"))
        assert _wait_for(lambda: paste.property("appBarStateName") == "sticky")
        assert paste.property("labelVisible") is True
        assert ribbon.property("minimized") is False
        assert ribbon.property("sticky") is True

        assert QMetaObject.invokeMethod(ribbon, "minimize")
        assert ribbon.property("displayState") == root.property("appBarCompact")
        assert QMetaObject.invokeMethod(ribbon, "expand")
        assert ribbon.property("displayState") == root.property("appBarExpanded")
        QMetaObject.invokeMethod(ribbon, "cycleDisplayState")
        assert ribbon.property("displayState") == root.property("appBarSticky")
        assert ribbon.property("appBarStateName") == "sticky"
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window, root)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_ribbon_tab_and_group_pin_their_own_display_state(qapp):
    """标签页与分组的显式状态必须压过宿主, 并传给自身命令按钮。"""
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, root, warnings = _create_scene(qapp)
    try:
        home_tab = _item(root, "homeTab")
        insert_group = _item(root, "insertGroup")
        paste = _item(root, "pasteButton")
        cut = _item(root, "cutButton")
        table = _item(root, "tableButton")
        picture = _item(root, "pictureButton")
        assert paste.property("appBarStateName") == "expanded"

        home_tab.setProperty("displayState", root.property("appBarCompact"))
        assert _wait_for(lambda: paste.property("appBarStateName") == "compact")
        assert paste.property("labelVisible") is False
        assert cut.property("appBarStateName") == "compact"
        # The untouched tab keeps inheriting the bar 未改动的标签页继续继承功能区
        assert table.property("appBarStateName") == "expanded"

        insert_group.setProperty("displayState", root.property("appBarSticky"))
        assert _wait_for(lambda: table.property("appBarStateName") == "sticky")
        assert table.property("labelVisible") is True
        assert picture.property("appBarStateName") == "expanded"
        assert insert_group.property("resolvedDisplayState") == root.property(
            "appBarSticky"
        )
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window, root)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_ribbon_bar_command_menu_opens_a_native_window(qapp):
    """功能区内命令菜单必须是独立原生窗口, Escape 可关闭且无残留窗口。"""
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, root, warnings = _create_scene(qapp)
    try:
        paste = _item(root, "pasteButton")
        assert paste.property("menuEnabled") is True
        assert paste.property("menuOpen") is False

        _click(window, paste)
        assert _wait_for(lambda: paste.property("menuOpen") is True)
        popups = _new_visible_windows(windows_before, window)
        assert len(popups) == 1

        actions = {
            item.property("text"): item
            for item in _visual_descendants(popups[0].contentItem())
            if item.objectName().startswith("appBarButtonMenuAction_")
        }
        assert set(actions) == {"Paste", "Paste special"}

        QTest.keyClick(popups[0], Qt.Key_Escape)
        assert _wait_for(lambda: paste.property("menuOpen") is False)
        assert _wait_for(
            lambda: _new_visible_windows(windows_before, window) == []
        )
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window, root)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_ribbon_bar_accepts_a_dynamically_added_tab(qapp):
    """运行时新增标签页必须重建条带、收敛序号并保持排布。"""
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, root, warnings = _create_scene(qapp)
    try:
        ribbon = _item(root, "ribbon")
        assert ribbon.property("tabCount") == 2
        assert QMetaObject.invokeMethod(root, "addDynamicTab")
        assert _wait_for(lambda: ribbon.property("tabCount") == 3)

        dynamic_tab = _item(root, "dynamicTab")
        assert _wait_for(lambda: dynamic_tab.property("tabIndex") == 2)
        assert dynamic_tab.property("selected") is False
        assert not dynamic_tab.isVisible()

        assert _wait_for(lambda: len(_strip_buttons(ribbon)) == 3)
        buttons = _strip_buttons(ribbon)
        assert buttons[2].width() > 0
        assert _wait_for(
            lambda: buttons[2].x()
            == pytest.approx(buttons[1].x() + buttons[1].width())
        )

        ribbon.setProperty("currentIndex", 2)
        assert _wait_for(lambda: dynamic_tab.isVisible())
        dynamic_group = _item(root, "dynamicGroup")
        assert dynamic_group.isVisible()
        assert dynamic_group.property("_isLastGroup") is True
        assert _wait_for(
            lambda: dynamic_group.width() > 0
            and dynamic_group.height() > 0
        )
        assert _item(root, "dynamicButton").isVisible()
        assert not _item(root, "homeTab").isVisible()
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window, root)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_ribbon_bar_sources_follow_conventions():
    for source_path in SOURCE_PATHS:
        source = source_path.read_text(encoding="utf-8")
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        violations = scan_source_text(source, path)
        assert [
            violation
            for violation in violations
            if violation.rule in {"QML008", "QML009", "QML010"}
        ] == []
