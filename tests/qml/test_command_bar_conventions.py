# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""CommandBar overflow and signal contracts. CommandBar 溢出与信号合同。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QPointF,
    QObject,
    QTimer,
    QUrl,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
COMMAND_BAR_DIR = (
    ROOT / "prismqml" / "PrismQML" / "controls" / "containers" / "CommandBar"
)
SOURCE_PATHS = [
    COMMAND_BAR_DIR / "CommandBarEntry.qml",
    COMMAND_BAR_DIR / "_internal" / "CommandBarCore.qml",
    COMMAND_BAR_DIR / "_internal" / "CommandBarSurface.qml",
]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "command-bar-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/controls/containers/CommandBar/_internal" as Internal

Window {
    id: root

    readonly property int wideVisibleCount: wideCore._visibleCommands.length
    readonly property int wideHiddenCount: wideCore._hiddenCommands.length
    readonly property bool wideHasOverflow: wideCore._hasOverflow
    readonly property int narrowVisibleCount: narrowCore._visibleCommands.length
    readonly property int narrowHiddenCount: narrowCore._hiddenCommands.length
    readonly property bool narrowHasOverflow: narrowCore._hasOverflow
    readonly property int disabledVisibleCount: disabledCore._visibleCommands.length
    readonly property int disabledHiddenCount: disabledCore._hiddenCommands.length
    readonly property bool disabledHasOverflow: disabledCore._hasOverflow
    readonly property int textBesideStyle: Enums.commandBar.style_text_beside
    readonly property int textUnderStyle: Enums.commandBar.style_text_under

    width: 900
    height: 420
    visible: true

    Internal.CommandBarCore {
        id: wideCore
        objectName: "wideCore"
        width: 400
        primaryCommands: [
            {"text": "Open", "icon": "FolderOpen"},
            {"text": "Save", "icon": "Save"},
            {"text": "Copy", "icon": "Copy"}
        ]
        secondaryCommands: [
            {"text": "Settings", "icon": "Settings"},
            {"text": "Help", "icon": "QuestionCircle"},
            {"text": "Help 2", "icon": "QuestionCircle"},
            {"text": "Help 3", "icon": "QuestionCircle"},
            {"text": "Help 4", "icon": "QuestionCircle"},
            {"text": "Help 5", "icon": "QuestionCircle"}
        ]
    }

    Internal.CommandBarCore {
        id: narrowCore
        objectName: "narrowCore"
        y: 60
        width: 120
        primaryCommands: [
            {"text": "Open", "icon": "FolderOpen"},
            {"text": "Save", "icon": "Save"},
            {"separator": true},
            {"text": "Copy", "icon": "Copy"}
        ]
    }

    Internal.CommandBarCore {
        id: disabledCore
        objectName: "disabledCore"
        y: 120
        width: 60
        disableOverflow: true
        primaryCommands: narrowCore.primaryCommands
    }

    Internal.CommandBarCore {
        id: emptyCore
        objectName: "emptyCore"
        y: 180
        width: 400
    }

    CommandBar {
        id: defaultEntry
        objectName: "defaultEntry"
        x: 450
        width: 360
        showLabels: true
        commands: [
            {"text": "Open", "icon": "FolderOpen"},
            {"text": "Save", "icon": "Save"}
        ]
    }

    CommandBar {
        id: viewEntry
        objectName: "viewEntry"
        x: 450
        y: 100
        width: 360
        type: Enums.commandBar.type_view
        showLabels: true
        primaryCommands: [{"text": "View", "icon": "View"}]
    }

    Breadcrumb {
        id: iconBreadcrumb
        objectName: "iconBreadcrumb"
        y: 220
        showIcons: true

        Component.onCompleted: {
            addItem("home", "Home", Enums.icon.home)
            addItem("folder", "Folder", Enums.icon.folder)
        }
    }

    Paginator {
        id: paginator
        objectName: "paginator"
        y: 340
        totalPages: 10
        currentPage: 3
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1600) -> bool:
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
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    _pump()
    return engine, component, root, warnings


def _dispose_scene(engine, component, root) -> None:
    root.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is accepted for accepted in allowed)
    ]


def _visual_descendants(root):
    result = []
    pending = list(root.childItems())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.childItems())
    return result


def _command_bar_core(entry):
    matches = [
        item
        for item in entry.findChildren(QQuickItem)
        if item.metaObject().className().startswith("CommandBarCore")
    ]
    assert len(matches) == 1
    return matches[0]


def _command_button(core, text):
    row = next(
        item
        for item in core.childItems()
        if item.metaObject().className() == "QQuickRow"
    )
    loaders = []
    for item in row.childItems():
        if not item.metaObject().className().startswith("QQuickLoader"):
            continue
        command_data = _variant(item.property("commandData"))
        if isinstance(command_data, dict) and command_data.get("text") == text:
            loaders.append(item)
    assert len(loaders) == 1
    wrapper = loaders[0].property("item")
    buttons = [
        item
        for item in wrapper.findChildren(QObject)
        if item.metaObject().className().startswith("ButtonCore")
    ]
    assert len(buttons) == 1
    return loaders[0], wrapper, buttons[0]


