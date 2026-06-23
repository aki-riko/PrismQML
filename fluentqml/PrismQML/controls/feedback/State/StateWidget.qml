// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../icons"
import "../../buttons"
import "../../data/Label"

// StateWidget - Unified state display component 统一状态展示组件
// Integrates EmptyState, ResultState, EmptyDataState, OfflineState 整合所有状态组件
Item {
    id: control
    
    // ==================== Props 属性 ====================
    property int stateType: Enums.state.type_no_data  // State type 状态类型
    property string severity: "info"  // For type_result: success/error/warning/info/empty/loading 结果类型
    property string icon: ""  // Custom icon 自定义图标
    property string title: ""  // Title text 标题文本
    property string description: ""  // Description text 描述文本
    property string actionText: ""  // Action button text 操作按钮文本
    property int imageWidth: Enums.controlSize.stateImageSize  // Icon container width 图标容器宽度
    property int imageHeight: Enums.controlSize.stateImageSize  // Icon container height 图标容器高度
    
    // ==================== Signals 信号 ====================
    signal actionClicked()
    
    // ==================== Computed Props 计算属性 ====================
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
                return "WifiOff"
            default:
                return "Info"
        }
    }
    
    readonly property string _defaultTitle: {
        switch (stateType) {
            case Enums.state.type_result:
                switch (severity) {
                    case "success": return "提交成功"
                    case "error": return "操作失败"
                    case "warning": return "警告"
                    default: return ""
                }
            case Enums.state.type_no_data:
                return "No Data"
            case Enums.state.type_no_internet:
                return "No Internet Connection"
            default:
                return ""
        }
    }
    
    readonly property string _defaultActionText: {
        if (stateType === Enums.state.type_no_internet) {
            return "Retry"
        }
        return ""
    }
    
    readonly property bool _isResultType: stateType === Enums.state.type_result
    readonly property bool _hasCircleIcon: _isResultType
    
    // ==================== Size 尺寸 ====================
    implicitWidth: 300
    implicitHeight: contentCol.implicitHeight
    
    // ==================== Layout 布局 ====================
    Column {
        id: contentCol
        anchors.centerIn: parent
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
                visible: _hasCircleIcon
                
                Icon {
                    anchors.centerIn: parent
                    iconSize: Enums.controlSize.flyoutIconSize
                    color: _stateColor
                    icon: control.icon || _defaultIcon
                }
                
                RotationAnimation on rotation {
                    running: severity === "loading"
                    from: 0; to: 360
                    duration: Enums.duration.dialog * 3.75
                    loops: Animation.Infinite
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
            type: _isResultType ? Enums.label.type_title_large : Enums.label.type_subtitle
            anchors.horizontalCenter: parent.horizontalCenter
            text: control.title || _defaultTitle
            color: _isResultType ? Enums.textColor.primary : Enums.textColor.tertiary
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
            width: Math.min(implicitWidth, _isResultType ? Enums.controlSize.stateDescMaxWidth : Enums.controlSize.stateDescEmptyWidth)
            visible: text !== ""
        }
        
        // Action button 操作按钮
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            width: actionBtnText.implicitWidth + (_isResultType ? Enums.controlSize.stateButtonPaddingLarge : Enums.controlSize.stateButtonPaddingSmall)
            height: _isResultType ? Enums.controlSize.topNavItemHeight : Enums.controlSize.emptyStateButtonHeight
            radius: Enums.radius.small
            color: actionArea.pressed ? Qt.darker(Enums.accentColor, 1.1) : (actionArea.containsMouse ? Qt.lighter(Enums.accentColor, 1.1) : Enums.accentColor)
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
