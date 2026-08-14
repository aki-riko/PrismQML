# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Neumorphic interactive surface regressions. 新拟态交互表面回归。"""

from pathlib import Path, PurePosixPath

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlProperty
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import Skin, Theme, getSkin, getTheme, register_types, setSkin, setTheme
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATHS = (
    ROOT / "prismqml/PrismQML/controls/buttons/Button/CustomButtonCore.qml",
    ROOT / "prismqml/PrismQML/controls/navigation/TabWidget.qml",
    ROOT / "prismqml/PrismQML/controls/feedback/State/StateWidget.qml",
    ROOT / "prismqml/PrismQML/controls/feedback/State/EmptyState.qml",
    ROOT / "prismqml/PrismQML/controls/feedback/State/ResultState.qml",
    ROOT / "prismqml/PrismQML/controls/feedback/State/OfflineState.qml",
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: host
    width: 1280
    height: 760
    visible: true

    readonly property int expectedRadius: Enums.neumorphism.radius
    readonly property real expectedBorderWidth: Enums.neumorphism.borderWidth

    Component {
        id: page
        Item {}
    }

    CustomButtonCore {
        id: customButton
        objectName: "interactiveCustomButton"
        x: 40
        y: 40
        width: 180
        height: 44
        text: "Pick"
    }

    TabWidget {
        id: tabs
        objectName: "interactiveTabs"
        x: 260
        y: 40
        width: 560
        height: 240
        movable: true
        tabs: [
            {"title": "Alpha", "content": page},
            {"title": "Bravo", "content": page}
        ]
    }

    StateWidget {
        objectName: "interactiveStateWidget"
        x: 40
        y: 340
        width: 240
        height: 220
        actionText: "Retry"
    }

    EmptyState {
        objectName: "interactiveEmptyState"
        x: 300
        y: 340
        width: 240
        height: 220
        actionText: "Open"
    }

    ResultState {
        objectName: "interactiveResultState"
        x: 560
        y: 340
        width: 240
        height: 220
        actionText: "Continue"
    }

    OfflineState {
        objectName: "interactiveOfflineState"
        x: 820
        y: 340
        width: 240
        height: 220
        retryText: "Reconnect"
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(
        SCENE_SOURCE,
        QUrl("inline:neumorphism-interactive-surfaces.qml"),
    )
    for _ in range(50):
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
    _pump()
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


def _visual_descendants(root: QQuickItem) -> list[QQuickItem]:
    result = []
    pending = list(root.childItems())
    while pending:
        item = pending.pop()
        result.append(item)
        pending.extend(item.childItems())
    return result


def _border_width(item: QObject, engine) -> float:
    return float(QQmlProperty(item, "border.width", engine).read())


def _matching_shadows(scope: QQuickWindow, target: QObject) -> list[QQuickItem]:
    return [
        item
        for item in _visual_descendants(scope.contentItem())
        if item.metaObject().indexOfProperty("target") >= 0
        and item.metaObject().indexOfProperty("inset") >= 0
        and item.metaObject().indexOfProperty("pressed") >= 0
        and item.property("target") == target
    ]


def _tab_drag_surface(tab: QQuickItem) -> QQuickItem:
    delegates = [
        item
        for item in _visual_descendants(tab)
        if item.metaObject().indexOfProperty("visualOffsetX") >= 0
        and item.metaObject().indexOfProperty("selected") >= 0
    ]
    assert len(delegates) == 2
    delegates.sort(key=lambda item: item.x())
    surface = next(
        item
        for item in delegates[1].childItems()
        if item.metaObject().className().startswith("QQuickRectangle")
        and item.metaObject().indexOfProperty("radius") >= 0
    )
    tab.setProperty("_dragSourceIndex", 1)
    _pump()
    return surface


def test_interactive_surfaces_follow_neumorphic_geometry_and_shadow_contract(qapp):
    previous_skin = getSkin()
    previous_theme = getTheme()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    setTheme(Theme.LIGHT)
    setSkin(Skin.NEUMORPHISM)
    engine, component, window, warnings = _create_scene()
    try:
        expected_radius = window.property("expectedRadius")
        expected_border = window.property("expectedBorderWidth")

        custom = window.findChild(QQuickItem, "interactiveCustomButton")
        custom_surface = custom.findChild(QQuickItem, "_customButtonSurface")
        tabs = window.findChild(QQuickItem, "interactiveTabs")
        assert custom is not None and custom_surface is not None and tabs is not None
        assert custom_surface.property("radius") == expected_radius
        assert _border_width(custom_surface, engine) == expected_border
        custom_shadows = _matching_shadows(window, custom_surface)
        assert len(custom_shadows) == 1
        assert custom_shadows[0].property("inset") is False

        drag_surface = _tab_drag_surface(tabs)
        assert drag_surface.property("radius") == expected_radius
        assert _border_width(drag_surface, engine) == expected_border

        for object_name in (
            "stateActionSurface",
            "emptyStateActionSurface",
            "resultStateActionSurface",
            "offlineStateActionSurface",
        ):
            surface = window.findChild(QQuickItem, object_name)
            assert surface is not None, object_name
            assert surface.property("radius") == expected_radius
            assert _border_width(surface, engine) == expected_border
            shadows = [
                child
                for child in surface.findChildren(QObject)
                if child.objectName() == "_shadowedRectangleNeumorphicShadow"
            ]
            assert len(shadows) == 1, object_name
            assert shadows[0].property("inset") is False

        assert warnings == []
        assert [
            item
            for item in QGuiApplication.topLevelWindows()
            if item.isVisible() and item not in windows_before and item is not window
        ] == []
    finally:
        _dispose_scene(engine, component, window)
        setTheme(previous_theme)
        setSkin(previous_skin)


def test_interactive_surface_sources_follow_qml_conventions():
    for source_path in SOURCE_PATHS:
        source = source_path.read_text(encoding="utf-8")
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        violations = scan_source_text(source, path)
        assert [
            violation
            for violation in violations
            if violation.rule in {"QML008", "QML009"}
        ] == []
