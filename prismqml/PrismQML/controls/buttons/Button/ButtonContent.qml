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
    property bool _verticalContent: false

    // ==================== Readonly State 只读状态 ====================
    readonly property bool verticalLayout: _verticalContent
    readonly property bool hasIcon: icon !== "" || loading
        || feature === skinContext.button.feature_progress_ring
        || feature === skinContext.button.feature_indeterminate_ring
    readonly property bool _useForegroundColor: style === skinContext.button.style_primary
        || style === skinContext.button.style_filled
        || style === skinContext.button.style_gradient
        || style === skinContext.button.style_glow
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
    // Inline slot order matches the historical Row: loading ring, feature ring,
    // icon, text. A slot only participates when it is visible and non-zero wide,
    // and the shared gap sits between consecutive participants only — the exact
    // rule Qt's Row applied before this layout became manual. A zero-width or
    // hidden visual therefore never pushes its neighbour sideways.
    // 横向槽位顺序沿用历史 Row: 加载环、功能环、图标、文字。只有可见且宽度非零的槽位
    // 参与排布, 共享间距只落在相邻的两个参与槽位之间 —— 这正是本布局改为手工定位前
    // Qt Row 所遵循的规则。零宽或隐藏的视觉因此不会把相邻项挤开。
    readonly property bool _showsLoadingRing: loading
    readonly property bool _showsIconVisual: !loading && icon !== ""
    // The vertical presentation stacks one leading visual above the text, so it
    // keeps exactly one: loading ring, else feature ring, else icon. The inline
    // presentation keeps placing every occupied slot side by side.
    // 纵向展示把前导视觉堆在文字上方, 因此只保留一个: 加载环 > 功能环 > 图标。
    // 横向展示继续把每个占位槽位并排排布。
    readonly property bool _verticalLeadingLoading: loading
    readonly property bool _verticalLeadingRing: !loading && _hasFeatureRing
    readonly property bool _verticalLeadingIcon: !loading && !_hasFeatureRing
        && _showsIconVisual
    readonly property bool _verticalHasLeading: _verticalLeadingLoading
        || _verticalLeadingRing || _verticalLeadingIcon
    // Effective visibility per axis: vertical drops the losing leading visuals.
    // 各轴的生效可见性: 纵向会隐藏落选的前导视觉。
    readonly property bool _loadingVisualVisible: verticalLayout
        ? _verticalLeadingLoading : _showsLoadingRing
    readonly property bool _featureRingVisible: verticalLayout
        ? _verticalLeadingRing : _hasFeatureRing
    readonly property bool _iconVisible: verticalLayout
        ? _verticalLeadingIcon : _showsIconVisual
    readonly property bool _textVisible: _displayText !== ""
    readonly property real _loadingSlotWidth: _showsLoadingRing ? iconSize : 0
    readonly property real _featureSlotWidth: _hasFeatureRing ? iconSize : 0
    readonly property real _iconSlotWidth: _showsIconVisual ? iconSize : 0
    readonly property real _textSlotWidth: _textVisible ? contentText.implicitWidth : 0
    readonly property int _loadingSlotCount: _loadingSlotWidth > 0 ? 1 : 0
    readonly property int _featureSlotCount: _featureSlotWidth > 0 ? 1 : 0
    readonly property int _iconSlotCount: _iconSlotWidth > 0 ? 1 : 0
    readonly property int _textSlotCount: _textSlotWidth > 0 ? 1 : 0
    readonly property int _placedSlotCount: _loadingSlotCount + _featureSlotCount
        + _iconSlotCount + _textSlotCount
    readonly property real _placedSlotWidth: _loadingSlotWidth + _featureSlotWidth
        + _iconSlotWidth + _textSlotWidth
    readonly property real _slotGap: skinContext.spacing.s
    // Prefix sums: participants and accumulated width preceding each slot.
    // 前缀和: 每个槽位之前已排布的参与槽位数量与累计宽度。
    readonly property int _slotsBeforeFeature: _loadingSlotCount
    readonly property int _slotsBeforeIcon: _loadingSlotCount + _featureSlotCount
    readonly property int _slotsBeforeText: _loadingSlotCount + _featureSlotCount
        + _iconSlotCount
    readonly property real _widthBeforeFeature: _loadingSlotWidth
    readonly property real _widthBeforeIcon: _loadingSlotWidth + _featureSlotWidth
    readonly property real _widthBeforeText: _loadingSlotWidth + _featureSlotWidth
        + _iconSlotWidth
    // A slot that does not participate keeps x = 0, exactly as Row left skipped
    // items untouched instead of parking them at a computed offset.
    // 不参与的槽位保持 x = 0, 与 Row 不对被跳过项做定位的行为一致。
    readonly property real _loadingSlotX: 0
    readonly property real _featureSlotX: _featureSlotCount > 0
        ? _widthBeforeFeature + _slotsBeforeFeature * _slotGap : 0
    readonly property real _iconSlotX: _iconSlotCount > 0
        ? _widthBeforeIcon + _slotsBeforeIcon * _slotGap : 0
    readonly property real _textSlotX: _textSlotCount > 0
        ? _widthBeforeText + _slotsBeforeText * _slotGap : 0

    // ==================== Size 尺寸 ====================
    implicitWidth: verticalLayout
        ? Math.max(iconSize, contentText.implicitWidth)
        : _placedSlotWidth + Math.max(_placedSlotCount - 1, 0) * _slotGap
    implicitHeight: verticalLayout
        ? (_verticalHasLeading ? iconSize + Enums.spacing.xxs : 0)
          + contentText.implicitHeight
        : Math.max(_loadingSlotWidth + _featureSlotWidth + _iconSlotWidth > 0
                   ? iconSize : 0,
                   _textSlotWidth > 0 ? contentText.implicitHeight : 0)

    // ==================== Content 内容 ====================
    Loader {
        id: loadingRingLoader

        active: content._loadingVisualVisible
        width: active ? content.iconSize : 0
        height: active ? content.iconSize : 0
        x: content.verticalLayout
            ? (content.width - width) / 2
            : content._loadingSlotX
        y: content.verticalLayout
            ? 0 : (content.height - height) / 2
        sourceComponent: loadingComponent
    }

    Loader {
        id: featureRingLoader

        active: content._featureRingVisible
        width: active ? content.iconSize : 0
        height: active ? content.iconSize : 0
        x: content.verticalLayout
            ? (content.width - width) / 2
            : content._featureSlotX
        y: content.verticalLayout
            ? 0 : (content.height - height) / 2
        sourceComponent: featureRingComponent
    }

    Loader {
        id: iconLoader

        objectName: "buttonContentVisual"
        active: content._iconVisible
        width: active ? content.iconSize : 0
        height: active ? content.iconSize : 0
        x: content.verticalLayout
            ? (content.width - width) / 2
            : content._iconSlotX
        y: content.verticalLayout
            ? 0 : (content.height - height) / 2
        sourceComponent: iconComponent
    }

    Text {
        id: contentText

        objectName: "buttonContentText"
        x: content.verticalLayout
            ? (content.width - implicitWidth) / 2
            : content._textSlotX
        y: content.verticalLayout
            ? (content._verticalHasLeading
               ? content.iconSize + Enums.spacing.xxs : 0)
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
        visible: content._textVisible
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
