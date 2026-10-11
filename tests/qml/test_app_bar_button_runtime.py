# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""AppBar button family runtime contracts. 应用栏按钮族运行时合同。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import (
    Q_ARG,
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
    NAV_DIR / "AppBarButton.qml",
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "app-bar-button-runtime.qml")
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
    readonly property int styleIconOnly: Enums.commandBar.style_icon_only
    readonly property int styleTextBeside: Enums.commandBar.style_text_beside
    readonly property int styleTextUnder: Enums.commandBar.style_text_under
    readonly property int toggleFeature: Enums.button.feature_toggle
    readonly property int compactHeight: Enums.controlSize.commandBarButtonSize
    readonly property int largeHeight: Enums.controlSize.commandBarButtonSize * 2
    readonly property int minButtonWidth: Enums.controlSize.buttonMinWidth

    width: 900
    height: 320

    AppBarButton {
        objectName: "underButton"
        x: 10
        y: 10
        text: "Under"
        icon: Enums.icon.save
    }

    AppBarButton {
        objectName: "besideButton"
        x: 120
        y: 10
        text: "Beside"
        icon: Enums.icon.open
        labelPosition: Enums.commandBar.style_text_beside
    }

    AppBarButton {
        objectName: "iconOnlyButton"
        x: 240
        y: 10
        text: "Icon only"
        icon: Enums.icon.copy
        labelPosition: Enums.commandBar.style_icon_only
    }

    AppBarButton {
        objectName: "compactButton"
        x: 300
        y: 10
        text: "Compact"
        icon: Enums.icon.cut
        displayState: Enums.commandBar.appBar_compact
    }

    AppBarButton {
        objectName: "toggleButton"
        x: 380
        y: 10
        text: "Toggle"
        icon: Enums.icon.text_bold
        checkable: true
    }

    AppBarButton {
        objectName: "menuButton"
        x: 480
        y: 10
        text: "Menu"
        icon: Enums.icon.more_horizontal
        menuItems: [
            {"text": "First", "icon": Enums.icon.save},
            {"text": "Second", "icon": Enums.icon.open}
        ]
    }

    AppBarButton {
        objectName: "disabledButton"
        x: 580
        y: 10
        text: "Disabled"
        icon: Enums.icon.delete
        enabled: false
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


def _click(window, item) -> None:
    point = item.mapToScene(
        QPointF(item.width() / 2, item.height() / 2)
    ).toPoint()
    QTest.mouseMove(window, point)
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point
    )
    _pump(60)


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


def _visual_descendants(item):
    found = []
    pending = list(item.childItems())
    while pending:
        child = pending.pop()
        found.append(child)
        pending.extend(child.childItems())
    return found


