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
    property alias customContent: customContentLoader.sourceComponent  // Custom widget slot 自定义组件插槽
    property bool hasCustomContent: customContentLoader.sourceComponent !== null && customContentLoader.item !== null
    
    // Custom background 自定义背景色
    property color backgroundColorLight: Enums.transparent  // Custom light theme bg 自定义浅色背景
    property color backgroundColorDark: Enums.transparent   // Custom dark theme bg 自定义深色背景
    readonly property bool _hasCustomBg: backgroundColorLight.a > 0 || backgroundColorDark.a > 0
    readonly property color _cardColor: _hasCustomBg ? (Enums.isDark ? backgroundColorDark : backgroundColorLight) : Enums.toastCardColor
    readonly property int _toastRadius: Enums.radius.small
    readonly property int _toastColorBarRadius: Enums.radius.large
    readonly property color _toastBackground: _cardColor
    readonly property int _toastBorderWidth: Enums.isNeobrutalism ? Enums.neo.borderWidth : Enums.border.thin
    readonly property color _toastBorderColor: Enums.stateColor.borderLight
    readonly property color _toastShadowColor: Enums.shadow.level4.color
    readonly property int _toastShadowBlur: Enums.shadow.level4.blur
    readonly property int _toastShadowOffset: Enums.shadow.level4.offset
    
    // Progress properties 进度属性
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

    // Use shared severity helpers 使用共享的语义辅助函数
    readonly property int _severityLevel: Enums.notification.getSeverityLevel(severity)
    readonly property color severityColor: Enums.statusLevel.getColorByLevel(_severityLevel)
    readonly property string severityIconName: Enums.notification.getSeverityIcon(severity)

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
        // Use childrenRect because Column implicitHeight can lag behind wrapped children 使用 childrenRect 避免 Column implicitHeight 滞后于换行子项
        var h = verticalLayout.childrenRect.height
            + Enums.spacing.m * 2
            + Enums.spacing.cardElevate
            + Enums.spacing.l * 2
        return Math.max(Enums.controlSize.toastHeight, h)
    }
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
            // Keep text-only vertical toasts compact so long text grows downward 纯文本纵向 Toast 保持标准宽度，让长文本向下撑高
            textW = hasCustomContent ? customContentLoader.implicitWidth : 0;
        }

        var targetWidth = baseWidth + textW;
        return Math.min(
            Math.max(targetWidth, Enums.controlSize.toastWidth),
            Enums.controlSize.toastMaxWidth
        )
    }
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
    property alias animator: animator  // Expose animator for stack management 暴露动画器供堆叠管理使用
    
    NotificationAnimator {
        id: animator
        target: control
        position: control.position
        parentItem: control.parent
        onHideFinished: { control.visible = false; control.closed() }
    }

    // Container 容器
    Item {
        id: container
        anchors.fill: parent
        anchors.margins: Enums.spacing.m
        anchors.topMargin: Enums.spacing.m + Enums.spacing.cardElevate  // Extra space for color bar 为颜色条预留额外空间

        // Shadow Layer 阴影层
        // Fluent: 模糊阴影; Neobrutalism: 硬阴影(NeoShadow)。
        RectangularShadow {
            anchors.fill: card
            radius: card.radius
            color: control._toastShadowColor
            blur: control._toastShadowBlur
            offset.x: 0
            offset.y: control._toastShadowOffset
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
            anchors.topMargin: -Enums.spacing.cardElevate  // Shared elevation offset 共享抬升间距
            height: Enums.spacing.l
            radius: control._toastColorBarRadius
            color: control.severityColor
        }

        // Top Layer: White card 上层白色卡片
        Rectangle {
            id: card
            anchors.fill: parent
            radius: control._toastRadius
            color: control._toastBackground  // 支持自定义背景色
            border.width: control._toastBorderWidth
            border.color: control._toastBorderColor
            
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
            
            // Horizontal layout 水平布局
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
                width: Math.min(implicitWidth, Enums.controlSize.toastMaxWidth - parent.x - (closeBtn.visible ? closeBtn.width + Enums.spacing.l + Enums.spacing.m : 0))
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
            
            // Vertical layout 垂直布局
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
            
            // Progress bar 进度条（参考 Button 圆角裁剪方案）
            Item {
                id: toastProgressClipRect
                anchors.fill: parent
                visible: control._isBarMode

                // Mask uses Rectangle's opaque white default and requires a layer 遮罩使用 Rectangle 默认不透明白色，且必须启用 layer
                Rectangle {
                    id: toastProgressMask

                    objectName: "toastProgressMask"
                    anchors.fill: parent
                    radius: card.radius
                    layer.enabled: control._isBarMode
                    visible: false
                }

                // Progress bar content with mask 带遮罩的进度条内容
                Item {
                    id: toastProgressContent

                    objectName: "toastProgressContent"
                    anchors.fill: parent
                    layer.enabled: control._isBarMode
                    layer.effect: MultiEffect {
                        maskEnabled: true
                        maskSource: toastProgressMask
                        maskThresholdMin: 0.5
                        maskSpreadAtMin: 0.0
                    }

                    ProgressBar {
                        objectName: "toastProgressBar"
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        height: Enums.spacing.xs
                        value: control.progress * 100
                        from: 0
                        to: 100
                        indeterminate: feature === Enums.notification.feature_indeterminate_bar
                    }
                }
            }
            
            // Progress ring 进度环（使用现有组件）
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

                ProgressRing {
                    objectName: "toastProgressRing"
                    anchors.centerIn: parent
                    width: Enums.infoBarMetrics.iconSize
                    height: width
                    strokeWidth: Enums.border.normal
                    value: control.progress * 100
                    from: 0
                    to: 100
                    indeterminate: feature === Enums.notification.feature_indeterminate_ring && toastRingContainer.visible && control.visible
                    visible: !control._progressComplete && (
                        feature === Enums.notification.feature_progress_ring ||
                        (feature === Enums.notification.feature_indeterminate_ring && control.visible)
                    )
                }

                // Complete icon 完成图标
                Icon {
                    objectName: "toastProgressCompleteIcon"
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
