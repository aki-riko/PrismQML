// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../Notification"
import "_internal" as InfoBarInternal

// InfoBarCore - Fluent style info bar 信息提示条
Widget {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property string title: ""
    property string message: ""
    property alias content: control.message
    property string severity: "info"  // info, success, warning, error, attention, processing
    property bool closable: true
    property int duration: Enums.duration.notification
    property string icon: ""
    property int position: Enums.notification.posBottomLeft  // Compat prop (handled by Manager) 兼容属性
    property bool desktopMode: false  // Desktop mode skips internal animation 桌面模式跳过内部动画
    
    // Layout properties 布局属性
    property int orient: Qt.Horizontal  // Layout orientation 布局方向 (Qt.Horizontal/Qt.Vertical)
    readonly property bool _isVertical: orient === Qt.Vertical

    // Custom widget 自定义组件
    property alias customContent: contentLayer.customContent  // Custom widget slot 自定义组件插槽
    property bool hasCustomContent: contentLayer.hasCustomContent

    // Animation 动画
    property alias animator: animator  // Expose animator for stack management 暴露动画器供堆叠管理使用

    // Custom background 自定义背景色
    property color backgroundColorLight: Enums.transparent  // Custom light theme bg 自定义浅色背景
    property color backgroundColorDark: Enums.transparent   // Custom dark theme bg 自定义深色背景
    readonly property bool _hasCustomBg: backgroundColorLight.a > 0 || backgroundColorDark.a > 0

    // Progress properties 进度属性
    property int feature: Enums.notification.feature_normal  // 功能模式
    property real progress: 0  // 0-1 进度值
    property int completeDuration: Enums.duration.progressComplete  // 进度完成后持续显示时间(ms)

    // Style properties 样式属性
    property real radius: Enums.surfaceRadius(Enums.radius.large)// 圆角半径
    // Border color 边框色 (neo 用控件边框 token=黑; Fluent 用 divider 轻分隔)
    readonly property color borderColor: Enums.hasOutlinedSurfaces ? Enums.stateColor.border : Enums.stateColor.divider
    readonly property real _infoBarRadius: radius
    readonly property color _infoBarBackground: backgroundColor
    readonly property real _infoBarBorderWidth: Enums.surfaceBorderWidth(Enums.border.thin)
    readonly property color _infoBarBorderColor: borderColor
    readonly property color _infoBarShadowColor: Enums.shadow.level4.color
    readonly property int _infoBarShadowBlur: Enums.shadow.level4.blur
    readonly property int _infoBarShadowOffset: Enums.shadow.level4.offset
    // Use shared severity helpers 使用共享的语义辅助函数
    readonly property int _severityLevel: Enums.notification.getSeverityLevel(severity)
    readonly property color severityColor: Enums.statusLevel.getColorByLevel(_severityLevel)
    readonly property string severityIconName: Enums.notification.getSeverityIcon(severity)
    
    // Background color based on feature 根据功能模式决定背景色
    readonly property bool _isProgressMode: feature === Enums.notification.feature_progress_bar ||
                                            feature === Enums.notification.feature_progress_ring
    readonly property bool _isIndeterminateMode: feature === Enums.notification.feature_indeterminate_bar ||
                                                 feature === Enums.notification.feature_indeterminate_ring
    readonly property bool _isRingMode: feature === Enums.notification.feature_progress_ring ||
                                        feature === Enums.notification.feature_indeterminate_ring
    readonly property bool _isBarMode: feature === Enums.notification.feature_progress_bar ||
                                       feature === Enums.notification.feature_indeterminate_bar
    readonly property bool _progressComplete: _isProgressMode && progress >= 1.0
    readonly property bool _autoCloseActive: duration > 0 && control.visible &&
                                              control._showing && !_isProgressMode
    readonly property bool _completeCloseActive: _progressComplete && control.visible
    
    readonly property color backgroundColor: {
        // Custom background color takes priority 自定义背景色优先
        if (_hasCustomBg) {
            return Enums.isDark ? backgroundColorDark : backgroundColorLight
        }
        // Progress bar/ring/indeterminate mode: white card (switch after complete) 进度条/进度环/不确定模式：白色卡片（进度完成后切换为语义色）

        if ((_isProgressMode || _isIndeterminateMode) && !_progressComplete) {
            return Enums.cardColor
        }
        // Normal mode or after complete: use semantic background color 普通模式或完成后：使用语义背景色
        // Neobrutalism: 白底(靠黑边+左侧色条+硬阴影区分), 不用语义淡背景
        if (Enums.hasOutlinedSurfaces) return Enums.cardColor

        return Enums.statusLevel.getBgColor(severity)
    }
    readonly property real _horizontalContentHeight: contentLayer.horizontalContentHeight
    readonly property real _verticalContentHeight: contentLayer.verticalContentHeight
    property bool _showing: true

    // ==================== Signals 信号 ====================
    signal closed()

    // ==================== Public Methods 公开方法 ====================
    function show() {
        _showing = true
        if (desktopMode) {
            visible = true
            opacity = 1
        } else {
            animator.show()  // Animator handles visibility 动画器处理可见性
        }
    }
    function hide() {
        if (!_showing) return
        _showing = false
        if (desktopMode) {
            closed()
        } else {
            animator.hide()
        }
    }
    function close() { hide() }

    // ==================== Size 尺寸 ====================
    // Content size (inherited from Widget) 内容尺寸：根据内部文字自适应
    contentWidth: {
        return contentLayer.calculatedContentWidth
    }
    // Height is always auto-calculated 高度始终自动计算
    implicitHeight: _isVertical ? _verticalContentHeight : _horizontalContentHeight

    // Desktop mode: set opacity directly 桌面模式直接设置透明度
    Component.onCompleted: {
        if (desktopMode) {
            opacity = 1
        }
    }

    // Shared animator 共享动画器
    NotificationAnimator {
        id: animator
        target: control
        position: control.position
        parentItem: control.parent
        onShowFinished: control._showing = true
        onHideFinished: { control.visible = false; control.closed() }
    }

    // Shared close timer 共享关闭计时器
    InfoBarInternal.InfoBarCloseTimer {
        id: closeTimer

        host: control
    }
    // ==================== Content 内容 ====================
    InfoBarInternal.InfoBarContent {
        id: contentLayer
        infoBar: control
    }
}
