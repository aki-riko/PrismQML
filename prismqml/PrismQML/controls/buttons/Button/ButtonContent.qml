// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../icons"
import "../../feedback"

// ButtonContent - Shared axis-aware content layout 共享轴向内容布局
// style_text_under is the only vertical presentation; all other styles stay inline.
// style_text_under 是唯一的纵向展示, 其它样式保持横向。
Item {
    id: content

    // ==================== Required Props 必需属性 ====================
    required property int feature
    required property int style
    required property string text
    required property string icon
    required property int iconSize
    required property bool loading
    required property string loadingText
    required property real progress
    required property color textColor
    required property int fontSize

    // ==================== Public Props 公开属性 ====================
    property bool fontBold: false
    property bool fontItalic: false
    property bool fontUnderline: false
    property bool fontStrikeout: false
    property bool countdownActive: false
    property int countdownRemaining: 0
    property string countdownText: "s"
    property var skinContext: Enums

    // ==================== Readonly State 只读状态 ====================
    readonly property bool verticalLayout: style === skinContext.commandBar.style_text_under
    readonly property bool hasIcon: icon !== "" || loading
        || feature === skinContext.button.feature_progress_ring
        || feature === skinContext.button.feature_indeterminate_ring
    readonly property bool _useForegroundColor: style === skinContext.button.style_primary
        || style === skinContext.button.style_filled
        || style === skinContext.button.style_gradient
    readonly property color _ringColor: _useForegroundColor
        ? skinContext.accentForeground : skinContext.accentColor
    readonly property color _ringBorderColor: _useForegroundColor
        ? skinContext.stateColor.onAccentOverlay : skinContext.stateColor.loadingBorder
    readonly property bool _hasDeterminateRing:
        feature === skinContext.button.feature_progress_ring
    readonly property bool _hasIndeterminateRing:
        feature === skinContext.button.feature_indeterminate_ring
    readonly property bool _hasFeatureRing: _hasDeterminateRing || _hasIndeterminateRing
    readonly property string _displayText: {
        if (countdownActive) return countdownRemaining + countdownText
        if (loading && loadingText !== "") return loadingText
        return text
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: verticalLayout
        ? Math.max(iconSize, contentText.implicitWidth)
        : iconSize * (hasIcon ? 1 : 0)
          + Enums.spacing.xs * (hasIcon && contentText.visible ? 1 : 0)
          + contentText.implicitWidth
    implicitHeight: verticalLayout
        ? (hasIcon ? iconSize + Enums.spacing.xxs : 0) + contentText.implicitHeight
        : Math.max(iconSize, contentText.implicitHeight)

    // ==================== Content 内容 ====================
    Loader {
        id: loadingRingLoader

        active: content.loading
        width: active ? content.iconSize : 0
        height: active ? content.iconSize : 0
        x: content.verticalLayout
            ? (content.width - width) / 2 : 0
        y: content.verticalLayout
            ? 0 : (content.height - height) / 2
        sourceComponent: loadingComponent
    }

    Loader {
        id: featureRingLoader

        active: content._hasFeatureRing
        width: active ? content.iconSize : 0
        height: active ? content.iconSize : 0
        x: content.verticalLayout
            ? (content.width - width) / 2 : 0
        y: content.verticalLayout
            ? 0 : (content.height - height) / 2
        sourceComponent: featureRingComponent
    }

    Loader {
        id: iconLoader

        objectName: "buttonContentVisual"
        active: !content.loading && content.icon !== ""
        width: active ? content.iconSize : 0
        height: active ? content.iconSize : 0
        x: content.verticalLayout
            ? (content.width - width) / 2 : 0
        y: content.verticalLayout
            ? 0 : (content.height - height) / 2
        sourceComponent: iconComponent
    }

    Text {
        id: contentText

        objectName: "buttonContentText"
        x: content.verticalLayout
            ? (content.width - implicitWidth) / 2
            : (content.hasIcon ? iconLoader.width + Enums.spacing.xs : 0)
        y: content.verticalLayout
            ? (content.hasIcon ? iconLoader.height + Enums.spacing.xxs : 0)
            : (content.height - implicitHeight) / 2
        text: content._displayText
        font.family: content.skinContext.fontFamily
        font.pixelSize: content.fontSize
        font.bold: content.fontBold
        font.italic: content.fontItalic
        font.underline: content.fontUnderline
            || content.style === content.skinContext.button.style_hyperlink
        font.strikeout: content.fontStrikeout
        color: content.textColor
        wrapMode: Text.WordWrap
        visible: text !== ""
    }

    Component {
        id: loadingComponent

        ProgressRing {
            anchors.fill: parent
            strokeWidth: content.skinContext.border.normal
            color: content.textColor
            indeterminate: true
        }
    }

    Component {
        id: featureRingComponent

        ProgressRing {
            anchors.fill: parent
            from: 0
            to: 1
            value: content.progress
            strokeWidth: content.skinContext.border.normal
            indeterminate: content._hasIndeterminateRing
            color: content._ringColor
            trackColorLight: content._hasDeterminateRing
                ? content._ringBorderColor : content.skinContext.stateColor.track
            trackColorDark: content._hasDeterminateRing
                ? content._ringBorderColor
                : (content.skinContext.isVintageTicket
                   ? content.skinContext.stateColor.progressTrack
                   : content.skinContext.stateColor.whiteOverlay)
        }
    }

    Component {
        id: iconComponent

        Icon {
            objectName: "buttonContentIcon"
            anchors.centerIn: parent
            icon: content.icon
            iconSize: content.iconSize
            color: content.textColor
        }
    }
}
