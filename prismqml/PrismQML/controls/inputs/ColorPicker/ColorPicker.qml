// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../.."
import "_internal" as ColorPickerInternal
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
    property bool _dialogRequested: false
    property bool _paletteDialogRequested: false
    property bool _popupContentRequested: false
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
            _dialogRequested = true
            // Set overlay target before opening 打开前设置覆盖目标
            if (contentLayer.dialogLoader.item) {
                contentLayer.dialogLoader.item.overlayTarget = control.parent
                contentLayer.dialogLoader.item.open()
            }
            _isOpen = true
        } else if (type === Enums.colorPicker.type_palette ||
                   type === Enums.colorPicker.type_picker) {
            _popupContentRequested = true
            contentLayer.popup.openAtControl(control)
            _isOpen = true
        }
    }

    function close() {
        if (type === Enums.colorPicker.type_dialog) {
            if (contentLayer.dialogLoader.item) contentLayer.dialogLoader.item.close()
        } else {
            contentLayer.popup.close()
        }
        _isOpen = false
    }

    function _preparePopup() {
        if (type === Enums.colorPicker.type_palette ||
                type === Enums.colorPicker.type_picker) {
            _popupContentRequested = true
            _isOpen = true
        }
    }

    function _prewarmTriggerContent() {
        if (!enabled) return
        if (type === Enums.colorPicker.type_dialog) {
            _dialogRequested = true
        } else if (type === Enums.colorPicker.type_palette ||
                   type === Enums.colorPicker.type_picker) {
            _popupContentRequested = true
        }
    }

    // Open ColorDialog from palette "自定义颜色" button 从调色板"自定义颜色"按钮打开
    function _openPaletteDialog() {
        if (_mainWindow && _mainWindow.contentItem) {
            _paletteDialogRequested = true
            contentLayer.paletteDialogLoader.parent = _mainWindow.contentItem
            contentLayer.paletteDialogLoader.anchors.fill = _mainWindow.contentItem
            if (contentLayer.paletteDialogLoader.item) {
                contentLayer.paletteDialogLoader.item.selectedColor = control.selectedColor
                contentLayer.paletteDialogLoader.item.open()
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
            case Enums.colorPicker.type_circle:
                return contentLayer.circleLoader.item
                    ? contentLayer.circleLoader.item.implicitWidth
                    : Enums.colorPickerMetrics.circleLoaderFallbackWidth
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
    ColorPickerInternal.ColorPickerContent {
        id: contentLayer
        colorControl: control
    }
}
