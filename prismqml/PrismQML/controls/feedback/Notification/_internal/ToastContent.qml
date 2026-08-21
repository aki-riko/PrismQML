// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../../../"
import "../../../../effects"
import "../../../icons"
import "../../../buttons"
import "../../Progress"

// ToastContent - Toast visual and lazy progress content Toast 视觉与惰性进度内容
// Keeps Toast focused on public state, timing and animation orchestration.
// 将 Toast 入口限制为公开状态、计时与动画编排。
Item {
    id: content

    // ==================== Required Props 必需属性 ====================
    required property var toast

    // ==================== Public Props 公开属性 ====================
    property alias customContent: customContentLoader.sourceComponent
    readonly property bool hasCustomContent:
        customContentLoader.sourceComponent !== null && customContentLoader.item !== null
    readonly property real calculatedContentWidth: {
        var baseWidth = Enums.spacing.m * 2
        if (toast._isRingMode || toast._isBarMode) {
            baseWidth += Enums.infoBarMetrics.iconContainerSize + Enums.infoBarMetrics.textLeftGap
        } else {
            baseWidth += Enums.spacing.xl
        }

        baseWidth += Enums.spacing.m
        if (toast.closable) {
            baseWidth += Enums.controlSize.inputHeightCompact + Enums.spacing.l
        }

        var textW = 0
        if (!toast._isVertical) {
            if (toast.title !== "") textW += titleText.implicitWidth
            if (toast.message !== "") {
                textW += (toast.title !== "" ? Enums.spacing.xs : 0) + messageText.implicitWidth
            }
        } else {
            // Keep text-only vertical toasts compact so long text grows downward.
            textW = hasCustomContent ? customContentLoader.implicitWidth : 0
        }

        var targetWidth = baseWidth + textW
        return Math.min(
            Math.max(targetWidth, Enums.controlSize.toastWidth),
            Enums.controlSize.toastMaxWidth
        )
    }
    readonly property real horizontalHeight: {
        var contentH = 0
        if (toast.title !== "") contentH += titleText.contentHeight + Enums.spacing.xs
        if (toast.message !== "") contentH += messageText.contentHeight
        var h = contentH + Enums.spacing.l * 2
        return Math.max(Enums.controlSize.toastHeight, h)
    }
    readonly property real verticalHeight: {
        // Use childrenRect because Column implicitHeight can lag wrapped children.
        var h = verticalLayout.childrenRect.height
            + Enums.spacing.m * 2
            + Enums.spacing.cardElevate
            + Enums.spacing.l * 2
        return Math.max(Enums.controlSize.toastHeight, h)
    }

    anchors.fill: parent
    anchors.margins: Enums.spacing.m
    anchors.topMargin: Enums.spacing.m + Enums.spacing.cardElevate

    // ==================== Content 内容 ====================
    // Shadow Layer 阴影层
    // Fluent: 模糊阴影; Neobrutalism: 硬阴影(NeoShadow)。
    RectangularShadow {
        anchors.fill: card
        radius: card.radius
        color: toast._toastShadowColor
        blur: toast._toastShadowBlur
        offset.x: 0
        offset.y: toast._toastShadowOffset
        visible: Enums.usesSoftElevation && !Enums.isNeumorphism
    }

    NeumorphicShadow {
        target: card
        visible: Enums.isNeumorphism
        z: card.z - 1
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
        anchors.topMargin: -Enums.spacing.cardElevate
        height: Enums.spacing.l
        radius: toast._toastColorBarRadius
        color: toast.severityColor
    }

    // Top Layer: White card 上层白色卡片
    Rectangle {
        id: card
        anchors.fill: parent
        radius: toast._toastRadius
        color: toast._toastBackground
        border.width: toast._toastBorderWidth
        border.color: toast._toastBorderColor

        // Icon container: hidden in ring mode 图标容器：环形模式下隐藏
        Item {
            id: toastIconContainer
            anchors.left: parent.left
            anchors.leftMargin: Enums.infoBarMetrics.margin
            anchors.top: toast._isVertical ? parent.top : undefined
            anchors.topMargin: toast._isVertical ? Enums.spacing.l : 0
            anchors.verticalCenter: toast._isVertical ? undefined : parent.verticalCenter
            width: Enums.infoBarMetrics.iconContainerSize
            height: Enums.infoBarMetrics.iconContainerSize
            visible: toast._isBarMode

            Icon {
                anchors.centerIn: parent
                iconSize: Enums.infoBarMetrics.iconSize
                icon: toast.severityIconName
                color: toast.severityColor
            }
        }

        // Horizontal layout 水平布局
        Label {
            id: titleText
            anchors.left: toast._isRingMode
                ? toastProgressModeLoader.right
                : (toast._isBarMode ? toastIconContainer.right : parent.left)
            anchors.leftMargin: (toast._isRingMode || toast._isBarMode)
                ? Enums.infoBarMetrics.textLeftGap : Enums.spacing.xl
            anchors.top: parent.top
            anchors.topMargin: Enums.spacing.l
            anchors.right: closeBtn.left
            anchors.rightMargin: Enums.spacing.m
            text: toast.title
            type: Enums.label.type_body_strong
            color: Enums.textColor.primary
            visible: text !== "" && !toast._isVertical
            width: Math.min(implicitWidth, Enums.controlSize.toastMaxWidth - parent.x
                            - (closeBtn.visible
                               ? closeBtn.width + Enums.spacing.l + Enums.spacing.m : 0))
            elide: Text.ElideRight
        }

        // Content 内容（水平模式）
        Label {
            id: messageText
            anchors.left: toast._isRingMode
                ? toastProgressModeLoader.right
                : (toast._isBarMode ? toastIconContainer.right : parent.left)
            anchors.leftMargin: (toast._isRingMode || toast._isBarMode)
                ? Enums.infoBarMetrics.textLeftGap : Enums.spacing.xl
            anchors.top: titleText.visible ? titleText.bottom : parent.top
            anchors.topMargin: titleText.visible ? Enums.spacing.xs : Enums.spacing.l
            anchors.right: closeBtn.left
            anchors.rightMargin: Enums.spacing.m
            text: toast.message
            type: Enums.label.type_caption
            color: Enums.textColor.secondary
            visible: text !== "" && !toast._isVertical
            // 用 anchors 左右约束确定宽度→触发自动换行;Text.Wrap 处理硬换行+长行折行
            wrapMode: Text.Wrap
            verticalAlignment: Text.AlignTop
        }

        // Vertical layout 垂直布局
        Column {
            id: verticalLayout
            anchors.left: toast._isRingMode
                ? toastProgressModeLoader.right
                : (toast._isBarMode ? toastIconContainer.right : parent.left)
            anchors.leftMargin: (toast._isRingMode || toast._isBarMode)
                ? Enums.infoBarMetrics.textLeftGap : Enums.spacing.xl
            anchors.right: closeBtn.left
            anchors.rightMargin: Enums.spacing.m
            anchors.top: parent.top
            anchors.topMargin: Enums.spacing.l
            spacing: Enums.spacing.xs
            visible: toast._isVertical

            // Title 标题（垂直模式）
            Label {
                id: titleTextVertical
                text: toast.title
                type: Enums.label.type_body_strong
                color: Enums.textColor.primary
                visible: text !== ""
                width: parent.width
                wrapMode: Text.Wrap
            }

            // Content 内容（垂直模式，支持换行）
            Label {
                id: messageTextVertical
                text: toast.message
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
            anchors.top: toast._isVertical ? parent.top : undefined
            anchors.topMargin: toast._isVertical ? Enums.spacing.l : 0
            anchors.verticalCenter: toast._isVertical ? undefined : parent.verticalCenter
            size: Enums.controlSize.inputHeightCompact
            iconSizeValue: Enums.iconSize.s
            visible: toast.closable
            onClicked: toast.hide()
        }

        // Load only the active progress shape; normal toasts keep both heavy branches absent.
        // 仅加载当前进度形态；普通 Toast 不常驻两个重型分支。
        Loader {
            id: toastProgressModeLoader

            active: toast._isBarMode || toast._isRingMode
            x: toast._isRingMode ? Enums.infoBarMetrics.margin : 0
            y: toast._isRingMode
                ? (toast._isVertical ? Enums.spacing.l : (card.height - height) / 2)
                : 0
            width: toast._isRingMode ? Enums.infoBarMetrics.iconContainerSize : card.width
            height: toast._isRingMode ? Enums.infoBarMetrics.iconContainerSize : card.height
            sourceComponent: toast._isBarMode
                ? toastProgressBarComponent
                : (toast._isRingMode ? toastProgressRingComponent : null)
        }

        Component {
            id: toastProgressBarComponent

            // Progress bar 进度条（参考 Button 圆角裁剪方案）
            Item {
                Rectangle {
                    id: toastProgressMask

                    objectName: "toastProgressMask"
                    anchors.fill: parent
                    radius: card.radius
                    layer.enabled: toast._isBarMode
                    visible: false
                }

                Item {
                    id: toastProgressContent

                    objectName: "toastProgressContent"
                    anchors.fill: parent
                    layer.enabled: toast._isBarMode
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
                        value: toast.progress * 100
                        from: 0
                        to: 100
                        indeterminate: toast.feature === Enums.notification.feature_indeterminate_bar
                    }
                }
            }
        }

        Component {
            id: toastProgressRingComponent

            // Progress ring container: ref InfoBar margins and size 进度环容器：参考 InfoBar 的边距和尺寸
            Item {
                id: toastRingContainer

                ProgressRing {
                    objectName: "toastProgressRing"
                    anchors.centerIn: parent
                    width: Enums.infoBarMetrics.iconSize
                    height: width
                    strokeWidth: Enums.border.normal
                    value: toast.progress * 100
                    from: 0
                    to: 100
                    indeterminate: toast.feature === Enums.notification.feature_indeterminate_ring
                                   && toastRingContainer.visible && toast.visible
                    visible: !toast._progressComplete && (
                        toast.feature === Enums.notification.feature_progress_ring ||
                        (toast.feature === Enums.notification.feature_indeterminate_ring
                         && toast.visible)
                    )
                }

                Icon {
                    objectName: "toastProgressStateIcon"
                    anchors.centerIn: parent
                    iconSize: Enums.iconSize.micro
                    icon: toast.progressIcon
                    color: Enums.accentColor
                    visible: !toast._progressComplete && icon !== ""
                }

                // Complete icon 完成图标
                Icon {
                    objectName: "toastProgressCompleteIcon"
                    anchors.centerIn: parent
                    iconSize: Enums.infoBarMetrics.iconSize
                    icon: Enums.icon.checkmark
                    color: Enums.accentColor
                    visible: toast._progressComplete
                    opacity: 0

                    NumberAnimation on opacity {
                        running: toast._progressComplete
                        from: 0; to: 1
                        duration: Enums.duration.normal
                    }
                }
            }
        }
    }
}
