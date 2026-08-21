// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "_internal" as NotificationInternal

// Toast - Card-style notification 卡片式通知
// Structure: bottom color bar + top white card 底层颜色条+上层卡片
Widget {
    id: control

    // ==================== Public Props 公开属性 ====================
    property string title: ""
    property string message: ""
    property alias text: control.message
    property int duration: Enums.duration.notification
    property string severity: "info"  // info, success, warning, error, attention, processing
    property bool closable: true
    property int position: Enums.notification.posBottomRight  // Nine-grid position from NotificationManager 九宫格位置(0-8)
    property bool desktopMode: false  // Desktop mode skips internal animation 桌面模式跳过内部动画
    
    // Layout properties 布局属性
    property int orient: Qt.Horizontal  // Layout orientation 布局方向 (Qt.Horizontal/Qt.Vertical)
    readonly property bool _isVertical: orient === Qt.Vertical
    // Transparent outer area reserved for shadows; excluded from visual stacking
    // 为阴影保留的透明外围，可见堆叠时不计入间距
    readonly property int _stackTopInset: Enums.spacing.m
    readonly property int _stackBottomInset: Enums.spacing.m
    
    // Custom content 自定义内容
    property alias customContent: contentLayer.customContent  // Custom widget slot 自定义组件插槽
    property bool hasCustomContent: contentLayer.hasCustomContent

    // Animation 动画
    property alias animator: animator  // Expose animator for stack management 暴露动画器供堆叠管理使用
    
    // Custom background 自定义背景色
    property color backgroundColorLight: Enums.transparent  // Custom light theme bg 自定义浅色背景
    property color backgroundColorDark: Enums.transparent   // Custom dark theme bg 自定义深色背景
    readonly property bool _hasCustomBg: backgroundColorLight.a > 0 || backgroundColorDark.a > 0
    readonly property color _cardColor: _hasCustomBg ? (Enums.isDark ? backgroundColorDark : backgroundColorLight) : Enums.toastCardColor
    readonly property int _toastRadius: Enums.surfaceRadius(Enums.radius.small)
    readonly property int _toastColorBarRadius: Enums.surfaceRadius(Enums.radius.large)
    readonly property color _toastBackground: _cardColor
    readonly property real _toastBorderWidth: Enums.surfaceBorderWidth(Enums.border.thin)
    readonly property color _toastBorderColor: Enums.stateColor.borderLight
    readonly property color _toastShadowColor: Enums.shadow.level4.color
    readonly property int _toastShadowBlur: Enums.shadow.level4.blur
    readonly property int _toastShadowOffset: Enums.shadow.level4.offset
    
    // Progress properties 进度属性
    property int feature: Enums.notification.feature_normal  // 功能模式
    property real progress: 0  // 0-1 进度值
    property string progressIcon: ""  // Progress ring center icon 进度环中心图标
    property int completeDuration: Enums.duration.progressComplete  // 进度完成后持续显示时间(ms)
    
    // Progress mode helpers 进度模式辅助属性
    readonly property bool _isProgressMode: feature === Enums.notification.feature_progress_bar ||
                                            feature === Enums.notification.feature_progress_ring
    readonly property bool _isRingMode: feature === Enums.notification.feature_progress_ring ||
                                        feature === Enums.notification.feature_indeterminate_ring
    readonly property bool _isBarMode: feature === Enums.notification.feature_progress_bar ||
                                       feature === Enums.notification.feature_indeterminate_bar
    readonly property bool _progressComplete: _isProgressMode && progress >= 1.0

    // Use shared severity helpers 使用共享的语义辅助函数
    readonly property int _severityLevel: Enums.notification.getSeverityLevel(severity)
    readonly property color severityColor: Enums.statusLevel.getColorByLevel(_severityLevel)
    readonly property string severityIconName: Enums.notification.getSeverityIcon(severity)

    // Height auto-adapts based on layout orientation 高度自适应：根据布局方向计算
    // 水平模式也按内容动态:title + message 实际高度堆叠,长文本/多行不被固定高裁切
    readonly property real _horizontalHeight: contentLayer.horizontalHeight
    readonly property real _verticalHeight: contentLayer.verticalHeight
    property bool _desktopClosing: false

    // ==================== Signals 信号 ====================
    signal closed()

    // ==================== Public Methods 公开方法 ====================
    function show(msg, type) {
        if (msg) message = msg
        if (type) severity = type
        if (desktopMode) {
            _desktopClosing = false
            visible = true
            opacity = 1
        } else {
            animator.show()  // Animator handles visibility 动画器处理可见性
        }
        if (duration > 0) hideTimer.restart()
    }

    function hide() {
        if (desktopMode) {
            if (_desktopClosing) return
            _desktopClosing = true
            hideTimer.stop()
            closed()
        } else {
            animator.hide()
        }
    }

    // ==================== Size 尺寸 ====================
    // Content size (inherited from Widget) 内容尺寸：根据内部文字自适应
    contentWidth: contentLayer.calculatedContentWidth
    // Height is always auto-calculated 高度始终自动计算
    implicitHeight: _isVertical ? _verticalHeight : _horizontalHeight
    width: implicitWidth
    height: implicitHeight
    visible: false  // Initially hidden 初始隐藏

    // Desktop mode: set opacity directly 桌面模式直接设置透明度
    Component.onCompleted: {
        if (desktopMode) {
            opacity = 1
        }
    }

    // ==================== Content 内容 ====================
    // Shared animator 共享动画器
    NotificationAnimator {
        id: animator
        target: control
        position: control.position
        parentItem: control.parent
        onHideFinished: { control.visible = false; control.closed() }
    }

    NotificationInternal.ToastContent {
        id: contentLayer
        toast: control
    }

    // Auto close 自动关闭
    NotificationInternal.ToastAutoCloseTimer {
        id: hideTimer

        host: control
    }
    
    // Progress complete timer 进度完成后延迟关闭
    NotificationInternal.ToastProgressCompleteTimer {
        id: completeTimer

        host: control
    }
}
