// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../icons"
import "../../buttons"
import "../../data/Label"

// StateWidget - Unified state display component 统一状态展示组件
// Integrates EmptyState, ResultState, EmptyDataState, OfflineState 整合所有状态组件
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property int stateType: Enums.state.type_no_data  // State type 状态类型
    property string severity: "info"  // For type_result: success/error/warning/info/empty/loading 结果类型
    property string icon: ""  // Custom icon 自定义图标
    property string title: ""  // Title text 标题文本
    property string description: ""  // Description text 描述文本
    property string actionText: ""  // Action button text 操作按钮文本
    property int imageWidth: Enums.controlSize.stateImageSize  // Icon container width 图标容器宽度
    property int imageHeight: Enums.controlSize.stateImageSize  // Icon container height 图标容器高度
    
    // ==================== Readonly State 只读状态 ====================
    readonly property color _stateColor: Enums.statusLevel.getColor(severity)
    
    readonly property string _defaultIcon: {
        switch (stateType) {
            case Enums.state.type_result:
                switch (severity) {
                    case "success": return "Checkmark"
                    case "error": return "Dismiss"
                    case "warning": return "Warning"
                    case "empty": return "MailInboxDismiss"
                    case "loading": return "ArrowSync"
                    default: return "Info"
                }
            case Enums.state.type_no_data:
                return "MailInboxDismiss"
            case Enums.state.type_no_internet:
                return "WiFiOff"
            default:
                return "Info"
        }
    }
    
    readonly property string _defaultTitle: {
        Translator._v
        switch (stateType) {
            case Enums.state.type_result:
                switch (severity) {
                    case "success": return Translator.tr("submit_success")
                    case "error": return Translator.tr("operation_failed")
                    case "warning": return Translator.tr("warning")
                    default: return ""
                }
            case Enums.state.type_no_data:
                return Translator.tr("no_data")
            case Enums.state.type_no_internet:
                return Translator.tr("no_internet")
            default:
                return ""
        }
    }
    
    readonly property string _defaultActionText: {
        Translator._v
        if (stateType === Enums.state.type_no_internet) {
            return Translator.tr("retry")
        }
        return ""
    }
    
    readonly property bool _isResultType: stateType === Enums.state.type_result
    readonly property bool _hasCircleIcon: _isResultType

    // ==================== Signals 信号 ====================
    signal actionClicked()
    
    // ==================== Size 尺寸 ====================
    implicitWidth: 300
    implicitHeight: contentCol.implicitHeight
    
    // ==================== Content 内容 ====================
    Column {
        id: contentCol
        anchors.centerIn: parent
        width: control.width
        spacing: _isResultType ? Enums.spacing.xl : Enums.spacing.l
        
        // Icon container 图标容器
        Item {
            anchors.horizontalCenter: parent.horizontalCenter
            width: _hasCircleIcon ? Enums.controlSize.resultStateIconSize : control.imageWidth
            height: _hasCircleIcon ? Enums.controlSize.resultStateIconSize : control.imageHeight
            
            // Circle background for result type 结果类型的圆形背景
            Rectangle {
                anchors.fill: parent
                radius: width / 2
                color: Enums.stateColor.accentSubtle
                visible: _hasCircleIcon && severity !== "loading"
                
                Icon {
                    anchors.centerIn: parent
                    iconSize: Enums.controlSize.flyoutIconSize
                    color: _stateColor
                    icon: control.icon || _defaultIcon
                }
                
            }

            // Standard loading ring 标准加载环
            Loader {
                anchors.fill: parent
                active: control._isResultType && control.severity === "loading"
                sourceComponent: ProgressRing {
                    indeterminate: true
                    color: control._stateColor
                }
            }
            
            // Normal icon for other types 其他类型的普通图标
            Icon {
                anchors.centerIn: parent
                iconSize: Math.min(parent.width, parent.height) * 0.6
                color: Enums.textColor.tertiary
                icon: control.icon || _defaultIcon
                visible: !_hasCircleIcon
            }
        }
        
        // Title 标题
        Label {
            objectName: "stateTitle"
            type: _isResultType ? Enums.label.type_title : Enums.label.type_subtitle
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width
            text: control.title || _defaultTitle
            color: _isResultType ? Enums.textColor.primary : Enums.textColor.tertiary
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            maximumLineCount: 2
            elide: Text.ElideRight
            visible: text !== ""
        }
        
        // Description 描述
        Label {
            type: _isResultType ? Enums.label.type_body : Enums.label.type_caption
            anchors.horizontalCenter: parent.horizontalCenter
            text: control.description
            color: _isResultType ? Enums.textColor.tertiary : Enums.stateColor.textMedium
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            width: Math.min(parent.width, _isResultType ? Enums.controlSize.stateDescMaxWidth : Enums.controlSize.stateDescEmptyWidth)
            visible: text !== ""
        }
        
        // Action button 操作按钮
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            width: actionBtnText.implicitWidth + (_isResultType ? Enums.controlSize.stateButtonPaddingLarge : Enums.controlSize.stateButtonPaddingSmall)
            height: _isResultType ? Enums.controlSize.topNavItemHeight : Enums.controlSize.emptyStateButtonHeight
            radius: Enums.radius.small
            color: actionArea.pressed ? Enums.accentColorDark : (actionArea.containsMouse ? Enums.accentColorLight : Enums.accentColor)
            visible: (control.actionText || _defaultActionText) !== ""
            
            Label {
                id: actionBtnText
                type: _isResultType ? Enums.label.type_body : Enums.label.type_caption
                anchors.centerIn: parent
                text: control.actionText || _defaultActionText
                color: Enums.accentForeground
            }
            
            MouseArea {
                id: actionArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: control.actionClicked()
            }
        }
    }
}
