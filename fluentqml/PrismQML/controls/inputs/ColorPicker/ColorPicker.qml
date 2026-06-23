// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import "../../.."
import "_internal"
import "../../utils"
import "../../buttons/Button"
import "../../icons"
import QtQuick.Window  // 置于库import后:原生Window名归库后不被覆盖
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// ColorPicker - Unified color picker component 统一颜色选择器组件
// Control via type property 通过type属性控制类型
// Types: dialog/palette/picker/circle/screen
Item {
    id: control
    
    // ==================== Type Props 类型属性 ====================
    property int type: Enums.colorPicker.type_picker
    property int colorMode: Enums.colorPicker.mode_rgb
    
    // ==================== Content Props 内容属性 ====================
    property color selectedColor: Enums.colorPickerDefaults.defaultColor
    property color defaultColor: Enums.colorPickerDefaults.defaultColor
    property bool enableAlpha: true
    
    // ==================== Circle Type Props 圆形类型属性 ====================
    property var circleColors: Enums.colorPickerDefaults.quickPalette
    property int circleSize: 28
    
    // ==================== Dialog Type Props 对话框类型属性 ====================
    property string dialogTitle: qsTr("选择背景颜色")
    property string editColorText: qsTr("编辑颜色")
    property string confirmText: qsTr("确定")
    property string cancelText: qsTr("取消")
    
    // ==================== Palette Type Props 调色板类型属性 ====================
    property bool showAutomatic: true
    property bool showMoreColors: true
    property string automaticText: qsTr("默认")
    property string themeColorsText: qsTr("主题色")
    property string standardColorsText: qsTr("标准色")
    property string moreColorsText: qsTr("自定义颜色")
    
    // ==================== Screen Type Props 屏幕取色类型属性 ====================
    property bool picking: false
    
    // ==================== State 状态 ====================
    property bool _isOpen: false
    readonly property bool popupVisible: _isOpen
    property var _mainWindow: Window.window  // Main window reference for ColorDialog 主窗口引用
    
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
            case Enums.colorPicker.type_circle: return circleLoader.item ? circleLoader.item.implicitWidth : circleLoader.item.implicitWidth
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
    
    // ==================== Trigger Button (for dropdown types) 触发按钮 ====================
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
    
    // ==================== Circle Colors (for circle type) 圆形颜色 ====================
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
    
    // ==================== Screen Picker (for screen type) 屏幕取色器 ====================
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
    
    // ==================== Screen Picker Connections 屏幕取色器连接 ====================
    Connections {
        target: typeof ScreenEyedropperManager !== "undefined" ? ScreenEyedropperManager : null
        enabled: control.type === Enums.colorPicker.type_screen
        
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
    }
    
    // ==================== Popup for palette/picker 调色板/选择器弹出层 ====================
    PopupWindowCore {
        id: popup
        popupWidth: {
            switch (control.type) {
                case Enums.colorPicker.type_palette: return 360
                case Enums.colorPicker.type_picker: return 320
                default: return 300
            }
        }
        popupHeight: {
            switch (control.type) {
                case Enums.colorPicker.type_palette: return 370
                case Enums.colorPicker.type_picker: return 480
                default: return 400
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

    // ==================== Palette ColorDialog Loader 调色板颜色对话框加载器 ====================
    Loader {
        id: paletteDialogLoader
        active: control.type === Enums.colorPicker.type_palette
        sourceComponent: ColorPickerDialog {
            title: qsTr("自定义颜色")
            selectedColor: control.selectedColor
            onColorAccepted: (c) => {
                control.selectedColor = c
                control.colorSelected(c)
            }
        }
    }
    
    // ==================== Modal Dialog Loader 模态对话框加载器 ====================
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
