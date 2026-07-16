// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick.Effects
import "../../.."
import "../../../effects"
import "../../icons"
import "../../buttons"
import "../../data"
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖
import QtQuick.Window  // 置于库import后:去前缀后保原生Window不被库覆盖

// DesktopNotification - Desktop notification (standalone window) 桌面通知
// Popup at screen corners, like system notification 屏幕角落弹出
Window {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property string title: ""
    property string message: ""
    property string severity: "info"  // info, success, warning, error
    property int duration: Enums.duration.notification
    property bool closable: true
    property int position: Enums.notification.posBottomRight  // 0=TOP_LEFT, 1=TOP, 2=TOP_RIGHT, 3=BOTTOM_LEFT, 4=BOTTOM, 5=BOTTOM_RIGHT

    // Custom content slot 自定义内容插槽
    // Inject custom widget (e.g. confirm button) below message 在消息下方注入自定义控件（如确认按钮）
    property alias customContent: customContentLoader.sourceComponent
    readonly property bool hasCustomContent: customContentLoader.sourceComponent !== null && customContentLoader.item !== null

    // ==================== Internal Props 内部属性 ====================
    readonly property int _notificationRadius: Enums.isPrismDesign ? Enums.prismDesign.radiusPopup : Enums.radius.large
    readonly property int _notificationIconRadius: Enums.isPrismDesign ? Enums.prismDesign.radiusControl : Enums.radius.large
    readonly property color _notificationBackground: Enums.isPrismDesign ? Enums.toastCardColor : Enums.cardColor
    readonly property int _notificationBorderWidth: Enums.isNeobrutalism ? Enums.neo.borderWidth : Enums.border.thin
    readonly property color _notificationBorderColor: Enums.stateColor.border
    readonly property color _notificationMessageColor: Enums.stateColor.notificationText
    readonly property color _notificationShadowColor: Enums.shadow.level8.color
    readonly property int _notificationShadowBlur: Enums.shadow.level8.blur
    readonly property int _notificationShadowOffset: Enums.shadow.level8.offset
    // Use shared severity helper 使用共享的语义辅助函数
    readonly property int _severityLevel: Enums.notification.getSeverityLevel(severity)
    readonly property color severityColor: Enums.statusLevel.getColorByLevel(_severityLevel)
    readonly property string severityIconName: {
        switch (severity) {
            case "success": return "Checkmark"
            case "warning": return "Warning"
            case "error": return "Dismiss"
            default: return "Info"
        }
    }
    // Use shared animation config 使用共享动画配置
    readonly property real _slideOffset: width + Enums.notification.layout.edgeMargin
    // Vertical slide needs larger offset for better bounce effect 垂直滑动需要更大偏移以获得更好的回弹效果
    readonly property real _slideOffsetY: height + Enums.notification.layout.verticalSlideExtra
    readonly property bool _isTop: Enums.notification.isTop(position)
    readonly property bool _isLeft: Enums.notification.isLeft(position)
    readonly property bool _isRight: Enums.notification.isRight(position)
    readonly property bool _isCenter: Enums.notification.isCenter(position)
    readonly property int _showEasing: Enums.notification.animation.showEasing
    readonly property real _showOvershoot: Enums.notification.animation.showOvershoot
    readonly property int _hideEasing: Enums.notification.animation.hideEasing
    property real _baseX: 0
    property real _baseY: 0

    // ==================== Signals 信号 ====================
    signal closed()
    signal clicked()

    // ==================== Public Methods 公开方法 ====================
    function show() {
        _calculateBasePosition()
        // Set initial position (from outside edge) 设置初始位置（从边缘外）
        if (_isLeft) {
            x = _baseX - _slideOffset
            y = _baseY
        } else if (_isRight) {
            x = _baseX + _slideOffset
            y = _baseY
        } else if (_isCenter) {
            x = _baseX
            y = _isTop ? _baseY - _slideOffsetY : _baseY + _slideOffsetY
        }
        visible = true
        showAnim.start()
        if (duration > 0) autoCloseTimer.start()
    }

    function hide() {
        hideAnim.start()
    }

    // ==================== Internal Methods 内部方法 ====================
    function _calculateBasePosition() {
        var screen = Screen
        var margin = Enums.notification.layout.screenMargin
        var taskbarOffset = Enums.notification.layout.taskbarOffset
        var sw = screen.width
        var sh = screen.height

        switch (position) {
            case 0: _baseX = margin; _baseY = margin; break
            case 1: _baseX = (sw - width) / 2; _baseY = margin; break
            case 2: _baseX = sw - width - margin; _baseY = margin; break
            case 3: _baseX = margin; _baseY = sh - height - margin - taskbarOffset; break
            case 4: _baseX = (sw - width) / 2; _baseY = sh - height - margin - taskbarOffset; break
            case 5: default: _baseX = sw - width - margin; _baseY = sh - height - margin - taskbarOffset; break
        }
    }

    // Window settings 窗口设置
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
    visible: false  // Default hidden, call show() to display 默认隐藏，调用show()显示
    color: Enums.transparent
    width: Enums.controlSize.desktopNotificationWidth
    height: Math.max(
        Enums.controlSize.toastHeight,
        contentCol.implicitHeight
            + (hasCustomContent ? customContentLoader.height + Enums.spacing.m : 0)
            + Enums.controlSize.dialogButtonHeight
    )

    // ==================== Content 内容 ====================
    Timer { id: autoCloseTimer; interval: duration; onTriggered: control.hide() }

    // Animations 动画
    ParallelAnimation {
        id: showAnim
        NumberAnimation { 
            target: control; property: "x"; to: control._baseX
            duration: Enums.notification.animation.showDuration
            easing.type: control._showEasing; easing.overshoot: control._showOvershoot
        }
        NumberAnimation { 
            target: control; property: "y"; to: control._baseY
            duration: Enums.notification.animation.showDuration
            easing.type: control._showEasing; easing.overshoot: control._showOvershoot
        }
    }
    
    ParallelAnimation {
        id: hideAnim
        onFinished: { control.visible = false; control.closed() }

        NumberAnimation { 
            target: control; property: "x"
            to: control._isLeft ? control._baseX - control._slideOffset : 
                (control._isRight ? control._baseX + control._slideOffset : control._baseX)
            duration: Enums.notification.animation.hideDuration
            easing.type: control._hideEasing
        }
        NumberAnimation { 
            target: control; property: "y"
            to: control._isCenter ? (control._isTop ? control._baseY - control._slideOffsetY : control._baseY + control._slideOffsetY) : control._baseY
            duration: Enums.notification.animation.hideDuration
            easing.type: control._hideEasing
        }
    }

    // Shadow layer 阴影层
    // Fluent: 模糊阴影; neo: 硬阴影
    RectangularShadow {
        anchors.fill: card
        radius: card.radius
        color: control._notificationShadowColor
        blur: control._notificationShadowBlur
        offset.x: 0
        offset.y: control._notificationShadowOffset
        visible: !Enums.isNeobrutalism
    }

    NeoShadow {
        target: card
        visible: Enums.isNeobrutalism
        z: card.z - 1
    }

    // Notification card 通知卡片
    Rectangle {
        id: card
        anchors.fill: parent
        anchors.margins: Enums.spacing.m
        radius: control._notificationRadius
        color: control._notificationBackground
        border.width: control._notificationBorderWidth
        border.color: control._notificationBorderColor
        
        // Left color bar 左侧色条
        Rectangle {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: Enums.spacing.xs
            color: severityColor
            radius: parent.radius
            
            Rectangle {
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                width: parent.radius
                color: parent.color
            }
        }
        
        // Icon 图标
        Rectangle {
            id: iconRect
            anchors.left: parent.left
            anchors.leftMargin: Enums.spacing.xl
            anchors.top: parent.top
            anchors.topMargin: Enums.spacing.xl
            width: Enums.spacing.xxxl; height: Enums.spacing.xxxl; radius: control._notificationIconRadius
            color: severityColor
            
            Icon {
                anchors.centerIn: parent
                iconSize: Enums.iconSize.xs
                color: Enums.accentForeground
                icon: severityIconName
            }
        }
        
        // Content 内容
        Column {
            id: contentCol
            anchors.left: iconRect.right
            anchors.leftMargin: Enums.spacing.l
            anchors.right: closeBtn.visible ? closeBtn.left : parent.right
            anchors.rightMargin: Enums.spacing.l
            anchors.top: parent.top
            anchors.topMargin: Enums.spacing.xl
            spacing: Enums.spacing.xs
            
            Label {
                text: control.title
                type: Enums.label.type_body_strong
                color: Enums.textColor.primary
                visible: text !== ""
                width: parent.width
                elide: Text.ElideRight
            }
            
            Label {
                text: control.message
                type: Enums.label.type_caption
                color: control._notificationMessageColor
                visible: text !== ""
                width: parent.width
                wrapMode: Text.WordWrap
                maximumLineCount: 3
                elide: Text.ElideRight
            }

            // Custom content slot (e.g. action button) 自定义内容插槽
            Loader {
                id: customContentLoader
                width: parent.width
                visible: item !== null
            }
        }
        
        // Close button 关闭按钮
        CloseButton {
            id: closeBtn
            anchors.right: parent.right
            anchors.rightMargin: Enums.spacing.l
            anchors.top: parent.top
            anchors.topMargin: Enums.spacing.l
            size: Enums.spacing.xxl
            iconSizeValue: Enums.iconSize.tiny
            normalIconColor: Enums.stateColor.scrollThumbHover
            visible: closable
            onClicked: control.hide()
        }
        
        // Click area 点击区域
        MouseArea {
            anchors.fill: parent
            z: Enums.zIndex.background
            onClicked: control.clicked()
        }
    }
}
