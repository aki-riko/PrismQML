// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."
import "../data"
import "../buttons/Button"

// MessageBox - Message dialog with title and content 带标题和内容的消息对话框
DialogBoxCore {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property string title: ""                    // Dialog title 对话框标题
    property string content: ""                  // Dialog content 对话框内容
    property bool contentCopyable: false         // Allow copy content 允许复制内容
    property int minWidth: 288                   // Minimum width 最小宽度 (8px 网格对齐)
    property string confirmText: qsTr("OK")          // Confirm button text 确定按钮文字
    property string cancelText: qsTr("Cancel")   // Cancel button text 取消按钮文字
    property bool yesButtonVisible: true         // Show yes button 显示确定按钮
    property bool cancelButtonVisible: true      // Show cancel button 显示取消按钮
    
    // ==================== Internal 内部属性 ====================
    readonly property int _contentWidth: Math.max(titleLabel.implicitWidth, contentLabel.implicitWidth, textLayout.implicitWidth)
    readonly property int _contentHeight: titleLabel.implicitHeight + contentLabel.implicitHeight + 12
    
    // ==================== Footer 按钮组 ====================
    footer: Component {
        Row {
            property var dialog  // 由 Loader 自动注入
            spacing: Enums.spacing.l
            
            // Yes Button (Primary) 确定按钮
            ButtonCore {
                objectName: "yesButton"
                visible: control.yesButtonVisible
                text: control.confirmText
                style: Enums.button.style_primary
                width: Enums.dialog.buttonWidth
                height: Enums.dialog.buttonHeight
                onClicked: {
                    if (control.validate()) {
                        control.accept()
                    }
                }
            }
            
            // Cancel Button 取消按钮
            ButtonCore {
                objectName: "cancelButton"
                visible: control.cancelButtonVisible
                text: control.cancelText
                style: Enums.button.style_default
                width: Enums.dialog.buttonWidth
                height: Enums.dialog.buttonHeight
                onClicked: control.reject()
            }
        }
    }
    
    // ==================== Content Area 内容区域 ====================
    Column {
        id: textLayout
        objectName: "contentLayout"
        width: Math.max(control.minWidth, control._contentWidth)
        spacing: Enums.spacing.l
        
        // Title label 标题标签
        Label {
            id: titleLabel
            text: control.title
            type: Enums.label.type_subtitle
            color: Enums.isDark ? "white" : "black"
            visible: text !== ""
            wrapMode: Text.WordWrap
            width: parent.width
        }
        
        // Content label 内容标签
        TextEdit {
            id: contentLabel
            text: control.content
            visible: text !== ""
            wrapMode: Text.WordWrap
            width: Math.min(implicitWidth, 400)
            readOnly: true
        }
    }
}
