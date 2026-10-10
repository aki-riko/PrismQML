# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""StandardUICommand presets and Action integration. StandardUICommand 预设与 Action 集成。"""

from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QTimer,
    QUrl,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem

from prismqml import configure_qml_environment, register_types


ROOT = Path(__file__).resolve().parents[2]

SCENE = b"""
import QtQuick
import PrismQML
import "../../prismqml/PrismQML/controls/data/List"
import "../../prismqml/PrismQML/controls/menus"

Item {
    id: root
    objectName: "root"
    width: 200
    height: 200

    readonly property var kinds: cutCommand.knownKinds
    readonly property string cutText: cutCommand.text
    readonly property string cutIcon: cutCommand.icon
    readonly property string cutShortcut: cutCommand.shortcut
    readonly property string cutId: cutCommand.commandId
    readonly property int cutKey: cutCommand.standardKey
    readonly property bool cutStandard: cutCommand.isStandardKind
    readonly property string expectedCutIcon: Enums.icon.cut
    readonly property int expectedCutKey: StandardKey.Cut
    readonly property string expectedPasteIcon: pasteCommand.icon
    readonly property string expectedSelectAllIcon: selectAllCommand.icon
    readonly property string expectedUndoIcon: undoCommand.icon
    readonly property string expectedRedoIcon: redoCommand.icon
    readonly property string copyText: copyCommand.text
    readonly property string copyIcon: copyCommand.icon
    readonly property string copyShortcut: copyCommand.shortcut
    readonly property string copyId: copyCommand.commandId
    readonly property string customText: customCommand.text
    readonly property string customIcon: customCommand.icon
    readonly property bool customStandard: customCommand.isStandardKind
    readonly property int customKey: customCommand.standardKey
    readonly property int unknownKey: StandardKey.UnknownKey
    readonly property string pasteText: pasteCommand.text
    readonly property string undoText: undoCommand.text
    readonly property string redoText: redoCommand.text
    readonly property string selectAllText: selectAllCommand.text

    property int triggeredCount: 0
    property bool lastTriggerResult: false

    function buildAction() {
        copyCommand.applyTo(action)
    }
    function triggerCut() { lastTriggerResult = cutCommand.trigger() }
    function disableCut() { cutCommand.enabled = false }
    function enableCut() { cutCommand.enabled = true }

    StandardUICommand {
        id: cutCommand
        kind: "cut"
        onTriggered: root.triggeredCount += 1
    }

    StandardUICommand {
        id: copyCommand
        kind: "copy"
    }

    StandardUICommand {
        id: pasteCommand
        kind: "paste"
    }

    StandardUICommand {
        id: undoCommand
        kind: "undo"
    }

    StandardUICommand {
        id: redoCommand
        kind: "redo"
    }

    StandardUICommand {
        id: selectAllCommand
        kind: "select_all"
    }

    StandardUICommand {
        id: customCommand
        kind: "not_a_standard_kind"
    }

    Action {
        id: action
        objectName: "action"
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_scene():
    configure_qml_environment()
    engine = QQmlApplicationEngine()
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE, QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "standard-ui-command.qml")))
    for _ in range(100):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    _pump(80)
    return engine, component, root, warnings


def _dispose(qapp, engine, component, root) -> None:
    root.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def test_standard_ui_command_presets_and_action_bridge(qapp):
    """Presets must resolve through Enums and drive a real Action. 预设必须经 Enums 解析并驱动真实 Action。"""
    engine, component, root, warnings = _create_scene()
    try:
        assert root.property("cutText") == "Cut"
        assert root.property("copyText") == "Copy"
        assert root.property("pasteText") == "Paste"
        assert root.property("undoText") == "Undo"
        assert root.property("redoText") == "Redo"
        assert root.property("selectAllText") == "Select All"
        assert root.property("cutShortcut") == "Ctrl+X"
        assert root.property("copyShortcut") == "Ctrl+C"
        assert root.property("cutId") == "standard.cut"
        assert root.property("copyId") == "standard.copy"

        # Icons come from the Enums icon registry 图标来自 Enums 图标注册表
        assert root.property("cutIcon") == root.property("expectedCutIcon")
        assert root.property("cutIcon") == "Cut"
        assert root.property("copyIcon") == "Copy"
        assert root.property("expectedPasteIcon") == "Clipboard"
        assert root.property("expectedUndoIcon") == "ArrowUndo"
        assert root.property("expectedRedoIcon") == "ArrowRedo"
        assert root.property("expectedSelectAllIcon") == "SelectAllOn"
        assert root.property("cutStandard") is True
        assert root.property("cutKey") == root.property("expectedCutKey")

        # The predefined set is enumerated 预定义集合可枚举
        assert _variant(root.property("kinds")) == [
            "copy",
            "cut",
            "paste",
            "redo",
            "select_all",
            "undo",
        ]

        # Unknown kinds stay inert instead of inventing presets 未知种类保持惰性
        assert root.property("customStandard") is False
        assert root.property("customText") == ""
        assert root.property("customIcon") == ""
        assert root.property("customKey") == root.property("unknownKey")

        # applyTo() drives a real menus/Action row 把命令写入真实 Action 行
        action = root.findChild(QQuickItem, "action")
        assert action is not None
        assert QMetaObject.invokeMethod(root, "buildAction")
        _pump(40)
        assert action.property("text") == root.property("copyText")
        assert action.property("icon") == root.property("copyIcon")
        assert action.property("shortcut") == root.property("copyShortcut")
        assert action.property("actionId") == root.property("copyId")
        assert action.property("enabled") is True
        assert action.property("checkable") is False

        # trigger() honours the enabled gate 触发遵守可用性门
        assert root.property("triggeredCount") == 0
        assert QMetaObject.invokeMethod(root, "triggerCut")
        assert root.property("lastTriggerResult") is True
        assert root.property("triggeredCount") == 1
        assert QMetaObject.invokeMethod(root, "disableCut")
        assert QMetaObject.invokeMethod(root, "triggerCut")
        assert root.property("lastTriggerResult") is False
        assert root.property("triggeredCount") == 1
        assert QMetaObject.invokeMethod(root, "enableCut")
        assert QMetaObject.invokeMethod(root, "triggerCut")
        assert root.property("lastTriggerResult") is True
        assert root.property("triggeredCount") == 2
        assert warnings == []
    finally:
        _dispose(qapp, engine, component, root)
