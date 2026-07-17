# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SettingsCard component group runtime contracts. SettingsCard 组件组运行时合同。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QMetaObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "settings"
    / "SettingsCard"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "settings-card-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"

    readonly property var cardValue: card.getValue()
    readonly property bool cardExpanded: card.expanded
    readonly property int folderCount: card.folders.length
    readonly property bool coreExpandable: core.expandable
    readonly property bool coreExpanded: core.expanded
    readonly property real coreHeight: core.implicitHeight

    property var addedGroupCard: null

    function selectOption() { card.setValue(1) }
    function toggleCard() { card.toggle() }
    function ensureCardExpanded() { card.setExpanded(true) }
    function runFolderFlow() {
        card.type = Enums.settingCard.type_folder_list
        card.addFolder("A")
        card.addFolder("A")
        card.addFolder("B")
        card.removeFolder("A")
    }
    function clearFolders() { card.clearFolders() }
    function addCoreWidgets() {
        core.addRightWidget(rightComponent.createObject(root))
        core.addExpandWidget(expandComponent.createObject(root))
        core.expanded = true
    }
    function addGroupCard() {
        addedGroupCard = groupCardComponent.createObject(root)
        group.addCard(addedGroupCard)
    }
    function removeGroupCard() { group.removeCard(addedGroupCard) }
    function clearGroupCards() { group.clearCards() }

    width: 760
    height: 520
    visible: true

    Component {
        id: rightComponent
        Rectangle {
            objectName: "rightWidget"
            width: 40
            height: 20
        }
    }

    Component {
        id: expandComponent
        Rectangle {
            objectName: "expandWidget"
            width: 120
            height: 36
        }
    }

    Component {
        id: groupCardComponent
        Rectangle {
            objectName: "dynamicGroupCard"
            height: 48
        }
    }

    SettingsCard {
        id: card
        objectName: "settingsCard"
        x: 20
        y: 20
        width: 320
        type: Enums.settingCard.type_options
        title: "Mode"
        options: ["One", "Two", "Three"]
        selectedIndex: 0
    }

    SettingsCardCore {
        id: core
        objectName: "settingsCardCore"
        x: 380
        y: 20
        width: 320
        title: "Core"
        content: "Description"
    }

    SettingsCardGroup {
        id: group
        objectName: "settingsCardGroup"
        x: 20
        y: 260
        width: 320
        title: "Group"

        Rectangle {
            objectName: "initialGroupCard"
            width: parent ? parent.width : 0
            height: 40
        }
    }

    SettingsCardContent {
        objectName: "settingsCardContent"
        x: 380
        y: 260
        type: Enums.settingCard.type_push
        buttonText: "Apply"
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1200) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 30
    return predicate()


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is accepted for accepted in allowed)
    ]


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _visual_items(item):
    result = []
    for child in item.childItems():
        result.append(child)
        result.extend(_visual_items(child))
    return result


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
    assert isinstance(window, QQuickWindow)
    items = {
        name: window.findChild(QQuickItem, name)
        for name in (
            "settingsCard",
            "settingsCardCore",
            "settingsCardGroup",
            "settingsCardContent",
        )
    }
    assert all(items.values())
    _pump()
    return engine, component, window, items, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


@pytest.fixture
def settings_scene(qapp):
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    try:
        yield (*scene[2:], windows_before)
    finally:
        _dispose_scene(scene[0], scene[1], scene[2])
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_settings_card_value_expand_and_folder_contracts(settings_scene):
    window, items, warnings, windows_before = settings_scene
    card = items["settingsCard"]
    expanded = []
    appended = []
    deleted = []
    updated = []
    card.expandToggled.connect(expanded.append)
    card.folderAppended.connect(appended.append)
    card.folderDeleted.connect(deleted.append)
    card.foldersUpdated.connect(lambda folders: updated.append(_variant(folders)))

    assert QMetaObject.invokeMethod(window, "selectOption")
    assert window.property("cardValue") == 1
    assert QMetaObject.invokeMethod(window, "toggleCard")
    assert window.property("cardExpanded")
    assert expanded == [True]
    assert QMetaObject.invokeMethod(window, "ensureCardExpanded")
    assert expanded == [True]

    assert QMetaObject.invokeMethod(window, "runFolderFlow")
    assert window.property("folderCount") == 1
    assert appended == ["A", "B"]
    assert deleted == ["A"]
    assert updated[-1] == ["B"]
    assert QMetaObject.invokeMethod(window, "clearFolders")
    assert window.property("folderCount") == 0
    assert updated[-1] == []
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_settings_card_core_and_group_composition(settings_scene):
    window, items, warnings, windows_before = settings_scene
    core = items["settingsCardCore"]
    group = items["settingsCardGroup"]
    collapsed_height = window.property("coreHeight")

    assert QMetaObject.invokeMethod(window, "addCoreWidgets")
    assert window.property("coreExpandable")
    assert window.property("coreExpanded")
    assert _wait_for(lambda: window.property("coreHeight") > collapsed_height)
    right_widget = next(
        (item for item in _visual_items(core) if item.objectName() == "rightWidget"),
        None,
    )
    expand_widget = next(
        (item for item in _visual_items(core) if item.objectName() == "expandWidget"),
        None,
    )
    assert right_widget is not None
    assert expand_widget is not None

    assert QMetaObject.invokeMethod(window, "addGroupCard")
    dynamic = next(
        (
            item
            for item in _visual_items(group)
            if item.objectName() == "dynamicGroupCard"
        ),
        None,
    )
    assert dynamic is not None
    assert dynamic.width() == pytest.approx(group.width())
    assert QMetaObject.invokeMethod(window, "removeGroupCard")
    assert dynamic.parentItem() is None
    assert QMetaObject.invokeMethod(window, "addGroupCard")
    assert QMetaObject.invokeMethod(window, "clearGroupCards")
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()
    assert not any(
        item.objectName() == "dynamicGroupCard" for item in _visual_items(group)
    )
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_settings_card_sources_follow_conventions():
    violations = []
    for source_path in sorted(SOURCE_DIR.glob("*.qml")):
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        violations.extend(
            violation
            for violation in scan_source_text(
                source_path.read_text(encoding="utf-8"), path
            )
            if violation.rule in {"QML008", "QML009"}
        )
    assert violations == []