def test_app_bar_button_label_positions_and_geometry(qapp):
    """三种标签位置必须给出不同的可见标签与高度。"""
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, root, warnings = _create_scene(qapp)
    try:
        under = _item(root, "underButton")
        beside = _item(root, "besideButton")
        icon_only = _item(root, "iconOnlyButton")
        compact = _item(root, "compactButton")
        large = root.property("largeHeight")
        small = root.property("compactHeight")

        assert under.property("labelVisible") is True
        assert under.height() == pytest.approx(large)
        assert beside.property("labelVisible") is True
        assert beside.height() == pytest.approx(small)
        assert icon_only.property("labelVisible") is False
        assert icon_only.height() == pytest.approx(small)
        assert compact.property("labelVisible") is False
        assert compact.height() == pytest.approx(small)
        assert icon_only.width() == pytest.approx(small)
        assert under.width() == pytest.approx(root.property("minButtonWidth"))
        assert under.width() > 0 and beside.width() > 0
        assert under.property("_stacked") is True
        assert beside.property("_stacked") is False
        assert under.property("labelPosition") == root.property("styleTextUnder")
        assert beside.property("labelPosition") == root.property("styleTextBeside")
        assert icon_only.property("labelPosition") == root.property(
            "styleIconOnly"
        )
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window, root)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_app_bar_button_display_state_machine(qapp):
    """Sticky/Compact/Expanded 状态机与继承回退必须真实生效。"""
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, root, warnings = _create_scene(qapp)
    try:
        under = _item(root, "underButton")
        large = root.property("largeHeight")
        small = root.property("compactHeight")

        # No host reachable: inherit falls back to expanded 无宿主可达时回退为展开态
        assert under.property("displayState") == root.property("appBarInherit")
        assert under.property("resolvedDisplayState") == root.property(
            "appBarExpanded"
        )
        assert under.property("appBarStateName") == "expanded"
        assert under.property("appBarSticky") is False
        assert under.property("appBarCompact") is False
        assert under.property("appBarExpanded") is True

        QMetaObject.invokeMethod(under, "cycleDisplayState")
        assert under.property("appBarStateName") == "sticky"
        assert under.property("appBarSticky") is True
        assert under.property("labelVisible") is True
        assert under.height() == pytest.approx(large)

        QMetaObject.invokeMethod(under, "cycleDisplayState")
        assert under.property("appBarStateName") == "compact"
        assert under.property("appBarCompact") is True
        assert under.property("labelVisible") is False
        assert under.height() == pytest.approx(small)

        QMetaObject.invokeMethod(under, "cycleDisplayState")
        assert under.property("appBarStateName") == "expanded"
        assert under.height() == pytest.approx(large)

        QMetaObject.invokeMethod(
            under,
            "setDisplayState",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", root.property("appBarSticky")),
        )
        assert under.property("resolvedDisplayState") == root.property(
            "appBarSticky"
        )
        assert under.property("labelVisible") is True
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window, root)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_app_bar_button_checkable_click_and_keyboard(qapp):
    """现有 AppBarButton 入口直接支持点击和键盘切换。"""
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, root, warnings = _create_scene(qapp)
    try:
        toggle = _item(root, "toggleButton")
        toggled = []
        clicked = []
        toggle.toggled.connect(toggled.append)
        toggle.clicked.connect(lambda: clicked.append(True))
        assert toggle.property("checkable") is True
        assert toggle.property("feature") == root.property("toggleFeature")
        assert toggle.property("checked") is False

        _click(window, toggle)
        assert _wait_for(lambda: toggle.property("checked") is True)
        assert toggled == [True]
        assert clicked == [True]

        _click(window, toggle)
        assert _wait_for(lambda: toggle.property("checked") is False)
        assert toggled == [True, False]

        toggle.forceActiveFocus()
        assert _wait_for(toggle.hasActiveFocus)
        QTest.keyClick(window, Qt.Key_Space)
        assert _wait_for(lambda: toggle.property("checked") is True)
        assert toggled == [True, False, True]
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window, root)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_app_bar_button_activates_from_keyboard_and_opens_native_menu(qapp):
    """键盘必须能激活按钮, 带菜单的按钮必须在独立原生窗口打开菜单。"""
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, root, warnings = _create_scene(qapp)
    try:
        under = _item(root, "underButton")
        clicks = []
        under.clicked.connect(lambda: clicks.append(True))
        under.forceActiveFocus()
        assert _wait_for(under.hasActiveFocus)
        QTest.keyClick(window, Qt.Key_Space)
        assert _wait_for(lambda: len(clicks) == 1)
        QTest.keyClick(window, Qt.Key_Return)
        assert _wait_for(lambda: len(clicks) == 2)

        menu_button = _item(root, "menuButton")
        assert menu_button.property("menuEnabled") is True
        menu_button.forceActiveFocus()
        assert _wait_for(menu_button.hasActiveFocus)
        QTest.keyClick(window, Qt.Key_Space)
        assert _wait_for(lambda: menu_button.property("menuOpen") is True)
        popups = _new_visible_windows(windows_before, window)
        assert len(popups) == 1
        actions = {
            item.property("text")
            for item in _visual_descendants(popups[0].contentItem())
            if item.objectName().startswith("appBarButtonMenuAction_")
        }
        assert actions == {"First", "Second"}

        QTest.keyClick(popups[0], Qt.Key_Escape)
        assert _wait_for(lambda: menu_button.property("menuOpen") is False)
        assert _wait_for(
            lambda: _new_visible_windows(windows_before, window) == []
        )
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window, root)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_app_bar_button_sources_follow_conventions():
    for source_path in SOURCE_PATHS:
        source = source_path.read_text(encoding="utf-8")
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        violations = scan_source_text(source, path)
        assert [
            violation
            for violation in violations
            if violation.rule in {"QML008", "QML009", "QML010"}
        ] == []
