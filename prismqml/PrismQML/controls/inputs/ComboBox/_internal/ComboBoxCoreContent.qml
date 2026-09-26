// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
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

    // Control surface and skin elevation 控件表面与皮肤层级
    ComboBoxSurface {
        anchors.fill: parent
        comboControl: content.comboControl
        popupClosing: comboPopup.isClosing
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
            // The editable input doubles as the search field. 可编辑输入框同时充当搜索框。
            if (comboControl._search) comboControl._search.apply(editedText)
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
        // Settle the queued prewarm while the button is still down, so the
        // released click opens warm instead of building the native surface
        // inside the click callback.
        // 按键仍按下时就地结算排队中的预热，抬起后的点击即走暖路径，而不是在点击
        // 回调里新建原生表面。
        onPressed: {
            if (comboPopup.flushQueuedPrewarm) comboPopup.flushQueuedPrewarm()
        }
        onClicked: {
            if (comboControl.isOpen && !comboPopup.isClosing) {
                comboControl.closePopup()
            } else if (!comboControl.isOpen && !comboPopup.isClosing) {
                comboControl.openPopup()
            }
        }
        onWheel: (wheel) => {
            var wheelY = WheelEventUtils.verticalDelta(wheel)
            var wheelX = WheelEventUtils.horizontalDelta(wheel)
            var delta = wheelY !== 0 ? wheelY : wheelX
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
        // The candidate list is its own native surface. Editable mode types into
        // this control while the list is open, so activating that surface would
        // abort the keystroke in flight; keep focus in the input instead.
        // Non-editable dropdowns keep the existing native focus behaviour.
        // 候选列表是独立原生窗口。可编辑模式要在候选展开期间持续输入，激活该窗口会
        // 打断正在进行的按键，因此焦点留在输入框；非可编辑下拉维持原有原生焦点行为。
        stealFocus: !comboControl.editable

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
