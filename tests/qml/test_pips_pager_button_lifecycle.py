# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""PipsPager button lifecycle regressions. 分页指示器按钮生命周期回归。"""

from pathlib import Path, PurePosixPath

import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent, QObject, QPoint, Qt, QUrl
from PySide6.QtGui import QGuiApplication
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
    / "data"
    / "FlipView"
    / "PipsPagerCore.qml"
)
NAV_BUTTON_SOURCE_PATH = SOURCE_PATH.parent / "_internal" / "PipsPagerNavButton.qml"
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "pips-pager-button-lifecycle.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    readonly property int alwaysMode: Enums.pipsPager.button_always
    readonly property int neverMode: Enums.pipsPager.button_never
    readonly property string leftIcon: Enums.icon.chevron_left
    readonly property string rightIcon: Enums.icon.chevron_right
    readonly property string upIcon: Enums.icon.chevron_up
    readonly property string downIcon: Enums.icon.chevron_down

    width: 420
    height: 240
    visible: true

    HorizontalPipsPager {
        objectName: "horizontalPager"
        x: 40
        y: 40
        count: 5
        currentIndex: 2
    }

    VerticalPipsPager {
        objectName: "verticalPager"
        x: 280
        y: 40
        count: 5
        currentIndex: 2
    }

    HorizontalPipsPager {
        objectName: "initialPager"
        x: 40
        y: 160
        count: 5
        currentIndex: 2
        prevButtonMode: Enums.pipsPager.button_always
        nextButtonMode: Enums.pipsPager.button_always
    }
}
"""


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
    ]


def _button(pager: QQuickItem, object_name: str):
    pending = list(pager.childItems())
    while pending:
        item = pending.pop()
        if item.objectName() == object_name:
            return item
        pending.extend(item.childItems())
    return None


def _point_for(window: QQuickWindow, item: QQuickItem) -> QPoint:
    center = item.mapToScene(item.boundingRect().center())
    return QPoint(round(center.x()), round(center.y()))


def _dispose_scene(engine, component, window) -> None:
    window.setVisible(False)
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def test_pips_pager_creates_only_buttons_enabled_by_mode(qapp):
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
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    horizontal = window.findChild(QQuickItem, "horizontalPager")
    vertical = window.findChild(QQuickItem, "verticalPager")
    initial = window.findChild(QQuickItem, "initialPager")
    assert horizontal is not None and vertical is not None and initial is not None
    QCoreApplication.processEvents()

    try:
        for pager in (horizontal, vertical):
            assert _button(pager, "pipsPrevButton") is None
            assert _button(pager, "pipsNextButton") is None

        initial_previous = _button(initial, "pipsPrevButton")
        initial_following = _button(initial, "pipsNextButton")
        assert initial_previous is not None and initial_previous.isVisible()
        assert initial_following is not None and initial_following.isVisible()
        assert initial_previous.property("icon") == window.property("leftIcon")
        assert initial_following.property("icon") == window.property("rightIcon")

        horizontal.setProperty("prevButtonMode", window.property("alwaysMode"))
        QCoreApplication.processEvents()
        previous = _button(horizontal, "pipsPrevButton")
        assert previous is not None and previous.isVisible()
        assert previous.property("icon") == window.property("leftIcon")
        assert _button(horizontal, "pipsNextButton") is None
        QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=_point_for(window, previous))
        assert horizontal.property("currentIndex") == 1

        horizontal.setProperty("nextButtonMode", window.property("alwaysMode"))
        QCoreApplication.processEvents()
        following = _button(horizontal, "pipsNextButton")
        assert following is not None and following.isVisible()
        assert following.property("icon") == window.property("rightIcon")
        QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=_point_for(window, following))
        assert horizontal.property("currentIndex") == 2

        horizontal.setProperty("prevButtonMode", window.property("neverMode"))
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()
        assert _button(horizontal, "pipsPrevButton") is None
        remaining = _button(horizontal, "pipsNextButton")
        assert remaining is not None
        assert remaining.property("icon") == window.property("rightIcon")

        horizontal.setProperty("nextButtonMode", window.property("neverMode"))
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()
        assert _button(horizontal, "pipsNextButton") is None
        assert not shiboken6.isValid(remaining)

        vertical.setProperty("prevButtonMode", window.property("alwaysMode"))
        vertical.setProperty("nextButtonMode", window.property("alwaysMode"))
        QCoreApplication.processEvents()
        vertical_previous = _button(vertical, "pipsPrevButton")
        vertical_following = _button(vertical, "pipsNextButton")
        assert vertical_previous.property("icon") == window.property("upIcon")
        assert vertical_following.property("icon") == window.property("downIcon")
        assert vertical_previous.x() + vertical_previous.width() / 2 == (
            vertical.width() / 2
        )
        assert vertical_following.x() + vertical_following.width() / 2 == (
            vertical.width() / 2
        )

        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_pips_pager_source_conventions():
    entry_source = SOURCE_PATH.read_text(encoding="utf-8")
    sources = (
        (SOURCE_PATH, entry_source),
        (NAV_BUTTON_SOURCE_PATH, NAV_BUTTON_SOURCE_PATH.read_text(encoding="utf-8")),
    )
    violations = []
    for source_path, source in sources:
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        violations.extend(scan_source_text(source, path))
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
    helper_source = NAV_BUTTON_SOURCE_PATH.read_text(encoding="utf-8")
    assert 'objectName: isNext ? "pipsNextButton" : "pipsPrevButton"' in helper_source
    assert "required property bool isNext" in helper_source
    assert "navButtonComponent.createObject(control" in entry_source
