// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Layouts
import "../../.."
import "_internal"

// CommandBar - Fluent Design command bar 命令栏
// Type 类型: type_default (transparent), type_view (card with shadow)
// Usage 用法: CommandBar { type: Enums.commandBar.type_view; primaryCommands: [...] }
Item {
    id: control
    
    // ==================== Layout Attached Properties 布局附加属性 ====================
    // 用于父布局的附加属性，让 CommandBar 能够填满可用宽度
    property bool layoutFillWidth: true
    property bool layoutFillHeight: false
    property int layoutAlignment: 0
    Layout.fillWidth: layoutFillWidth
    Layout.fillHeight: layoutFillHeight
    Layout.alignment: layoutAlignment
    
    // ==================== Public Props 公开属性 ====================
    property int type: Enums.commandBar.type_default
    
    // Command data 命令数据
    // Primary commands: [{text, icon, enabled, checkable, checked, separator}]
    property var primaryCommands: []
    property var secondaryCommands: []  // Hidden actions (always in menu) 始终在菜单中的操作
    
    // Style props 样式属性
    property int iconSize: type === Enums.commandBar.type_view ? Enums.iconSize.l : Enums.iconSize.m
    property int buttonStyle: Enums.commandBar.style_icon_only
    property bool tight: type === Enums.commandBar.type_view
    property int spacing: Enums.spacing.xs
    property bool showLabels: false  // Only for type_view 仅用于视图类型
    
    // Convenience alias 便捷别名
    property alias commands: control.primaryCommands
    
    // ==================== Signals 信号 ====================
    signal actionTriggered(int index, var action)
    signal secondaryActionTriggered(int index, var action)
    signal commandClicked(int index, string text)  // Emitted on command activation 命令触发时发出
    
    // ==================== Size 尺寸 ====================
    // Width: fill parent width when in layout 在布局中填充父容器宽度
    implicitWidth: loader.implicitWidth
    implicitHeight: loader.implicitHeight
    
    // Key: width follows parent.width when available (like Widget.qml)
    // 关键：当有父容器时 width 跟随 parent.width（类似 Widget.qml）
    
    // Width defaults to implicitWidth, allowing Layout or anchors to override it.
    // 宽度默认为 implicitWidth，允许 Layout 或 anchors 覆盖它。
    // No explicit width binding here to prevent conflicts.
    // 此处不进行显式 width 绑定以防止冲突。
    
    height: implicitHeight
    
    // ==================== Loader 加载器 ====================
    Loader {
        id: loader
        anchors.fill: parent
        sourceComponent: control.type === Enums.commandBar.type_view ? viewComponent : defaultComponent
    }
    
    // ==================== Default Style Component 默认样式组件 ====================
    Component {
        id: defaultComponent
        CommandBarCore {
            width: parent.width  // Fix: Fill width 修复：填充宽度
            primaryCommands: control.primaryCommands
            secondaryCommands: control.secondaryCommands
            iconSize: control.iconSize
            // ✅ 2026-02-02: showLabels 为 true 时使用 style_text_beside
            buttonStyle: control.showLabels ? Enums.commandBar.style_text_beside : control.buttonStyle
            tight: control.tight
            spacing: control.spacing
            
            onActionTriggered: (index, action) => {
                control.actionTriggered(index, action)
                control.commandClicked(index, action.text || "")
            }
            onSecondaryActionTriggered: (index, action) => control.secondaryActionTriggered(index, action)
        }
    }
    
    // ==================== View Style Component 视图样式组件 ====================
    Component {
        id: viewComponent
        CommandBarSurface {
            width: parent.width  // Fix: Fill width 修复：填充宽度
            primaryCommands: control.primaryCommands
            secondaryCommands: control.secondaryCommands
            iconSize: control.iconSize
            buttonStyle: control.buttonStyle
            tight: control.tight
            spacing: control.spacing
            showLabels: control.showLabels
            
            onActionTriggered: (index, action) => {
                control.actionTriggered(index, action)
                control.commandClicked(index, action.text || "")
            }
            onSecondaryActionTriggered: (index, action) => control.secondaryActionTriggered(index, action)
        }
    }
}
