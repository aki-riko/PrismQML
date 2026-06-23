// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../../.."       // → qml/ (FluentEnums)
import "../../../icons"    // → controls/icons/
import "../../../menus"    // → controls/menus/
import "../../../buttons"  // → controls/buttons/
import "../../../containers/Separator"
import "../../../data"     // → controls/data/

// CommandBarCore - Base class for command bar 命令栏基类
// Refactored to use Button for stable hover 重构使用Button实现稳定hover
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property var primaryCommands: []
    property var secondaryCommands: []
    property int iconSize: Enums.iconSize.m
    property int buttonStyle: Enums.commandBar.style_icon_only
    property bool tight: false
    property int spacing: Enums.spacing.xs
    property bool disableOverflow: false
    
    // ==================== Signals 信号 ====================
    signal actionTriggered(int index, var action)
    signal secondaryActionTriggered(int index, var action)
    
    // ==================== Size 尺寸 ====================
    implicitWidth: contentRow.implicitWidth
    implicitHeight: Enums.controlSize.commandBarButtonSize
    
    // ==================== Private Props 私有属性 ====================
    property var _visibleCommands: primaryCommands
    property var _hiddenCommands: []
    property bool _hasOverflow: false

    // ==================== Methods 方法 ====================
    function _updateOverflow() {
        if (disableOverflow || width <= 0) {
            _visibleCommands = primaryCommands
            _hiddenCommands = []
            _hasOverflow = false
            return
        }

        var moreButtonWidth = Enums.controlSize.commandBarMoreWidth + Enums.spacing.xs
        var hasSecondary = secondaryCommands.length > 0

        var totalContentWidth = 0
        for (var i = 0; i < primaryCommands.length; i++) {
            var cmd = primaryCommands[i]
            var btnWidth = cmd.separator ? Enums.controlSize.commandBarSeparatorWidth : Enums.controlSize.commandBarButtonSize
            if (buttonStyle === Enums.commandBar.style_text_beside && cmd.text) btnWidth += Enums.controlSize.commandBarMoreWidth
            totalContentWidth += btnWidth + (i > 0 ? spacing : 0)
        }

        var availableWithoutMore = hasSecondary ? width - moreButtonWidth : width
        if (totalContentWidth <= availableWithoutMore) {
            _visibleCommands = primaryCommands
            _hiddenCommands = []
            _hasOverflow = false
            return
        }

        var availableWidth = width - moreButtonWidth
        var currentWidth = 0
        var visibleCount = 0

        for (var j = 0; j < primaryCommands.length; j++) {
            var cmd2 = primaryCommands[j]
            var btnWidth2 = cmd2.separator ? Enums.controlSize.commandBarSeparatorWidth : Enums.controlSize.commandBarButtonSize
            if (buttonStyle === Enums.commandBar.style_text_beside && cmd2.text) btnWidth2 += Enums.controlSize.commandBarMoreWidth

            var nextWidth = currentWidth + btnWidth2 + (j > 0 ? spacing : 0)
            if (nextWidth > availableWidth) break
            currentWidth = nextWidth
            visibleCount++
        }

        visibleCount = Math.max(1, visibleCount)

        if (visibleCount < primaryCommands.length) {
            _visibleCommands = primaryCommands.slice(0, visibleCount)
            _hiddenCommands = primaryCommands.slice(visibleCount)
            _hasOverflow = true
        } else {
            _visibleCommands = primaryCommands
            _hiddenCommands = []
            _hasOverflow = false
        }
    }

    // ==================== Layout 布局 ====================
    Row {
        id: contentRow
        anchors.verticalCenter: parent.verticalCenter
        spacing: control.spacing
        
        // Primary command buttons 主命令按钮
        Repeater {
            model: _visibleCommands
            
            Loader {
                // ✅ 2026-02-02: 支持三种类型：separator、widget、button
                sourceComponent: {
                    if (modelData.separator) return separatorComponent
                    if (modelData.widget && modelData.qmlItem) return widgetComponent
                    return buttonComponent
                }
                property var commandData: modelData
                property int commandIndex: index
            }
        }
        
        // More button 更多按钮
        Button {
            id: moreButton
            visible: _hasOverflow || secondaryCommands.length > 0
            style: Enums.button.style_transparent
            icon: Enums.icon.more_horizontal
            iconSize: Enums.iconSize.m
            implicitWidth: Enums.controlSize.commandBarMoreWidth
            implicitHeight: Enums.controlSize.commandBarButtonSize
            flat: true
            onClicked: moreMenu.show(moreButton)
        }
    }  // Row
    
    // More Menu (outside Row, use popup with position) 更多菜单（Row外部，使用popup定位）
    ContextMenu {
        id: moreMenu
        autoBindRightClick: false
        
        Repeater {
            model: _hiddenCommands
            Action {
                text: modelData.text || ""
                icon: modelData.icon || ""
                enabled: modelData.enabled !== false
                visible: !modelData.separator
                onTriggered: {
                    var originalIndex = primaryCommands.indexOf(modelData)
                    control.actionTriggered(originalIndex, modelData)
                    moreMenu.close()
                }
            }
        }
        
        MenuSeparator {
            visible: _hiddenCommands.length > 0 && secondaryCommands.length > 0
        }
        
        Repeater {
            model: secondaryCommands
            Action {
                text: modelData.text || ""
                icon: modelData.icon || ""
                enabled: modelData.enabled !== false
                onTriggered: {
                    control.secondaryActionTriggered(index, modelData)
                    moreMenu.close()
                }
            }
        }
    }
    
    // ==================== Components 组件 ====================
    
    // Command button 命令按钮
    Component {
        id: buttonComponent
        Item {
            width: cmdBtn.implicitWidth
            height: cmdBtn.implicitHeight
            
            // Hidden text for measuring 用于测量的隐藏文本
            Label {
                id: btnTextMeasure
                visible: false
                type: Enums.label.type_caption
                text: commandData.text || ""
            }
            
            Button {
                id: cmdBtn
                style: Enums.button.style_transparent
                flat: true
                enabled: commandData.enabled !== false
                icon: commandData.icon || ""
                text: buttonStyle === Enums.commandBar.style_text_beside ? (commandData.text || "") : ""
                iconSize: control.iconSize
                implicitWidth: _calcButtonWidth()
                implicitHeight: Enums.controlSize.commandBarButtonSize
                
                function _calcButtonWidth() {
                    if (buttonStyle === Enums.commandBar.style_icon_only) return Enums.controlSize.commandBarButtonSize
                    if (buttonStyle === Enums.commandBar.style_text_beside) return btnTextMeasure.implicitWidth + iconSize + Enums.controlSize.buttonHeight
                    return Math.max(Enums.controlSize.commandBarButtonSize, btnTextMeasure.implicitWidth + Enums.spacing.xl)
                }
                
                onClicked: control.actionTriggered(commandIndex, commandData)
            }
        }
    }
    
    // Separator 分隔线
    Component {
        id: separatorComponent
        Rectangle {
            width: Enums.controlSize.commandBarSeparatorWidth
            height: Enums.controlSize.commandBarButtonSize
            color: Enums.transparent

            Separator {
                type: Enums.separator.vertical
                anchors.centerIn: parent
                lineLength: parent.height - Enums.spacing.xs
                lineColor: Enums.stateColor.border
            }
        }
    }
    
    // ✅ 2026-02-02: Widget wrapper 嵌入式组件容器
    // 用于在 CommandBar 中嵌入自定义 QML 组件
    Component {
        id: widgetComponent
        Item {
            id: widgetWrapper
            // 尺寸跟随嵌入的组件
            implicitWidth: commandData.qmlItem ? commandData.qmlItem.width : 0
            implicitHeight: commandData.qmlItem ? commandData.qmlItem.height : Enums.controlSize.commandBarButtonSize
            width: implicitWidth
            height: implicitHeight
            
            Component.onCompleted: {
                // 将外部 QML 组件重新设置父级到这个容器
                if (commandData.qmlItem) {
                    commandData.qmlItem.parent = widgetWrapper
                    commandData.qmlItem.anchors.verticalCenter = widgetWrapper.verticalCenter
                }
            }
        }
    }
    
    // ==================== Overflow Logic 溢出逻辑 ====================
    onWidthChanged: _updateOverflow()
    onPrimaryCommandsChanged: _updateOverflow()

    Component.onCompleted: _updateOverflow()
}
