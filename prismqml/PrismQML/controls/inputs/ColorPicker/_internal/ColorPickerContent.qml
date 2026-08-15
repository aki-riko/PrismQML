// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Window
import "../../../.."
import "../../../utils"
import "../../../buttons/Button"
import "../../../icons"
import "."

// ColorPickerContent - Trigger, popup, and dialog content 触发器、弹层与对话框内容
// Keeps ColorPicker focused on public state and lifecycle orchestration.
// 将 ColorPicker 入口限制为公开状态与生命周期编排。
Item {
    id: content

    // ==================== Required Props 必需属性 ====================
    required property var colorControl

    // ==================== Public Props 公开属性 ====================
    property alias circleLoader: circleLoader
    property alias popup: popup
    property alias paletteDialogLoader: paletteDialogLoader
    property alias dialogLoader: dialogLoader

    anchors.fill: parent

    // ==================== Content 内容 ====================
    // Trigger button for dropdown types 下拉类型触发按钮
    Loader {
        id: triggerLoader
        parent: colorControl
        anchors.fill: parent
        active: colorControl.type === Enums.colorPicker.type_dialog
                || colorControl.type === Enums.colorPicker.type_palette
                || colorControl.type === Enums.colorPicker.type_picker
        sourceComponent: ColorPickerTrigger {
            selectedColor: colorControl.selectedColor
            isOpen: colorControl._isOpen
            enabled: colorControl.enabled
            menu: colorControl.type === Enums.colorPicker.type_palette
                   || colorControl.type === Enums.colorPicker.type_picker ? popup : null
            onMenuAboutToOpen: colorControl._preparePopup()
            onHoveredChanged: {
                if (hovered) colorControl._prewarmTriggerContent()
            }
            onClicked: {
                // Prevent reopen during closing animation 防止关闭动画期间重新打开
                if (popup.isClosing) return
                if (colorControl._isOpen) {
                    colorControl.close()
                } else {
                    colorControl.open()
                }
            }
        }
    }

    // Circle colors 圆形颜色
    Loader {
        id: circleLoader
        parent: colorControl
        anchors.fill: parent
        active: colorControl.type === Enums.colorPicker.type_circle
        sourceComponent: ColorCircles {
            selectedColor: colorControl.selectedColor
            colors: colorControl.circleColors
            circleSize: colorControl.circleSize
            enabled: colorControl.enabled
            onColorSelected: (c) => {
                colorControl.selectedColor = c
                colorControl.colorSelected(c)
                colorControl.colorChanged(c)
            }
        }
    }

    // Screen picker 屏幕取色器
    Loader {
        id: screenLoader
        parent: colorControl
        anchors.fill: parent
        active: colorControl.type === Enums.colorPicker.type_screen
        sourceComponent: CustomButtonCore {
            id: screenPickerBtn
            text: ""
            enabled: colorControl.enabled

            // Override background color 覆盖背景色
            getBackgroundColor: function() {
                if (!enabled) return Enums.stateColor.controlBgDisabled
                if (pressed) return Enums.stateColor.controlBgPressed
                if (hovered) return Enums.stateColor.controlBgHover
                return Enums.stateColor.controlBg
            }

            getBorderColor: function() {
                if (!enabled) return Enums.stateColor.borderLight
                if (hovered) return Enums.stateColor.borderStrong
                return Enums.stateColor.border
            }

            onClicked: {
                if (!colorControl.picking) {
                    // Start picking via Python manager 通过Python管理器开始取色
                    colorControl.picking = true
                    colorControl.pickingStarted()
                    if (typeof ScreenEyedropperManager !== "undefined") {
                        ScreenEyedropperManager.startPicking(Enums.isDark)
                    }
                }
            }

            // Custom content 自定义内容
            Row {
                anchors.centerIn: parent
                spacing: Enums.spacing.s

                // Left: Color swatch 左侧：色块
                Rectangle {
                    width: Enums.spacing.xl
                    height: Enums.spacing.xl
                    radius: Enums.radius.small
                    anchors.verticalCenter: parent.verticalCenter
                    color: colorControl.selectedColor
                    border.width: Enums.border.thin
                    border.color: Enums.stateColor.inputBorderStrong
                }

                // Right: Eyedropper icon 右侧：吸管图标
                Icon {
                    icon: Enums.icon.eyedropper
                    iconSize: Enums.iconSize.s
                    color: screenPickerBtn.getTextColor()
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
    }

    // Screen picker connections 屏幕取色器连接
    Connections {
        function onColorPicked(color) {
            colorControl.selectedColor = color
            colorControl.colorSelected(color)
            colorControl.colorChanged(color)
        }

        function onPickingFinished() {
            colorControl.picking = false
            colorControl.pickingFinished()
        }

        function onPickingCancelled() {
            colorControl.picking = false
        }

        target: typeof ScreenEyedropperManager !== "undefined"
                ? ScreenEyedropperManager : null
        enabled: colorControl.type === Enums.colorPicker.type_screen
    }

    // Palette and picker popup 调色板与选择器弹层
    PopupWindowCore {
        id: popup
        parent: colorControl
        popupWidth: {
            switch (colorControl.type) {
                case Enums.colorPicker.type_palette:
                    return Enums.colorPickerMetrics.palettePopupWidth
                case Enums.colorPicker.type_picker:
                    return Enums.colorPickerMetrics.pickerPopupWidth
                default:
                    return Enums.colorPickerMetrics.fallbackPopupWidth
            }
        }
        popupHeight: {
            switch (colorControl.type) {
                case Enums.colorPicker.type_palette:
                    return Enums.colorPickerMetrics.palettePopupHeight
                case Enums.colorPicker.type_picker:
                    return Enums.colorPickerMetrics.pickerPopupHeight
                default:
                    return Enums.colorPickerMetrics.fallbackPopupHeight
            }
        }

        onClosed: colorControl._isOpen = false

        // Palette content 调色板内容
        Loader {
            anchors.fill: parent
            active: colorControl.type === Enums.colorPicker.type_palette
                    && (colorControl._isOpen || colorControl._popupContentRequested)
            sourceComponent: ColorPalette {
                selectedColor: colorControl.selectedColor
                showAutomatic: colorControl.showAutomatic
                showMoreColors: colorControl.showMoreColors
                automaticText: colorControl.automaticText
                themeColorsText: colorControl.themeColorsText
                standardColorsText: colorControl.standardColorsText
                moreColorsText: colorControl.moreColorsText
                enabled: colorControl.enabled
                onColorSelected: (c) => {
                    colorControl.selectedColor = c
                    colorControl.colorSelected(c)
                    colorControl.colorChanged(c)
                    popup.close()
                }
                onMoreColorsClicked: {
                    popup.close()
                    colorControl.moreColorsClicked()
                    colorControl._openPaletteDialog()
                }
                onMoreColorsPrewarmRequested: colorControl._paletteDialogRequested = true
            }
        }

        // Picker content 选择器内容
        Loader {
            anchors.fill: parent
            active: colorControl.type === Enums.colorPicker.type_picker
                    && (colorControl._isOpen || colorControl._popupContentRequested)
            sourceComponent: ColorPickerDropdown {
                selectedColor: colorControl.selectedColor
                colorMode: colorControl.colorMode
                enableAlpha: colorControl.enableAlpha
                enabled: colorControl.enabled
                onColorChanged: (c) => {
                    colorControl.selectedColor = c
                    colorControl.colorChanged(c)
                }
                onAccepted: (c) => {
                    colorControl.selectedColor = c
                    colorControl.colorSelected(c)
                    colorControl.accepted(c)
                    popup.close()
                }
                onRejected: {
                    colorControl.selectedColor = colorControl.defaultColor
                    colorControl.rejected()
                    popup.close()
                }
            }
        }
    }

    // Palette color-dialog loader 调色板颜色对话框加载器
    Loader {
        id: paletteDialogLoader
        parent: colorControl
        active: colorControl.type === Enums.colorPicker.type_palette
                && colorControl._paletteDialogRequested
        sourceComponent: ColorPickerDialog {
            title: { Translator._v; return Translator.tr("custom_color") }
            selectedColor: colorControl.selectedColor
            onColorAccepted: (c) => {
                colorControl.selectedColor = c
                colorControl.colorSelected(c)
            }
        }
    }

    // Modal dialog loader 模态对话框加载器
    Loader {
        id: dialogLoader
        parent: colorControl
        active: colorControl.type === Enums.colorPicker.type_dialog
                && colorControl._dialogRequested
        sourceComponent: ColorPickerDialog {
            selectedColor: colorControl.selectedColor
            title: colorControl.dialogTitle
            editColorText: colorControl.editColorText
            confirmText: colorControl.confirmText
            cancelText: colorControl.cancelText
            enableAlpha: colorControl.enableAlpha
            enabled: colorControl.enabled
            overlayTarget: colorControl.parent
            onColorAccepted: (c) => {
                colorControl.selectedColor = c
                colorControl.colorSelected(c)
                colorControl.accepted(c)
                colorControl._isOpen = false
            }
            onRejected: {
                colorControl.rejected()
                colorControl._isOpen = false
            }
            onColorUpdated: (c) => {
                colorControl.colorChanged(c)
            }
        }
    }
}
