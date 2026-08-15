// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../../.."
import "../../../../effects"
import "../../../data"
import "../../../icons"
import "../../../utils"
import "../../"
import "../../_internal" as InputsInternal
import "../../../menus"

// ComboBoxCoreContent - ComboBox visual and popup content 下拉框视觉与弹层内容
// Keeps the public ComboBoxCore entry focused on state and orchestration
// 将公开 ComboBoxCore 入口限制为状态与编排。
Item {
    id: content

    // ==================== Required Props 必需属性 ====================
    required property var comboControl

    // ==================== Public Props 公开属性 ====================
    property alias editableInput: editableInput
    property alias mouseArea: mouseArea
    property alias editableClickArea: editableClickArea
    property alias comboTextMeasureLoader: comboTextMeasureLoader
    property alias popup: comboPopup

    anchors.fill: parent

    // ==================== Content 内容 ====================
    // Style helper 样式辅助
    ComboBoxStyleHelper {
        id: styleHelper
        control: content.comboControl
    }

    // Shadow layer below background 背景下方阴影层
    // Fluent: 模糊阴影。Neobrutalism: 硬阴影(纯黑, 展开时转橙强调)。
    RectangularShadow {
        anchors.fill: background
        radius: background.radius
        color: Enums.shadow.level2.color
        blur: Enums.shadow.level2.blur
        offset.x: 0
        offset.y: Enums.shadow.level2.offset
        visible: comboControl.style === 0 && Enums.usesSoftElevation && !Enums.isNeumorphism
    }

    NeumorphicShadow {
        target: background
        inset: true
        visible: comboControl.style === 0 && Enums.isNeumorphism
        z: background.z - 1
    }

    // Neobrutalism 硬阴影: 复用 NeoShadow 组件; 展开时 accent=true 转橙强调。
    NeoShadow {
        target: background
        visible: Enums.isNeobrutalism && comboControl.style === 0
        accent: comboControl.popupVisible
        z: background.z - 1
    }

    // Background 背景
    Rectangle {
        id: background
        anchors.fill: parent
        radius: content.comboControl.radius
        clip: false

        layer.enabled: true
        layer.effect: OpacityMask {
            mask: Rectangle {
                width: background.width
                height: background.height
                radius: background.radius
            }
        }

        // Fluent Design style Fluent Design样式
        // Unified with Button/LineEdit controlBg series 与Button/LineEdit统一使用controlBg系列
        color: {
            if (comboControl.style !== 0) return styleHelper.getBackgroundColor()
            if (!comboControl.enabled) return Enums.stateColor.controlBgDisabled
            if (comboControl.popupVisible) return Enums.stateColor.controlBgPressed
            if (comboControl.pressed) return Enums.stateColor.controlBgPressed
            if (comboControl.hovered) return Enums.stateColor.controlBgHover
            return Enums.stateColor.controlBg
        }

        // Fluent Design 边框:亮/暗主题各用低透明度描边,具体取值见 StateColor.pickerBorder
        border.width: comboControl.style !== 0
            ? 0
            : Enums.surfaceBorderWidth(Enums.border.thin)
        border.color: Enums.isNeobrutalism && comboControl.style === 0
            ? (!comboControl.enabled ? Enums.stateColor.comboBoxDisabledBorder
               : (comboControl.popupVisible ? Enums.neo.primary : Enums.neo.borderColor))
            : (Enums.isVintageTicket && comboControl.style === 0
               ? (!comboControl.enabled ? Enums.stateColor.borderLight
                  : (comboControl.popupVisible ? Enums.accentColor : Enums.borderColor))
            : styleHelper.getBorderColor()
            )

        // Color animation (not applied during close to avoid delay) 颜色动画
        HoverBehavior on color {
            active: comboControl.hovered && !comboControl.pressed &&
                    !comboControl.popupVisible
            animationEnabled: !comboPopup.isClosing
            enterDuration: Enums.duration.fast
        }
    }

    // Focus accent line (ONLY for editable mode) 聚焦主题色底线(仅editable模式)
    FocusLine {
        showLine: !Enums.hasOutlinedSurfaces && comboControl.editable &&
                  editableInput.activeFocus && comboControl.showFocusedBorder
        lineColor: comboControl.focusedBorderColor
        parentRadius: comboControl.radius
        visible: !Enums.hasOutlinedSurfaces && comboControl.editable &&
                 comboControl.showFocusedBorder
    }

    // Current text (non-editable mode) 当前文本
    Label {
        anchors.left: parent.left
        anchors.right: arrow.left
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: Enums.spacing.l
        anchors.rightMargin: Enums.spacing.m
        type: Enums.label.type_body
        text: comboControl.currentText !== ""
            ? comboControl.currentText : comboControl.placeholderText
        color: styleHelper.getTextColor()
        wrapMode: Text.NoWrap
        elide: Text.ElideRight
        clip: true
        visible: !comboControl.editable && comboControl.useDefaultContent
    }

    // Editable input (editable mode) 可编辑输入框
    TextInput {
        id: editableInput
        anchors.left: parent.left
        anchors.right: arrow.left
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: Enums.spacing.l
        anchors.rightMargin: Enums.spacing.m
        text: comboControl.currentText
        font.family: Enums.fontFamily
        font.pixelSize: Enums.typography.body
        color: styleHelper.getTextColor()
        selectionColor: Enums.accentColor
        selectedTextColor: Enums.accentForeground
        selectByMouse: true
        visible: comboControl.editable && comboControl.useDefaultContent
        enabled: comboControl.enabled

        onTextEdited: {
            var editedText = text
            if (comboControl.currentIndex !== -1) comboControl.currentIndex = -1
            comboControl.currentText = editedText
            if (comboControl.textEdited) comboControl.textEdited(editedText)
        }

        InputsInternal.InputPlaceholderLabel {
            anchors.fill: parent
            text: comboControl.placeholderText
            visible: !parent.text && !parent.activeFocus
        }
    }

    // Dropdown arrow 下拉箭头
    ChevronIcon {
        id: arrow
        anchors.right: parent.right
        anchors.rightMargin: Enums.spacing.l
        anchors.verticalCenter: parent.verticalCenter
        animated: true
        isOpen: comboControl.isOpen
        color: comboControl.enabled
            ? (comboControl.style === 1
                ? Enums.accentForeground : Enums.textColor.secondary)
            : Enums.stateColor.indicatorActive
    }

    // Interaction 交互
    // Editable mode: only respond to arrow area clicks, let TextInput work editable模式
    // Non-editable mode: whole area responds 非editable模式
    MouseArea {
        id: mouseArea
        anchors.fill: comboControl.editable ? undefined : parent
        anchors.right: comboControl.editable ? parent.right : undefined
        anchors.top: comboControl.editable ? parent.top : undefined
        anchors.bottom: comboControl.editable ? parent.bottom : undefined
        width: comboControl.editable ? Enums.comboBoxMetrics.arrowAreaWidth : undefined
        enabled: comboControl.enabled && !comboPopup.isClosing
        hoverEnabled: true

        onContainsMouseChanged: {
            if (containsMouse) {
                comboControl._popupContentRequested = true
                if (comboPopup.prewarm) comboPopup.prewarm()
            }
        }
        onClicked: {
            if (comboControl.isOpen && !comboPopup.isClosing) {
                comboControl.closePopup()
            } else if (!comboControl.isOpen && !comboPopup.isClosing) {
                comboControl.openPopup()
            }
        }
        onWheel: (wheel) => {
            var delta = wheel.angleDelta.y !== 0 ? wheel.angleDelta.y : wheel.angleDelta.x
            comboControl.wheelScrolled(delta)
            wheel.accepted = comboControl.acceptWheel
        }
    }

    // Editable mode: focus input area when clicked 点击输入框区域时聚焦
    MouseArea {
        id: editableClickArea
        anchors.left: parent.left
        anchors.right: mouseArea.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        visible: comboControl.editable
        enabled: comboControl.enabled && comboControl.editable
        hoverEnabled: true
        cursorShape: Qt.IBeamCursor
        onClicked: editableInput.forceActiveFocus()
    }

    // Content width measurement 内容宽度测量
    Loader {
        id: comboTextMeasureLoader
        active: comboControl._popupContentRequested
        sourceComponent: TextMetrics {
            font.family: Enums.fontFamily
            font.pixelSize: Enums.typography.body
        }
    }

    // Popup window using unified base 使用统一基类的弹出窗口
    PopupWindowCore {
        id: comboPopup
        popupWidth: comboControl.width
        implicitContentHeight: Math.max(
            0, Enums.comboBoxMetrics.popupDefaultHeight - 2 * contentPadding)
        closeOnClickOutside: comboControl.popupCloseOnClickOutside

        onClosed: {
            if (comboControl.isOpen) comboControl.isOpen = false
        }

        Loader {
            anchors.fill: parent
            active: comboControl._popupContentRequested
            sourceComponent: comboControl.popupContent

            onLoaded: {
                if (item && item.hasOwnProperty("control")) {
                    item.control = comboControl
                }
            }
        }
    }
}
