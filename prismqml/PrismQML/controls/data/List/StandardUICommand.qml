// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "_internal/StandardCommandTable.js" as StandardCommandTable

// StandardUICommand - Predefined standard command 预定义标准命令
// Mirrors the public capability surface of menus/Action.qml (text / icon / shortcut /
// toolTip / checkable / checked / actionId / enabled / triggered), so applyTo() can
// drive an existing Action row without this task touching Action.qml.
// 对齐 menus/Action.qml 的公开能力面 (text / icon / shortcut / toolTip / checkable /
// checked / actionId / enabled / triggered), 因此 applyTo() 可以驱动既有 Action 行,
// 本任务无需改动 Action.qml。
// Kinds 种类: cut / copy / paste / undo / redo / select_all.
QtObject {
    id: command

    // ==================== Public Props 公开属性 ====================
    property string kind: "copy"
    // Preset text unless the consumer overrides it 消费方未覆盖时使用预设文本
    property string text: command._preset ? command._preset.label : ""
    property string icon: command._icons[command.kind] !== undefined
        ? command._icons[command.kind] : ""
    property string shortcut: command._preset ? command._preset.shortcut : ""
    property string toolTip: ""
    property bool enabled: true
    property bool checkable: false
    property bool checked: false

    // ==================== Readonly State 只读状态 ====================
    readonly property var _preset: StandardCommandTable.preset(command.kind)
    // Enums and StandardKey are not reachable from a library JS file
    // 库 JS 文件访问不到 Enums 与 StandardKey
    readonly property var _icons: ({
        "cut": Enums.icon.cut,
        "copy": Enums.icon.copy,
        "paste": Enums.icon.clipboard,
        "undo": Enums.icon.arrow_undo,
        "redo": Enums.icon.arrow_redo,
        "select_all": Enums.icon.select_all_on
    })
    readonly property var _standardKeys: ({
        "cut": StandardKey.Cut,
        "copy": StandardKey.Copy,
        "paste": StandardKey.Paste,
        "undo": StandardKey.Undo,
        "redo": StandardKey.Redo,
        "select_all": StandardKey.SelectAll
    })
    readonly property string commandId: "standard." + command.kind
    // Qt StandardKey value for a real Shortcut binding 真实 Shortcut 绑定用的 StandardKey 值
    readonly property int standardKey: command._standardKeys[command.kind] !== undefined
        ? command._standardKeys[command.kind] : StandardKey.UnknownKey
    readonly property bool isStandardKind: command._preset !== null
    // Every predefined kind 全部预定义种类
    readonly property var knownKinds: StandardCommandTable.kinds()

    // ==================== Signals 信号 ====================
    signal triggered()

    // ==================== Public Methods 公开方法 ====================
    // Raise triggered() when the command is enabled 命令可用时发出 triggered()
    function trigger() {
        if (!command.enabled) return false
        command.triggered()
        return true
    }

    // Copy this command onto an existing Action instance 把命令写入既有 Action 实例
    function applyTo(action) {
        if (!action) return null
        action.text = command.text
        action.icon = command.icon
        action.shortcut = command.shortcut
        action.toolTip = command.toolTip
        action.actionId = command.commandId
        action.enabled = command.enabled
        action.checkable = command.checkable
        action.checked = command.checked
        return action
    }
}
