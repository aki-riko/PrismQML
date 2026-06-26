// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../.."
import "../../../effects"
import "../../icons"
import "../../buttons"
import "../../data"
import "../Progress"
import "../../containers"

// Toast - Card-style notification 卡片式通知
// Structure: bottom color bar + top white card 底层颜色条+上层卡片
Widget {
    id: control
    
    property string title: ""
    property string message: ""
    property alias text: control.message
    property int duration: Enums.duration.notification
    property string severity: "info"  // info, success, warning, error, attention, processing
    property bool closable: true
    property int position: Enums.notification.posBottomRight  // Position from NotificationManager 位置(0-5)
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
    readonly property color _cardColor: _hasCustomBg ? (Enums.isDark ? backgroundColorDark : backgroundColorLight) : Enums.toastCardColor
    
    // ==================== Progress Props 进度属性 ====================
    property int feature: Enums.notification.feature_normal  // 功能模式
    property real progress: 0  // 0-1 进度值
    property int completeDuration: Enums.duration.progressComplete  // 进度完成后持续显示时间(ms)
    
    // Progress mode helpers 进度模式辅助属性
    readonly property bool _isProgressMode: feature === Enums.notification.feature_progress_bar ||
                                            feature === Enums.notification.feature_progress_ring
    readonly property bool _isRingMode: feature === Enums.notification.feature_progress_ring ||
                                        feature === Enums.notification.feature_indeterminate_ring
    readonly property bool _isBarMode: feature === Enums.notification.feature_progress_bar ||
                                       feature === Enums.notification.feature_indeterminate_bar
    readonly property bool _progressComplete: _isProgressMode && progress >= 1.0
    
    signal closed()

    // Use shared severity helpers 使用共享的语义辅助函数
    readonly property int _severityLevel: Enums.notification.getSeverityLevel(severity)
    readonly property color severityColor: Enums.statusLevel.getColorByLevel(_severityLevel)
    readonly property string severityIconName: Enums.notification.getSeverityIcon(severity)
    
    // ==================== Size 尺寸 ====================
    // Content size (inherited from Widget) 内容尺寸：根据内部文字自适应
    contentWidth: {
        var baseWidth = Enums.spacing.m * 2; // margins
        if (_isRingMode || _isBarMode) {
            baseWidth += Enums.infoBarMetrics.iconContainerSize + Enums.infoBarMetrics.textLeftGap;
        } else {
            baseWidth += Enums.spacing.xl; // text left margin
        }
        
        baseWidth += Enums.spacing.m; // text right margin
        if (closable) {
            baseWidth += Enums.controlSize.inputHeightCompact + Enums.spacing.l; // closeBtn width + right margin
        }
        
        var textW = 0;
        if (!_isVertical) {
            if (title !== "") textW += titleText.implicitWidth;
            if (message !== "") textW += (title !== "" ? Enums.spacing.xs : 0) + messageText.implicitWidth;
        } else {
            if (title !== "") textW = Math.max(textW, titleTextVertical.implicitWidth);
            if (message !== "") textW = Math.max(textW, messageTextVertical.implicitWidth);
        }
        
        var targetWidth = baseWidth + textW;
        return Math.min(Math.max(targetWidth, Enums.controlSize.toastWidth), 800)
    }
    // Height auto-adapts based on layout orientation 高度自适应：根据布局方向计算
    // 水平模式也按内容动态:title + message 实际高度堆叠,长文本/多行不被固定高裁切
    readonly property real _horizontalHeight: {
        var contentH = 0
        if (title !== "") contentH += titleText.contentHeight + Enums.spacing.xs
        if (message !== "") contentH += messageText.contentHeight
        var h = contentH + Enums.spacing.l * 2  // 上下边距
        return Math.max(Enums.controlSize.toastHeight, h)
    }
    readonly property real _verticalHeight: {
        var h = Enums.spacing.m * 2 + Enums.spacing.l  // Margins + color bar offset
        if (title !== "") h += titleTextVertical.implicitHeight + Enums.spacing.xs
        if (message !== "") h += messageTextVertical.implicitHeight + Enums.spacing.xs
        if (hasCustomContent) h += customContentLoader.height + Enums.spacing.m
        return Math.max(Enums.controlSize.toastHeight, h)
    }
    // Height is always auto-calculated 高度始终自动计算
    implicitHeight: _isVertical ? _verticalHeight : _horizontalHeight
    width: implicitWidth
    height: implicitHeight
    visible: false  // Initially hidden 初始隐藏
    
    // ==================== Show/Hide 显示/隐藏 ====================
    function show(msg, type) {
        if (msg) message = msg
        if (type) severity = type
        if (desktopMode) {
            visible = true
            opacity = 1
        } else {
            animator.show()  // Animator handles visibility 动画器处理可见性
        }
        if (duration > 0) hideTimer.restart()
    }
    
    function hide() {
        if (desktopMode) {
            visible = false
            closed()
        } else {
            animator.hide()
        }
    }
    
    // ==================== Shared Animator 共享动画器 ====================
    property alias animator: animator  // Expose animator for stack management 暴露动画器供堆叠管理使用
    
    NotificationAnimator {
        id: animator
        target: control
        position: control.position
        parentItem: control.parent
        onHideFinished: { control.visible = false; control.closed() }
    }
    
    // Desktop mode: set opacity directly 桌面模式直接设置透明度
    Component.onCompleted: {
        if (desktopMode) {
            opacity = 1
        }
    }
    
    // ==================== Container 容器 ====================
    Item {
        id: container
        anchors.fill: parent
        anchors.margins: Enums.spacing.m
        anchors.topMargin: Enums.spacing.m + 3  // Extra space for color bar

        // Shadow Layer 阴影层
        // Fluent: 模糊阴影; Neobrutalism: 硬阴影(NeoShadow)。
        RectangularShadow {
            anchors.fill: card
            radius: card.radius
            color: Enums.shadow.level4.color
            blur: Enums.shadow.level4.blur
            offset.x: 0
            offset.y: Enums.shadow.level4.offset
            visible: !Enums.isNeobrutalism
        }

        NeoShadow {
            target: card
            visible: Enums.isNeobrutalism
            z: card.z - 1
        }

        // Bottom Layer: Color bar 底层颜色条
        Rectangle {
            id: colorBar
            anchors.left: card.left
            anchors.right: card.right
            anchors.top: card.top
            anchors.topMargin: -3  // Extend 3px up 向上延伸
            height: Enums.spacing.l
            radius: Enums.radius.large
            color: control.severityColor
        }

        // Top Layer: White card 上层白色卡片
        Rectangle {
            id: card
            anchors.fill: parent
            radius: Enums.radius.small
            color: control._cardColor  // 支持自定义背景色
            border.width: Enums.isNeobrutalism ? Enums.neo.borderWidth : Enums.border.thin
            border.color: Enums.stateColor.borderLight
            
            // Icon container: ref InfoBar icon in progress bar mode, hidden in ring mode 图标容器：参考 InfoBar 进度条模式下的图标，环形模式下隐藏

            Item {
                id: toastIconContainer
                anchors.left: parent.left
                anchors.leftMargin: Enums.infoBarMetrics.margin
                anchors.top: _isVertical ? parent.top : undefined
                anchors.topMargin: _isVertical ? Enums.spacing.l : 0
                anchors.verticalCenter: _isVertical ? undefined : parent.verticalCenter
                width: Enums.infoBarMetrics.iconContainerSize
                height: Enums.infoBarMetrics.iconContainerSize
                visible: control._isBarMode
                
                Icon {
                    anchors.centerIn: parent
                    iconSize: Enums.infoBarMetrics.iconSize
                    icon: control.severityIconName
                    color: control.severityColor
                }
            }
            
            // ==================== Horizontal Layout 水平布局 ====================
            // Title 标题（水平模式）
            Label {
                id: titleText
                anchors.left: _isRingMode ? toastRingContainer.right : (_isBarMode ? toastIconContainer.right : parent.left)
                anchors.leftMargin: (_isRingMode || _isBarMode) ? Enums.infoBarMetrics.textLeftGap : Enums.spacing.xl
                anchors.top: parent.top
                anchors.topMargin: Enums.spacing.l
                anchors.right: closeBtn.left
                anchors.rightMargin: Enums.spacing.m
                text: control.title
                type: Enums.label.type_body_strong
                color: Enums.textColor.primary
                visible: text !== "" && !_isVertical
                width: Math.min(implicitWidth, 800 - parent.x - (closeBtn.visible ? closeBtn.width + Enums.spacing.l + Enums.spacing.m : 0))
                elide: Text.ElideRight
            }

            // Content 内容（水平模式）
            Label {
                id: messageText
                anchors.left: _isRingMode ? toastRingContainer.right : (_isBarMode ? toastIconContainer.right : parent.left)
                anchors.leftMargin: (_isRingMode || _isBarMode) ? Enums.infoBarMetrics.textLeftGap : Enums.spacing.xl
                anchors.top: titleText.visible ? titleText.bottom : parent.top
                anchors.topMargin: titleText.visible ? Enums.spacing.xs : Enums.spacing.l
                anchors.right: closeBtn.left
                anchors.rightMargin: Enums.spacing.m
                text: control.message
                type: Enums.label.type_caption
                color: Enums.textColor.secondary
                visible: text !== "" && !_isVertical
                // 用 anchors 左右约束确定宽度→触发自动换行;Text.Wrap 处理 \n 硬换行+长行折行
                wrapMode: Text.Wrap
                verticalAlignment: Text.AlignTop
            }
            
            // ==================== Vertical Layout 垂直布局 ====================
            Column {
                id: verticalLayout
                anchors.left: _isRingMode ? toastRingContainer.right : (_isBarMode ? toastIconContainer.right : parent.left)
                anchors.leftMargin: (_isRingMode || _isBarMode) ? Enums.infoBarMetrics.textLeftGap : Enums.spacing.xl
                anchors.right: closeBtn.left
                anchors.rightMargin: Enums.spacing.m
                anchors.top: parent.top
                anchors.topMargin: Enums.spacing.l
                spacing: Enums.spacing.xs
                visible: _isVertical
                
                // Title 标题（垂直模式）
                Label {
                    id: titleTextVertical
                    text: control.title
                    type: Enums.label.type_body_strong
                    color: Enums.textColor.primary
                    visible: text !== ""
                    width: parent.width
                    wrapMode: Text.Wrap
                }
                
                // Content 内容（垂直模式，支持换行）
                Label {
                    id: messageTextVertical
                    text: control.message
                    type: Enums.label.type_caption
                    color: Enums.textColor.secondary
                    visible: text !== ""
                    width: parent.width
                    wrapMode: Text.Wrap
                }
                
                // Custom content loader 自定义内容加载器
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
                anchors.top: _isVertical ? parent.top : undefined
                anchors.topMargin: _isVertical ? Enums.spacing.l : 0
                anchors.verticalCenter: _isVertical ? undefined : parent.verticalCenter
                size: Enums.controlSize.inputHeightCompact
                iconSizeValue: Enums.iconSize.s
                visible: control.closable
                onClicked: control.hide()
            }
            
            // ==================== Progress Bar 进度条（参考Button圆角裁剪方案） ====================
            Item {
                id: toastProgressClipRect
                anchors.fill: parent
                visible: control._isBarMode
                
                // Mask shape (layer must be enabled) 遮罩形状（必须启用layer）
                Rectangle {
                    id: toastProgressMask
                    anchors.fill: parent
                    radius: card.radius
                    color: "white"
                    layer.enabled: true
                    visible: false
                }
                
                // Progress bar content with mask 带遮罩的进度条内容
                Item {
                    id: toastProgressContent
                    anchors.fill: parent
                    layer.enabled: true
                    layer.effect: MultiEffect {
                        maskEnabled: true
                        maskSource: toastProgressMask
                        maskThresholdMin: 0.5
                        maskSpreadAtMin: 0.0
                    }
                    
                    // Indeterminate progress bar 不确定进度条
                    ProgressBar {
                        id: toastIndeterminateBar
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        height: Enums.spacing.xs
                        indeterminate: true
                        visible: feature === Enums.notification.feature_indeterminate_bar
                    }
                    
                    // Determinate progress bar 确定进度条
                    ProgressBar {
                        id: toastDeterminateBar
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
            // Progress ring container: ref InfoBar margins and size 进度环容器：参考 InfoBar 的边距和尺寸
            Item {
                id: toastRingContainer
                anchors.left: parent.left
                anchors.leftMargin: Enums.infoBarMetrics.margin
                anchors.top: _isVertical ? parent.top : undefined
                anchors.topMargin: _isVertical ? Enums.spacing.l : 0
                anchors.verticalCenter: _isVertical ? undefined : parent.verticalCenter
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
                    indeterminate: feature === Enums.notification.feature_indeterminate_ring && toastRingContainer.visible && control.visible
                    visible: feature === Enums.notification.feature_indeterminate_ring && control.visible
                }
                
                // Complete icon 完成图标
                Icon {
                    anchors.centerIn: parent
                    iconSize: Enums.infoBarMetrics.iconSize
                    icon: Enums.icon.checkmark
                    color: Enums.accentColor
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
    }
    
    // Auto close 自动关闭
    Timer {
        id: hideTimer
        interval: control.duration
        running: control.visible && control.duration > 0 && !_isProgressMode
        onTriggered: control.hide()
    }
    
    // Progress complete timer 进度完成后延迟关闭
    Timer {
        id: completeTimer
        running: _progressComplete && control.visible
        interval: control.completeDuration
        onTriggered: control.hide()
    }
}
