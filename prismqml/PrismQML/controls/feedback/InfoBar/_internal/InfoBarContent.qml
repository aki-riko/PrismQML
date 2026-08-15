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

// InfoBarContent - InfoBar visual and lazy progress content 信息条视觉与惰性进度内容
// Keeps InfoBarCore focused on public state, timing and animation orchestration.
// 将 InfoBarCore 入口限制为公开状态、计时与动画编排。
Item {
    id: content

    // ==================== Required Props 必需属性 ====================
    required property var infoBar

    // ==================== Public Props 公开属性 ====================
    property alias customContent: customContentLoader.sourceComponent
    readonly property bool hasCustomContent:
        customContentLoader.sourceComponent !== null && customContentLoader.item !== null
    readonly property real calculatedContentWidth: {
        var baseWidth = 0
        if (!infoBar._isRingMode) {
            baseWidth += Enums.infoBarMetrics.margin + Enums.infoBarMetrics.iconContainerSize
        } else {
            baseWidth += Enums.infoBarMetrics.margin + Enums.infoBarMetrics.iconContainerSize
        }
        baseWidth += Enums.infoBarMetrics.textLeftGap + Enums.infoBarMetrics.textRightMargin
        if (infoBar.closable) {
            baseWidth += Enums.infoBarMetrics.margin + Enums.infoBarMetrics.closeButtonSize
        }

        var textW = 0
        if (!infoBar._isVertical) {
            if (infoBar.title !== "") textW += titleLabel.implicitWidth
            if (infoBar.message !== "") {
                textW += (infoBar.title !== "" ? textRow.spacing : 0) + contentLabel.implicitWidth
            }
        } else {
            if (infoBar.title !== "") {
                textW = Math.max(textW, titleLabelVertical.implicitWidth)
            }
            if (infoBar.message !== "") {
                textW = Math.max(textW, contentLabelVertical.implicitWidth)
            }
        }

        var targetWidth = baseWidth + textW
        return Math.min(Math.max(targetWidth, Enums.controlSize.toastWidth), 800)
    }
    readonly property real horizontalContentHeight:
        Math.max(Enums.spacing.xxxl, textRow.implicitHeight) + Enums.spacing.m * 2
    readonly property real verticalContentHeight: {
        var h = Enums.spacing.m * 2
        h += iconContainer.height + Enums.spacing.m
        if (infoBar.title !== "") h += titleLabelVertical.implicitHeight + Enums.spacing.xs
        if (infoBar.message !== "") h += contentLabelVertical.implicitHeight + Enums.spacing.xs
        if (hasCustomContent) h += customContentLoader.height + Enums.spacing.m
        return Math.max(Enums.infoBarMetrics.height, h)
    }

    anchors.fill: parent

    // ==================== Content 内容 ====================
    // Shadow layer 阴影层
    // Fluent: 模糊阴影; Neobrutalism: 硬阴影(NeoShadow)。
    RectangularShadow {
        anchors.fill: card
        radius: card.radius
        color: infoBar._infoBarShadowColor
        blur: infoBar._infoBarShadowBlur
        offset.x: 0
        offset.y: infoBar._infoBarShadowOffset
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

    // Card 卡片
    Rectangle {
        id: card
        anchors.fill: parent
        radius: infoBar._infoBarRadius
        color: infoBar._infoBarBackground
        border.width: infoBar._infoBarBorderWidth  // neo 粗黑边
        border.color: infoBar._infoBarBorderColor
    }

    // Icon container - 自适应高度 图标容器
    // Hidden when ring mode is active 进度环模式时隐藏
    Item {
        id: iconContainer
        anchors.left: parent.left
        anchors.leftMargin: Enums.infoBarMetrics.margin
        anchors.top: infoBar._isVertical ? parent.top : undefined
        anchors.topMargin: infoBar._isVertical ? Enums.spacing.m : 0
        anchors.verticalCenter: infoBar._isVertical ? undefined : parent.verticalCenter
        width: height  // 保持正方形
        height: Math.min(infoBar.height - Enums.spacing.xs * 2, Enums.infoBarMetrics.iconContainerSize)
        visible: !infoBar._isRingMode

        Icon {
            anchors.centerIn: parent
            iconSize: Enums.infoBarMetrics.iconSize
            icon: infoBar.severityIconName
            color: infoBar.severityColor
        }
    }

    // Horizontal layout 水平布局
    // Text container 文字容器（水平模式）
    Row {
        id: textRow
        anchors.left: infoBar._isRingMode ? progressModeLoader.right : iconContainer.right
        anchors.leftMargin: Enums.infoBarMetrics.textLeftGap
        anchors.right: closeBtn.visible ? closeBtn.left : parent.right
        anchors.rightMargin: Enums.infoBarMetrics.textRightMargin
        anchors.verticalCenter: parent.verticalCenter
        spacing: Enums.infoBarMetrics.textSpacing
        visible: !infoBar._isVertical

        // Title (bold) 标题
        Label {
            id: titleLabel
            text: infoBar.title
            type: Enums.label.type_body_strong
            color: Enums.textColor.primary
            visible: infoBar.title !== ""
        }

        // Content 内容
        Label {
            id: contentLabel
            text: infoBar.message
            type: Enums.label.type_body
            color: Enums.textColor.primary
            visible: infoBar.message !== ""
            width: Math.min(implicitWidth, 800 - parent.x
                            - (closeBtn.visible
                               ? closeBtn.width + Enums.infoBarMetrics.margin * 2 : 0))
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
        sourceComponent: !infoBar._isVertical ? infoBar.customContent : null
        visible: !infoBar._isVertical && item !== null
    }

    // Vertical layout 垂直布局
    Column {
        id: verticalLayout
        anchors.left: iconContainer.right
        anchors.leftMargin: Enums.infoBarMetrics.textLeftGap
        anchors.right: closeBtn.visible ? closeBtn.left : parent.right
        anchors.rightMargin: Enums.infoBarMetrics.textRightMargin
        anchors.top: parent.top
        anchors.topMargin: Enums.spacing.m
        spacing: Enums.spacing.xs
        visible: infoBar._isVertical

        // Title (bold) 标题（垂直模式）
        Label {
            id: titleLabelVertical
            text: infoBar.title
            type: Enums.label.type_body_strong
            color: Enums.textColor.primary
            visible: infoBar.title !== ""
            width: parent.width
            wrapMode: Text.Wrap
        }

        // Content 内容（垂直模式，支持换行）
        Label {
            id: contentLabelVertical
            text: infoBar.message
            type: Enums.label.type_body
            color: Enums.textColor.primary
            visible: infoBar.message !== ""
            width: parent.width
            wrapMode: Text.Wrap
        }

        // Custom content loader (vertical) 自定义内容加载器（垂直模式）
        Loader {
            id: customContentLoader
            width: parent.width
            sourceComponent: infoBar._isVertical ? infoBar.customContent : null
            visible: infoBar._isVertical && item !== null
        }
    }

    // Close button - 自适应高度 关闭按钮-右侧
    CloseButton {
        id: closeBtn
        anchors.right: parent.right
        anchors.rightMargin: Enums.infoBarMetrics.margin
        anchors.top: infoBar._isVertical ? parent.top : undefined
        anchors.topMargin: infoBar._isVertical ? Enums.spacing.m : 0
        anchors.verticalCenter: infoBar._isVertical ? undefined : parent.verticalCenter
        size: Math.min(infoBar.height - Enums.spacing.xs * 2, Enums.infoBarMetrics.closeButtonSize)
        iconSizeValue: Enums.infoBarMetrics.closeIconSize
        visible: infoBar.closable
        onClicked: infoBar.hide()
    }

    // Load only the active progress shape; normal notifications keep both heavy branches absent.
    // 仅加载当前进度形态；普通通知不常驻两个重型分支。
    Loader {
        id: progressModeLoader

        active: infoBar._isBarMode || infoBar._isRingMode
        x: infoBar._isRingMode ? Enums.infoBarMetrics.margin : 0
        y: infoBar._isRingMode ? (infoBar.height - height) / 2 : 0
        width: infoBar._isRingMode ? Enums.infoBarMetrics.iconContainerSize : infoBar.width
        height: infoBar._isRingMode ? Enums.infoBarMetrics.iconContainerSize : infoBar.height
        sourceComponent: infoBar._isBarMode
            ? progressBarComponent
            : (infoBar._isRingMode ? progressRingComponent : null)
    }

    Component {
        id: progressBarComponent

        // Progress bar container: ref Button rounded clip solution 进度条容器：参考Button的圆角裁剪方案
        Item {
            // Mask uses Rectangle's opaque white default and requires a layer 遮罩使用 Rectangle 默认不透明白色，且必须启用 layer
            Rectangle {
                id: progressMask

                objectName: "infoBarProgressMask"
                anchors.fill: parent
                radius: infoBar.radius
                layer.enabled: infoBar._isBarMode
                visible: false
            }

            // Progress bar content with mask 带遮罩的进度条内容
            Item {
                id: progressContent

                objectName: "infoBarProgressContent"
                anchors.fill: parent
                layer.enabled: infoBar._isBarMode
                layer.effect: MultiEffect {
                    maskEnabled: true
                    maskSource: progressMask
                    maskThresholdMin: 0.5
                    maskSpreadAtMin: 0.0
                }

                ProgressBar {
                    objectName: "infoBarProgressBar"
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    height: Enums.spacing.xs
                    value: infoBar.progress * 100
                    from: 0
                    to: 100
                    indeterminate: infoBar.feature === Enums.notification.feature_indeterminate_bar
                }
            }
        }
    }

    Component {
        id: progressRingComponent

        // Progress ring container: same size and margin as icon container 进度环容器：与图标容器相同的尺寸和间距
        Item {
            id: ringContainer

            ProgressRing {
                objectName: "infoBarProgressRing"
                anchors.centerIn: parent
                width: Enums.infoBarMetrics.iconSize
                height: width
                strokeWidth: Enums.border.normal
                value: infoBar.progress * 100
                from: 0
                to: 100
                indeterminate: infoBar.feature === Enums.notification.feature_indeterminate_ring
                               && ringContainer.visible && infoBar.visible
                visible: !infoBar._progressComplete && (
                    infoBar.feature === Enums.notification.feature_progress_ring ||
                    (infoBar.feature === Enums.notification.feature_indeterminate_ring
                     && infoBar.visible)
                )
            }

            // Complete icon 完成图标
            Icon {
                objectName: "infoBarProgressCompleteIcon"
                anchors.centerIn: parent
                iconSize: Enums.infoBarMetrics.iconSize
                icon: infoBar.severityIconName
                color: infoBar.severityColor
                visible: infoBar._progressComplete
                opacity: 0

                NumberAnimation on opacity {
                    running: infoBar._progressComplete
                    from: 0; to: 1
                    duration: Enums.duration.normal
                }
            }
        }
    }
}
