// ButtonContentLayer - Button custom and default content layer 按钮自定义与默认内容层
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import ".."

// ButtonContentLayer - Owns content slots and default ButtonContent 承载内容插槽与默认按钮内容
Item {
    id: contentLayer

    // ==================== Required Props 必需属性 ====================
    required property var buttonControl
    required property var pressTransform

    // ==================== Public Props 公开属性 ====================
    default property alias contentData: customContentContainer.data
    property alias customContentContainer: customContentContainer
    property alias contentLoader: contentLoader

    z: Enums.zIndex.content
    anchors.fill: parent

    // ==================== Content 内容 ====================
    // Custom content container 自定义内容容器
    Item {
        id: customContentContainer

        anchors.verticalCenter: parent.verticalCenter
        anchors.left: contentLayer.buttonControl.contentAlignment === Enums.button.align_left
                      ? parent.left : undefined
        anchors.right: contentLayer.buttonControl.contentAlignment === Enums.button.align_right
                       ? parent.right : undefined
        anchors.horizontalCenter:
            contentLayer.buttonControl.contentAlignment === Enums.button.align_center
            ? parent.horizontalCenter : undefined
        anchors.leftMargin:
            contentLayer.buttonControl.contentAlignment === Enums.button.align_left
            ? contentLayer.buttonControl._contentLeadingPadding : 0
        anchors.rightMargin:
            contentLayer.buttonControl.contentAlignment === Enums.button.align_right
            ? contentLayer.buttonControl._contentTrailingPadding : 0
        anchors.horizontalCenterOffset:
            contentLayer.buttonControl.contentAlignment === Enums.button.align_center
            ? (contentLayer.buttonControl.feature === Enums.button.feature_split
               ? -Enums.controlSize.splitButtonContentOffset
               : (contentLayer.buttonControl._showsDropdownIndicator
                  ? -Enums.spacing.m : 0)) : 0
        z: Enums.zIndex.content
        visible: contentLayer.buttonControl.hasCustomContent
        onChildrenChanged: contentLayer.buttonControl._syncCustomContentState()
        Component.onCompleted: contentLayer.buttonControl._syncCustomContentState()
        // Neobrutalism press shift moves custom content with the face 新粗野主义按压位移使自定义内容随按钮面移动
        transform: contentLayer.pressTransform
    }

    // Default icon and text content 默认图标与文本内容
    Loader {
        id: contentLoader

        property real _indicatorTransitionWidth: -1

        width: item ? (_indicatorTransitionWidth >= 0
                       ? _indicatorTransitionWidth : item.implicitWidth) : 0
        x: {
            if (contentLayer.buttonControl.contentAlignment === Enums.button.align_left)
                return contentLayer.buttonControl._contentLeadingPadding
            if (contentLayer.buttonControl.contentAlignment === Enums.button.align_right)
                return parent.width - width - contentLayer.buttonControl._contentTrailingPadding
            var centerOffset = contentLayer.buttonControl.feature === Enums.button.feature_split
                               ? -Enums.controlSize.splitButtonContentOffset
                               : (contentLayer.buttonControl._showsDropdownIndicator
                                  ? -Enums.spacing.m : 0)
            return (parent.width - width) / 2 + centerOffset
        }
        anchors.verticalCenter: parent.verticalCenter
        z: Enums.zIndex.content
        active: !contentLayer.buttonControl.hasCustomContent
        // Neobrutalism press shift moves default content with the face 新粗野主义按压位移使默认内容随按钮面移动
        transform: contentLayer.pressTransform
        sourceComponent: ButtonContent {
            feature: contentLayer.buttonControl.feature
            style: contentLayer.buttonControl.style
            text: contentLayer.buttonControl.text
            icon: contentLayer.buttonControl.icon
            iconSize: contentLayer.buttonControl.iconSize
            loading: contentLayer.buttonControl.loading
            loadingText: contentLayer.buttonControl.loadingText
            progress: contentLayer.buttonControl.progress
            textColor: contentLayer.buttonControl.getTextColor()
            fontSize: contentLayer.buttonControl.fontSize
            fontBold: contentLayer.buttonControl.fontBold
            fontItalic: contentLayer.buttonControl.fontItalic
            fontUnderline: contentLayer.buttonControl.fontUnderline
            fontStrikeout: contentLayer.buttonControl.fontStrikeout
            countdownActive: contentLayer.buttonControl._countdownActive
            countdownRemaining: contentLayer.buttonControl._countdownRemaining
            countdownText: contentLayer.buttonControl.countdownText
        }
    }
}
