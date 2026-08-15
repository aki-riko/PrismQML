// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import ".."

// ToggleContent - Toggle visual assembly Toggle视觉装配
// Owns indicator/content factories while Toggle keeps state and interaction orchestration.
// 承载指示器/内容工厂，Toggle 保留状态与交互编排。
Row {
    id: content

    // ==================== Required Props 必需属性 ====================
    required property var toggleControl

    // ==================== Readonly State 只读状态 ====================
    readonly property bool contentLoaded: contentLoader.item !== null
    readonly property real contentImplicitHeight:
        contentLoader.item ? contentLoader.item.implicitHeight : 0

    // ==================== Size 尺寸 ====================
    anchors.verticalCenter: parent.verticalCenter
    spacing: toggleControl._isIndicatorOnly
        ? 0
        : (toggleControl._isSubtitle ? Enums.spacing.l : Enums.spacing.m)

    // ==================== Content 内容 ====================
    // Indicator 指示器
    Loader {
        id: indicatorLoader

        anchors.verticalCenter: toggleControl._isSubtitle
            ? undefined : parent.verticalCenter
        anchors.top: toggleControl._isSubtitle ? parent.top : undefined
        anchors.topMargin: toggleControl._isSubtitle ? Enums.spacing.xxs : 0
        sourceComponent: {
            if (content.toggleControl._isSwitch) return switchIndicator
            if (content.toggleControl._isRadio) return radioIndicator
            return checkboxIndicator
        }
    }

    // Content 内容
    Loader {
        id: contentLoader

        anchors.verticalCenter: parent.verticalCenter
        active: !content.toggleControl._isIndicatorOnly
            && (content.toggleControl.text !== ""
                || content.toggleControl.subtitle !== "")
        sourceComponent: content.toggleControl._isSubtitle
            ? subtitleContent : defaultContent
    }

    // CheckBox indicator 复选框指示器
    Component {
        id: checkboxIndicator

        ToggleCheckIndicator {
            checkState: content.toggleControl.checkState
            enabled: content.toggleControl.enabled
            hovered: content.toggleControl.hovered
            pressed: content.toggleControl.pressed
            checkedColor: content.toggleControl._checkedColor
        }
    }

    // Radio indicator 单选按钮指示器
    Component {
        id: radioIndicator

        ToggleRadioIndicator {
            checked: content.toggleControl.checked
            enabled: content.toggleControl.enabled
            hovered: content.toggleControl.hovered
            pressed: content.toggleControl.pressed
        }
    }

    // Switch indicator 开关指示器
    Component {
        id: switchIndicator

        ToggleSwitchIndicator {
            checked: content.toggleControl.checked
            enabled: content.toggleControl.enabled
            hovered: content.toggleControl.hovered
            pressed: content.toggleControl.pressed
            checkedColor: content.toggleControl._checkedColor
            onClicked: content.toggleControl._handleClick()
        }
    }

    // Default content 默认内容
    Component {
        id: defaultContent

        ToggleDefaultContent {
            text: content.toggleControl.text
            icon: content.toggleControl.icon
            iconSize: content.toggleControl.iconSize
            textColor: content.toggleControl._textColor
            showIcon: content.toggleControl._isCheckBox
        }
    }

    // Subtitle content 副标题内容
    Component {
        id: subtitleContent

        ToggleSubtitleContent {
            text: content.toggleControl.text
            subtitle: content.toggleControl.subtitle
            textColor: content.toggleControl._textColor
        }
    }
}
