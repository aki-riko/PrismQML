// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import QtQuick.Effects
import "../../../effects"
import "../../icons"
import "../../buttons"
import "../../data"
import "../Notification"
import "../Progress"
import "../../containers"

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
    
    // ==================== Layout Props 布局属性 ====================
    property int orient: Qt.Horizontal  // Layout orientation 布局方向 (Qt.Horizontal/Qt.Vertical)
    readonly property bool _isVertical: orient === Qt.Vertical
    
    // ==================== Custom Widget 自定义组件 ====================
    property alias customContent: customContentLoader.sourceComponent  // Custom widget slot 自定义组件插槽
    property bool hasCustomContent: customContentLoader.sourceComponent !== null && customContentLoader.item !== null
    
    // ==================== Custom Background 自定义背景色 ====================
    property color backgroundColorLight: "transparent"  // Custom light theme bg 自定义浅色背景
    property color backgroundColorDark: "transparent"   // Custom dark theme bg 自定义深色背景
    readonly property bool _hasCustomBg: backgroundColorLight.a > 0 || backgroundColorDark.a > 0
    
    // ==================== Progress Props 进度属性 ====================
    property int feature: Enums.notification.feature_normal  // 功能模式
    property real progress: 0  // 0-1 进度值
    property int completeDuration: Enums.duration.progressComplete  // 进度完成后持续显示时间(ms)
    
    // ==================== Style Props 样式属性 ====================
    property real radius: Enums.radius.large  // 圆角半径
    
    // ==================== Signals 信号 ====================
    signal closed()
    
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
    
    readonly property color backgroundColor: {
        // Custom background color takes priority 自定义背景色优先
        if (_hasCustomBg) {
            return Enums.isDark ? backgroundColorDark : backgroundColorLight
        }
        // Progress bar/ring/indeterminate mode: white card (switch after complete) 进度条/进度环/不确定模式：白色卡片（进度完成后切换为语义色）

        if ((_isProgressMode || _isIndeterminateMode) && !_progressComplete) {
            return Enums.isDark ? Enums.cardColor : "white"
        }
        // Normal mode or after complete: use semantic background color 普通模式或完成后：使用语义背景色
        // Neobrutalism: 白底(靠黑边+左侧色条+硬阴影区分), 不用语义淡背景
        if (Enums.isNeobrutalism) return Enums.neo.surface

        if (Enums.isDark) {
            var c = Enums.statusLevel.getColorByLevel(_severityLevel)
            return Qt.rgba(c.r * 0.25, c.g * 0.25, c.b * 0.25, 1)
        }
        return Enums.statusLevel.getBgColor(severity)
    }
    
    // Border color 边框色 (neo 用控件边框 token=黑; Fluent 用 divider 轻分隔)
    readonly property color borderColor: Enums.isNeobrutalism ? Enums.stateColor.border : Enums.stateColor.divider
    
    // ==================== Size 尺寸 ====================
    // Content size (inherited from Widget) 内容尺寸：根据内部文字自适应
    contentWidth: {
        var baseWidth = 0;
        if (!_isRingMode) {
            baseWidth += Enums.infoBarMetrics.margin + Enums.infoBarMetrics.iconContainerSize;
        } else {
            baseWidth += Enums.infoBarMetrics.margin + Enums.infoBarMetrics.iconContainerSize;
        }
        baseWidth += Enums.infoBarMetrics.textLeftGap + Enums.infoBarMetrics.textRightMargin;
        if (closable) {
            baseWidth += Enums.infoBarMetrics.margin + Enums.infoBarMetrics.closeButtonSize;
        }
        
        var textW = 0;
        if (!_isVertical) {
            if (title !== "") textW += titleLabel.implicitWidth;
            if (message !== "") textW += (title !== "" ? textRow.spacing : 0) + contentLabel.implicitWidth;
        } else {
            if (title !== "") textW = Math.max(textW, titleLabelVertical.implicitWidth);
            if (message !== "") textW = Math.max(textW, contentLabelVertical.implicitWidth);
        }
        
        var targetWidth = baseWidth + textW;
        return Math.min(Math.max(targetWidth, Enums.controlSize.toastWidth), 800) // 最大限制到800，避免过宽破坏UI
    }
    // Height auto-adapts based on layout orientation 高度自适应：根据布局方向计算
    readonly property real _horizontalContentHeight: Math.max(Enums.spacing.xxxl, textRow.implicitHeight) + Enums.spacing.m * 2
    readonly property real _verticalContentHeight: {
        var h = Enums.spacing.m * 2  // Top/bottom padding 上下内边距
        h += iconContainer.height + Enums.spacing.m  // Icon + gap 图标+间距
        if (title !== "") h += titleLabelVertical.implicitHeight + Enums.spacing.xs
        if (message !== "") h += contentLabelVertical.implicitHeight + Enums.spacing.xs
        if (hasCustomContent) h += customContentLoader.height + Enums.spacing.m
        return Math.max(Enums.infoBarMetrics.height, h)
    }
    // Height is always auto-calculated 高度始终自动计算
    implicitHeight: _isVertical ? _verticalContentHeight : _horizontalContentHeight

    // ==================== Animation 动画 ====================
    property bool _showing: true

    // ==================== Public Methods 公开方法 ====================
    function show() {
        if (desktopMode) {
            visible = true
            opacity = 1
        } else {
            animator.show()  // Animator handles visibility 动画器处理可见性
        }
    }
    function hide() {
        _showing = false
        if (desktopMode) {
            visible = false
            closed()
        } else {
            animator.hide()
        }
    }
    function close() { hide() }

    // ==================== Shadow Layer 阴影层 ====================
    // Fluent: 模糊阴影; Neobrutalism: 硬阴影(NeoShadow)。
    RectangularShadow {
        anchors.fill: card
        radius: card.radius
        color: Enums.shadow.level4.color
        blur: Enums.shadow.level4.blur
        offset: Qt.vector2d(0, Enums.shadow.level4.offset)
        visible: !Enums.isNeobrutalism
    }

    NeoShadow {
        target: card
        visible: Enums.isNeobrutalism
        z: card.z - 1
    }

    // ==================== Card 卡片 ====================
    Rectangle {
        id: card
        anchors.fill: parent
        radius: Enums.radius.large  // 6px
        color: backgroundColor
        border.width: Enums.isNeobrutalism ? Enums.neo.borderWidth : Enums.border.thin  // neo 粗黑边
        border.color: borderColor
    }
    
    // ==================== Animation 动画 ====================
    property alias animator: animator  // Expose animator for stack management 暴露动画器供堆叠管理使用

    // Shared animator 共享动画器
    NotificationAnimator {
        id: animator
        target: control
        position: control.position
        parentItem: control.parent
        onShowFinished: control._showing = true
        onHideFinished: { control.visible = false; control.closed() }
    }

    // Desktop mode: set opacity directly 桌面模式直接设置透明度
    Component.onCompleted: {
        if (desktopMode) {
            opacity = 1
        }
    }

    // ==================== Content Layout 内容布局 ====================
    
    // Icon container - 自适应高度 图标容器
    // Hidden when ring mode is active 进度环模式时隐藏
    Item {
        id: iconContainer
        anchors.left: parent.left
        anchors.leftMargin: Enums.infoBarMetrics.margin
        anchors.top: _isVertical ? parent.top : undefined
        anchors.topMargin: _isVertical ? Enums.spacing.m : 0
        anchors.verticalCenter: _isVertical ? undefined : parent.verticalCenter
        width: height  // 保持正方形
        height: Math.min(control.height - Enums.spacing.xs * 2, Enums.infoBarMetrics.iconContainerSize)
        visible: !_isRingMode
        
        Icon {
            anchors.centerIn: parent
            iconSize: Enums.infoBarMetrics.iconSize
            icon: control.severityIconName
            color: control.severityColor
        }
    }
    
    // ==================== Horizontal Layout 水平布局 ====================
    // Text container 文字容器（水平模式）
    Row {
        id: textRow
        anchors.left: _isRingMode ? ringContainer.right : iconContainer.right
        anchors.leftMargin: Enums.infoBarMetrics.textLeftGap  // 与图标模式相同的间距
        anchors.right: closeBtn.visible ? closeBtn.left : parent.right
        anchors.rightMargin: Enums.infoBarMetrics.textRightMargin
        anchors.verticalCenter: parent.verticalCenter
        spacing: Enums.infoBarMetrics.textSpacing
        visible: !_isVertical
        
        // Title (bold) 标题
        Label {
            id: titleLabel
            text: control.title
            type: Enums.label.type_body_strong
            color: Enums.textColor.primary
            visible: control.title !== ""
        }
        
        // Content 内容
        Label {
            id: contentLabel
            text: control.message
            type: Enums.label.type_body
            color: Enums.textColor.primary
            visible: control.message !== ""
            width: Math.min(implicitWidth, 800 - parent.x - (closeBtn.visible ? closeBtn.width + Enums.infoBarMetrics.margin * 2 : 0))
            // 长文本/多行折行显示,不再单行省略号截断
            wrapMode: Text.Wrap
        }
    }
    
    // Custom content loader (horizontal) 自定义内容加载器（水平模式）
    Loader {
        id: customContentLoaderHorizontal
        anchors.left: textRow.right
        anchors.leftMargin: Enums.spacing.m
        anchors.right: closeBtn.visible ? closeBtn.left : parent.right
        anchors.rightMargin: Enums.spacing.m
        anchors.verticalCenter: parent.verticalCenter
        sourceComponent: !_isVertical ? control.customContent : null
        visible: !_isVertical && item !== null
    }
    
    // ==================== Vertical Layout 垂直布局 ====================
    Column {
        id: verticalLayout
        anchors.left: iconContainer.right
        anchors.leftMargin: Enums.infoBarMetrics.textLeftGap
        anchors.right: closeBtn.visible ? closeBtn.left : parent.right
        anchors.rightMargin: Enums.infoBarMetrics.textRightMargin
        anchors.top: parent.top
        anchors.topMargin: Enums.spacing.m
        spacing: Enums.spacing.xs
        visible: _isVertical
        
        // Title (bold) 标题（垂直模式）
        Label {
            id: titleLabelVertical
            text: control.title
            type: Enums.label.type_body_strong
            color: Enums.textColor.primary
            visible: control.title !== ""
            width: parent.width
            wrapMode: Text.Wrap
        }
        
        // Content 内容（垂直模式，支持换行）
        Label {
            id: contentLabelVertical
            text: control.message
            type: Enums.label.type_body
            color: Enums.textColor.primary
            visible: control.message !== ""
            width: parent.width
            wrapMode: Text.Wrap
        }
        
        // Custom content loader (vertical) 自定义内容加载器（垂直模式）
        Loader {
            id: customContentLoader
            width: parent.width
            sourceComponent: _isVertical ? control.customContent : null
            visible: _isVertical && item !== null
        }
    }
    
    // Close button - 自适应高度 关闭按钮-右侧
    CloseButton {
        id: closeBtn
        anchors.right: parent.right
        anchors.rightMargin: Enums.infoBarMetrics.margin
        anchors.top: _isVertical ? parent.top : undefined
        anchors.topMargin: _isVertical ? Enums.spacing.m : 0
        anchors.verticalCenter: _isVertical ? undefined : parent.verticalCenter
        size: Math.min(control.height - Enums.spacing.xs * 2, Enums.infoBarMetrics.closeButtonSize)
        iconSizeValue: Enums.infoBarMetrics.closeIconSize
        visible: control.closable
        onClicked: control.hide()
    }
    
    // ==================== Auto Close 自动关闭 ====================
    Timer {
        running: duration > 0 && control.visible && control._showing && !_isProgressMode
        interval: duration
        onTriggered: control.hide()
    }
    
    // Progress complete timer 进度完成后延迟关闭
    Timer {
        id: completeTimer
        running: _progressComplete && control.visible
        interval: control.completeDuration
        onTriggered: control.hide()
    }
    
    // ==================== Progress Bar 进度条（使用现有ProgressBar组件） ====================
    // Progress bar container: ref Button rounded clip solution 进度条容器：参考Button的圆角裁剪方案

    Item {
        id: progressClipRect
        anchors.fill: parent
        visible: _isBarMode
        
        // Mask shape (layer must be enabled) 遮罩形状（必须启用layer）
        Rectangle {
            id: progressMask
            anchors.fill: parent
            radius: control.radius
            color: "white"
            layer.enabled: true
            visible: false
        }
        
        // Progress bar content with mask 带遮罩的进度条内容
        Item {
            id: progressContent
            anchors.fill: parent
            layer.enabled: true
            layer.effect: MultiEffect {
                maskEnabled: true
                maskSource: progressMask
                maskThresholdMin: 0.5
                maskSpreadAtMin: 0.0
            }
            
            // Indeterminate progress bar: reuse ProgressBar indeterminate mode 不确定进度条：复用 ProgressBar 的不确定模式

            ProgressBar {
                id: indeterminateBar
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: Enums.spacing.xs
                indeterminate: true
                visible: feature === Enums.notification.feature_indeterminate_bar
            }
            
            // Determinate progress bar: reuse ProgressBar determinate mode 确定进度条：复用 ProgressBar 的确定模式

            ProgressBar {
                id: determinateBar
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: Enums.spacing.xs
                value: control.progress * 100
                from: 0
                to: 100
                visible: feature === Enums.notification.feature_progress_bar
            }
        }
    }
    
    // ==================== Progress Ring 进度环（使用现有组件） ====================
    // Progress ring container: same size and margin as icon container 进度环容器：与图标容器相同的尺寸和间距

    Item {
        id: ringContainer
        anchors.left: parent.left
        anchors.leftMargin: Enums.infoBarMetrics.margin
        anchors.verticalCenter: parent.verticalCenter
        width: Enums.infoBarMetrics.iconContainerSize
        height: Enums.infoBarMetrics.iconContainerSize
        visible: _isRingMode
        
        // Determinate progress ring: reuse ProgressRing 确定进度环：复用ProgressRing
        ProgressRing {
            anchors.centerIn: parent
            width: Enums.infoBarMetrics.iconSize
            height: width
            strokeWidth: Enums.border.normal
            value: control.progress * 100
            from: 0
            to: 100
            visible: feature === Enums.notification.feature_progress_ring && !control._progressComplete
        }
        
        // Indeterminate progress ring: ProgressRing with indeterminate 不确定进度环：ProgressRing 不确定模式

        ProgressRing {
            anchors.centerIn: parent
            width: Enums.infoBarMetrics.iconSize
            height: width
            strokeWidth: Enums.border.normal
            indeterminate: feature === Enums.notification.feature_indeterminate_ring && ringContainer.visible && control.visible
            visible: feature === Enums.notification.feature_indeterminate_ring && control.visible
        }
        
        // Complete icon 完成图标
        Icon {
            anchors.centerIn: parent
            iconSize: Enums.infoBarMetrics.iconSize
            icon: control.severityIconName
            color: control.severityColor
            visible: control._progressComplete
            opacity: 0
            
            NumberAnimation on opacity {
                running: control._progressComplete
                from: 0; to: 1
                duration: Enums.duration.normal
            }
        }
    }
}
