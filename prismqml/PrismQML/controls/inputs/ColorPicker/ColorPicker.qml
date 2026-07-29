// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../.."
import "_internal"
import "../../utils"
import "../../buttons/Button"
import "../../icons"
import QtQuick.Window  // 置于库import后:原生Window名归库后不被覆盖
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// ColorPicker - Unified color picker component 统一颜色选择器组件
// Control via type property 通过type属性控制类型
// Types: dialog, palette, picker, circle, and screen 类型：对话框、调色板、选择器、圆形与屏幕取色
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property int type: Enums.colorPicker.type_picker
    property int colorMode: Enums.colorPicker.mode_rgb
    property color selectedColor: Enums.colorPickerDefaults.defaultColor
    property color defaultColor: Enums.colorPickerDefaults.defaultColor
    property bool enableAlpha: true
    property var circleColors: Enums.colorPickerDefaults.quickPalette
    property int circleSize: Enums.colorPickerMetrics.circleDefaultSize
    property string dialogTitle: {
        Translator._v
        return Translator.tr("choose_background_color")
    }
    property string editColorText: {
        Translator._v
        return Translator.tr("edit_color")
    }
    property string confirmText: { Translator._v; return Translator.tr("ok") }
    property string cancelText: { Translator._v; return Translator.tr("cancel") }
    property bool showAutomatic: true
    property bool showMoreColors: true
    property string automaticText: {
        Translator._v
        return Translator.tr("default_color_text")
    }
    property string themeColorsText: {
        Translator._v
        return Translator.tr("theme_colors")
    }
    property string standardColorsText: {
        Translator._v
        return Translator.tr("standard_colors")
    }
    property string moreColorsText: {
        Translator._v
        return Translator.tr("more_colors")
    }
    property bool picking: false

    // ==================== Internal Props 内部属性 ====================
    property bool _isOpen: false
    property var _mainWindow: Window.window  // Main window reference for ColorDialog 主窗口引用

    // ==================== Readonly State 只读状态 ====================
    readonly property bool popupVisible: _isOpen

    // ==================== Signals 信号 ====================
    signal colorSelected(color value)
    signal colorChanged(color value)
    signal accepted(color value)
    signal rejected()
    signal pickingStarted()
    signal pickingFinished()
    signal moreColorsClicked()

    // ==================== Public Methods 公开方法 ====================
    function open() {
        if (type === Enums.colorPicker.type_dialog) {
            // Set overlay target before opening 打开前设置覆盖目标
            if (dialogLoader.item) {
                dialogLoader.item.overlayTarget = control.parent
                dialogLoader.item.open()
            }
            _isOpen = true
        } else if (type === Enums.colorPicker.type_palette ||
                   type === Enums.colorPicker.type_picker) {
            popup.openAtControl(control)
            _isOpen = true
        }
    }

    function close() {
        if (type === Enums.colorPicker.type_dialog) {
            if (dialogLoader.item) dialogLoader.item.close()
        } else {
            popup.close()
        }
        _isOpen = false
    }

    function _preparePopup() {
        if (type === Enums.colorPicker.type_palette ||
                type === Enums.colorPicker.type_picker) {
            _isOpen = true
        }
    }

    // Open ColorDialog from palette "自定义颜色" button 从调色板"自定义颜色"按钮打开
    function _openPaletteDialog() {
        if (_mainWindow && _mainWindow.contentItem) {
            paletteDialogLoader.parent = _mainWindow.contentItem
            paletteDialogLoader.anchors.fill = _mainWindow.contentItem
            if (paletteDialogLoader.item) {
                paletteDialogLoader.item.selectedColor = control.selectedColor
                paletteDialogLoader.item.open()
            }
        }
    }

    function setColor(color) {
        selectedColor = color
        defaultColor = color
    }

    // Screen picker helper 屏幕取色辅助
    function setPickedColor(color) {
        selectedColor = color
        colorSelected(color)
        picking = false
        pickingFinished()
    }

    // Get selected color 获取选中颜色
    function getColor() {
        return selectedColor
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: {
        switch (type) {
            case Enums.colorPicker.type_dialog: return Enums.colorPickerMetrics.triggerWidth
            case Enums.colorPicker.type_palette: return Enums.colorPickerMetrics.triggerWidth
            case Enums.colorPicker.type_picker: return Enums.colorPickerMetrics.triggerWidth
            case Enums.colorPicker.type_circle: return circleLoader.item ? circleLoader.item.implicitWidth : Enums.colorPickerMetrics.circleLoaderFallbackWidth
            case Enums.colorPicker.type_screen: return Enums.colorPickerMetrics.triggerWidth
            default: return Enums.colorPickerMetrics.triggerWidth
        }
    }
    implicitHeight: {
        switch (type) {
            case Enums.colorPicker.type_circle: return circleSize
            case Enums.colorPicker.type_screen: return Enums.controlSize.inputHeight
            default: return Enums.controlSize.inputHeight
        }
    }

    // ==================== Content 内容 ====================
    // Trigger button for dropdown types 下拉类型触发按钮
    Loader {
        id: triggerLoader
        anchors.fill: parent
        active: type === Enums.colorPicker.type_dialog ||
                type === Enums.colorPicker.type_palette ||
                type === Enums.colorPicker.type_picker
        sourceComponent: ColorPickerTrigger {
            selectedColor: control.selectedColor
            isOpen: control._isOpen
            enabled: control.enabled
            menu: control.type === Enums.colorPicker.type_palette ||
                  control.type === Enums.colorPicker.type_picker ? popup : null
            onMenuAboutToOpen: control._preparePopup()
            onClicked: {
                // Prevent reopen during closing animation 防止关闭动画期间重新打开
                if (popup.isClosing) return
                if (control._isOpen) {
                    control.close()
                } else {
                    control.open()
                }
            }
        }
    }

    // Circle colors 圆形颜色
    Loader {
        id: circleLoader
        anchors.fill: parent
        active: type === Enums.colorPicker.type_circle
        sourceComponent: ColorCircles {
            selectedColor: control.selectedColor
            colors: control.circleColors
            circleSize: control.circleSize
            enabled: control.enabled
            onColorSelected: (c) => {
                control.selectedColor = c
                control.colorSelected(c)
                control.colorChanged(c)
            }
        }
    }

    // Screen picker 屏幕取色器
    Loader {
        id: screenLoader
        anchors.fill: parent
        active: type === Enums.colorPicker.type_screen
        sourceComponent: CustomButtonCore {
            id: screenPickerBtn
            text: ""
            enabled: control.enabled
            
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
                if (!control.picking) {
                    // Start picking via Python manager 通过Python管理器开始取色
                    control.picking = true
                    control.pickingStarted()
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
                    color: control.selectedColor
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
            control.selectedColor = color
            control.colorSelected(color)
            control.colorChanged(color)
        }
        
        function onPickingFinished() {
            control.picking = false
            control.pickingFinished()
        }
        
        function onPickingCancelled() {
            control.picking = false
        }

        target: typeof ScreenEyedropperManager !== "undefined" ? ScreenEyedropperManager : null
        enabled: control.type === Enums.colorPicker.type_screen
    }

    // Palette and picker popup 调色板与选择器弹层
    PopupWindowCore {
        id: popup
        popupWidth: {
            switch (control.type) {
                case Enums.colorPicker.type_palette: return Enums.colorPickerMetrics.palettePopupWidth
                case Enums.colorPicker.type_picker: return Enums.colorPickerMetrics.pickerPopupWidth
                default: return Enums.colorPickerMetrics.fallbackPopupWidth
            }
        }
        popupHeight: {
            switch (control.type) {
                case Enums.colorPicker.type_palette: return Enums.colorPickerMetrics.palettePopupHeight
                case Enums.colorPicker.type_picker: return Enums.colorPickerMetrics.pickerPopupHeight
                default: return Enums.colorPickerMetrics.fallbackPopupHeight
            }
        }
        
        onClosed: control._isOpen = false
        
        // Palette content 调色板内容
        Loader {
            anchors.fill: parent
            active: control.type === Enums.colorPicker.type_palette && control._isOpen
            sourceComponent: ColorPalette {
                selectedColor: control.selectedColor
                showAutomatic: control.showAutomatic
                showMoreColors: control.showMoreColors
                automaticText: control.automaticText
                themeColorsText: control.themeColorsText
                standardColorsText: control.standardColorsText
                moreColorsText: control.moreColorsText
                enabled: control.enabled
                onColorSelected: (c) => {
                    control.selectedColor = c
                    control.colorSelected(c)
                    control.colorChanged(c)
                    popup.close()
                }
                onMoreColorsClicked: {
                    popup.close()  // Close palette popup first 先关闭调色板弹窗
                    control.moreColorsClicked()
                    control._openPaletteDialog()  // Open ColorDialog 打开颜色对话框
                }
            }
        }
        
        // Picker content 选择器内容
        Loader {
            anchors.fill: parent
            active: control.type === Enums.colorPicker.type_picker && control._isOpen
            sourceComponent: ColorPickerDropdown {
                selectedColor: control.selectedColor
                colorMode: control.colorMode
                enableAlpha: control.enableAlpha
                enabled: control.enabled
                onColorChanged: (c) => {
                    control.selectedColor = c
                    control.colorChanged(c)
                }
                onAccepted: (c) => {
                    control.selectedColor = c
                    control.colorSelected(c)
                    control.accepted(c)
                    popup.close()
                }
                onRejected: {
                    control.selectedColor = control.defaultColor
                    control.rejected()
                    popup.close()
                }
            }
        }
    }

    // Palette color-dialog loader 调色板颜色对话框加载器
    Loader {
        id: paletteDialogLoader
        active: control.type === Enums.colorPicker.type_palette
        sourceComponent: ColorPickerDialog {
            title: { Translator._v; return Translator.tr("custom_color") }
            selectedColor: control.selectedColor
            onColorAccepted: (c) => {
                control.selectedColor = c
                control.colorSelected(c)
            }
        }
    }

    // Modal dialog loader 模态对话框加载器
    Loader {
        id: dialogLoader
        active: control.type === Enums.colorPicker.type_dialog
        sourceComponent: ColorPickerDialog {
            selectedColor: control.selectedColor
            title: control.dialogTitle
            editColorText: control.editColorText
            confirmText: control.confirmText
            cancelText: control.cancelText
            enableAlpha: control.enableAlpha
            enabled: control.enabled
            overlayTarget: control.parent  // Overlay parent component 覆盖父组件
            onColorAccepted: (c) => {
                control.selectedColor = c
                control.colorSelected(c)
                control.accepted(c)
                control._isOpen = false
            }
            onRejected: {
                control.rejected()
                control._isOpen = false
            }
            onColorUpdated: (c) => {
                control.colorChanged(c)
            }
        }
    }
}