def _breadcrumb_button(breadcrumb, text):
    matches = [
        item
        for item in _visual_descendants(breadcrumb)
        if item.metaObject().className().startswith("ButtonCore")
        and item.property("text") == text
    ]
    return matches[0] if len(matches) == 1 else None


def _paginator_button(paginator, icon):
    matches = [
        item
        for item in _visual_descendants(paginator)
        if item.metaObject().className().startswith("ButtonCore")
        and item.property("icon") == icon
    ]
    assert len(matches) == 1
    return matches[0]


def _more_loader(core):
    loader = core.findChild(QQuickItem, "commandBarMoreLoader")
    assert loader is not None
    return loader


def test_command_bar_overflow_matrix(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, warnings = _create_scene()
    try:
        assert root.property("wideVisibleCount") == 3
        assert root.property("wideHiddenCount") == 0
        assert not root.property("wideHasOverflow")
        assert root.property("narrowVisibleCount") == 2
        assert root.property("narrowHiddenCount") == 2
        assert root.property("narrowHasOverflow")
        assert root.property("disabledVisibleCount") == 4
        assert root.property("disabledHiddenCount") == 0
        assert not root.property("disabledHasOverflow")
        assert warnings == []
        assert _new_visible_windows(windows_before, root) == []
    finally:
        _dispose_scene(engine, component, root)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_command_bar_entry_styles_and_signal_forwarding(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, warnings = _create_scene()
    default_entry = root.findChild(QQuickItem, "defaultEntry")
    view_entry = root.findChild(QQuickItem, "viewEntry")
    actions = []
    commands = []
    default_entry.actionTriggered.connect(
        lambda index, action: actions.append((index, _variant(action)["text"]))
    )
    default_entry.commandClicked.connect(
        lambda index, text: commands.append((index, text))
    )
    try:
        default_core = _command_bar_core(default_entry)
        view_core = _command_bar_core(view_entry)
        assert default_core.property("buttonStyle") == root.property("textBesideStyle")
        assert view_core.property("buttonStyle") == root.property("textUnderStyle")
        button_loader, button_wrapper, button = _command_button(
            default_core, "Open"
        )
        assert button_loader.property("item") is not None
        assert button_wrapper is not None
        assert button.property("text") == "Open"
        assert button.width() == button_wrapper.width()
        assert button.height() == button_wrapper.height()
        default_icon = button.findChild(QQuickItem, "buttonContentIcon")
        default_text = button.findChild(QQuickItem, "buttonContentText")
        assert default_icon is not None and default_text is not None
        assert default_icon.mapToItem(button, QPointF()).x() + default_icon.width() \
            <= default_text.mapToItem(button, QPointF()).x()

        _, view_button_wrapper, view_button = _command_button(view_core, "View")
        assert view_button.property("text") == "View"
        assert view_button.width() == view_button_wrapper.width()
        assert view_button.height() == view_button_wrapper.height()
        view_icon = view_button.findChild(QQuickItem, "buttonContentIcon")
        view_text = view_button.findChild(QQuickItem, "buttonContentText")
        assert view_icon is not None and view_text is not None
        assert view_icon.mapToItem(view_button, QPointF()).y() + view_icon.height() \
            <= view_text.mapToItem(view_button, QPointF()).y()

        breadcrumb = root.findChild(QQuickItem, "iconBreadcrumb")
        assert _wait_for(lambda: _breadcrumb_button(breadcrumb, "Home") is not None)
        breadcrumb_button = _breadcrumb_button(breadcrumb, "Home")
        breadcrumb_icon = breadcrumb_button.findChild(
            QQuickItem, "buttonContentIcon"
        )
        breadcrumb_text = breadcrumb_button.findChild(
            QQuickItem, "buttonContentText"
        )
        assert breadcrumb_icon is not None and breadcrumb_text is not None
        assert breadcrumb_icon.mapToItem(breadcrumb_button, QPointF()).x() \
            + breadcrumb_icon.width() \
            <= breadcrumb_text.mapToItem(breadcrumb_button, QPointF()).x()

        paginator = root.findChild(QQuickItem, "paginator")
        for icon_name in ("ChevronLeft", "ChevronRight"):
            arrow_button = _paginator_button(paginator, icon_name)
            arrow_icon = arrow_button.findChild(
                QQuickItem, "buttonContentIcon"
            )
            assert arrow_icon is not None
            arrow_origin = arrow_icon.mapToItem(arrow_button, QPointF())
            assert arrow_origin.x() + arrow_icon.width() / 2 == \
                pytest.approx(arrow_button.width() / 2)
            # The icon sits centred inside the 1px-smaller content layer, so on a host
            # that snaps that layer to whole pixels the centre lands 0.5px off the
            # button centre (observed on Linux CI: 15.5 vs 16.0). Keep the centring
            # contract and allow for that platform pixel snapping.
            # 图标居中于比按钮矮 1px 的内容层；宿主把该层吸附到整像素时，中心会偏离按钮
            # 中心 0.5px（Linux CI 实测 15.5 对 16.0）。保留居中契约并容许该平台像素吸附。
            assert arrow_origin.y() + arrow_icon.height() / 2 == \
                pytest.approx(arrow_button.height() / 2, abs=0.5)
        assert QMetaObject.invokeMethod(button, "click")
        _pump()
        assert actions == [(0, "Open")]
        assert commands == [(0, "Open")]
        assert warnings == []
        assert _new_visible_windows(windows_before, root) == []
    finally:
        _dispose_scene(engine, component, root)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_command_bar_more_controls_load_on_demand_and_open(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, warnings = _create_scene()
    wide_core = root.findChild(QQuickItem, "wideCore")
    narrow_core = root.findChild(QQuickItem, "narrowCore")
    disabled_core = root.findChild(QQuickItem, "disabledCore")
    empty_core = root.findChild(QQuickItem, "emptyCore")
    secondary_actions = []
    wide_core.secondaryActionTriggered.connect(
        lambda index, action: secondary_actions.append(
            (index, _variant(action)["text"])
        )
    )
    try:
        wide_loader = _more_loader(wide_core)
        narrow_loader = _more_loader(narrow_core)
        disabled_loader = _more_loader(disabled_core)
        empty_loader = _more_loader(empty_core)
        assert wide_loader.property("item") is not None
        assert narrow_loader.property("item") is not None
        assert disabled_loader.property("item") is None
        assert empty_loader.property("item") is None

        more_button = wide_core.findChild(QQuickItem, "commandBarMoreButton")
        more_menu = wide_core.findChild(QQuickItem, "commandBarMoreMenu")
        assert more_button is not None
        assert more_menu is not None
        assert QMetaObject.invokeMethod(more_button, "click")
        assert _wait_for(lambda: more_menu.property("isOpen"))
        popup_windows = _new_visible_windows(windows_before, root)
        assert len(popup_windows) == 1
        assert more_menu.property("popupHeight") >= 6 * 32

        settings_action = next(
            (
                item
                for item in _visual_descendants(popup_windows[0].contentItem())
                if item.objectName() == "commandBarSecondaryAction_0"
            ),
            None,
        )
        assert settings_action is not None
        assert settings_action.property("text") == "Settings"
        visual_secondary_actions = [
            item
            for item in _visual_descendants(popup_windows[0].contentItem())
            if item.objectName().startswith("commandBarSecondaryAction_")
        ]
        assert len(visual_secondary_actions) == 6
        assert all(item.isVisible() for item in visual_secondary_actions)
        assert QMetaObject.invokeMethod(settings_action, "triggered")
        assert _wait_for(lambda: secondary_actions == [(0, "Settings")])
        assert _wait_for(lambda: not more_menu.property("isOpen"))
        assert _wait_for(lambda: _new_visible_windows(windows_before, root) == [])
        assert warnings == []
    finally:
        _dispose_scene(engine, component, root)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_command_bar_open_menu_is_destroyed_when_more_controls_deactivate(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, warnings = _create_scene()
    wide_core = root.findChild(QQuickItem, "wideCore")
    loader = _more_loader(wide_core)
    more_button = wide_core.findChild(QQuickItem, "commandBarMoreButton")
    more_menu = wide_core.findChild(QQuickItem, "commandBarMoreMenu")
    try:
        assert loader.property("item") is not None
        assert QMetaObject.invokeMethod(more_button, "click")
        assert _wait_for(lambda: more_menu.property("isOpen"))
        popup_windows = _new_visible_windows(windows_before, root)
        assert len(popup_windows) == 1
        opened_popup = popup_windows[0]

        wide_core.setProperty("secondaryCommands", [])
        assert _wait_for(lambda: loader.property("item") is None)
        assert _wait_for(
            lambda: all(
                window is not opened_popup
                for window in QGuiApplication.topLevelWindows()
            )
        )
        assert _new_visible_windows(windows_before, root) == []
        assert warnings == []
    finally:
        _dispose_scene(engine, component, root)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_command_bar_sources_follow_conventions():
    for source_path in SOURCE_PATHS:
        source = source_path.read_text(encoding="utf-8")
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        violations = scan_source_text(source, path)
        assert [
            violation
            for violation in violations
            if violation.rule in {"QML008", "QML009"}
        ] == []
