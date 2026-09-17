// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../icons"
import "../../../data"

// ColorPalette - Theme colors + Standard colors grid 主题色+标准色网格
// Layout: Automatic option + Theme Colors (10x6) + Standard Colors (10x1) + More Colors
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property color selectedColor: Enums.accentColor
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
    
    // Theme colors (10 columns x 6 rows) 主题色
    property var themeColors: Enums.colorPalette.themeColors
    
    // Standard colors (10 colors) 标准色
    property var standardColors: Enums.colorPalette.standardColors

    property int cellSize: Enums.colorPickerMetrics.paletteCellSize
    property int cellSpacing: Enums.colorPickerMetrics.paletteCellSpacing
    property int columns: Enums.colorPickerMetrics.paletteColumns

    // ==================== Readonly State 只读状态 ====================
    readonly property var _safeThemeColors: _colorsOrEmpty(themeColors)
    readonly property var _safeStandardColors: _colorsOrEmpty(standardColors)
    
    // ==================== Signals 信号 ====================
    signal colorSelected(color value)
    signal moreColorsClicked()
    signal moreColorsPrewarmRequested()

    // ==================== Internal Methods 内部方法 ====================
    function _colorsOrEmpty(value) {
        if (!value || typeof value.length !== "number") return []
        var result = []
        for (var i = 0; i < value.length; i++) {
            if (value[i] !== null && value[i] !== undefined) result.push(value[i])
        }
        return result
    }
    
    // ==================== Size 尺寸 ====================
    implicitWidth: columns * (cellSize + cellSpacing) + Enums.spacing.xl * 2
    implicitHeight: contentColumn.implicitHeight + Enums.spacing.l * 2
    
    // ==================== Content 内容 ====================
    Column {
        id: contentColumn
        anchors.fill: parent
        anchors.margins: Enums.spacing.l
        spacing: Enums.spacing.m
        
        // Automatic option 自动选项
        Rectangle {
            // Touch has no hover preview: on touch the hover treatment follows the press
            // 触摸没有 hover 预览: 触摸端 hover 视觉只在按压时生效, 避免松手后残留
            readonly property bool _touchActive: Touch.feedback(autoArea.containsMouse, autoArea.pressed)

            visible: control.showAutomatic
            width: parent.width
            height: Enums.controlSize.inputHeight
            color: _touchActive ? Enums.stateColor.controlBgHover : Enums.transparent
            radius: Enums.radius.small
            
            Row {
                anchors.fill: parent
                anchors.leftMargin: Enums.spacing.m
                spacing: Enums.spacing.m
                
                // Color preview 颜色预览
                Rectangle {
                    width: Enums.colorPickerMetrics.palettePreviewSize
                    height: Enums.colorPickerMetrics.palettePreviewSize
                    radius: Enums.radius.small
                    color: Enums.colorPalette.automaticColor
                    border.width: Enums.border.thin
                    border.color: Enums.stateColor.border
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Label {
                    type: Enums.label.type_body
                    text: control.automaticText
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            
            MouseArea {
                id: autoArea
                anchors.fill: parent
                hoverEnabled: true
                enabled: control.enabled
                onClicked: {
                    control.selectedColor = Enums.colorPalette.automaticColor
                    control.colorSelected(Enums.colorPalette.automaticColor)
                }
            }
        }
        
        // Theme Colors section 主题色区域
        Column {
            width: parent.width
            spacing: Enums.spacing.s
            
            Label {
                type: Enums.label.type_caption
                text: control.themeColorsText
                color: Enums.accentColor
            }
            
            Grid {
                columns: control.columns
                spacing: control.cellSpacing
                
                Repeater {
                    model: control._safeThemeColors
                    
                    Rectangle {
                        // Touch has no hover preview: on touch the hover treatment follows the press
                        // 触摸没有 hover 预览: 触摸端 hover 视觉只在按压时生效, 避免松手后残留
                        readonly property bool _touchActive: Touch.feedback(cellArea.containsMouse,
                                                                           cellArea.pressed)

                        width: control.cellSize
                        height: control.cellSize
                        color: modelData || Enums.transparent
                        radius: Enums.radius.tiny
                        border.width: {
                            if (control.selectedColor.toString().toUpperCase() === String(modelData).toUpperCase()) return Enums.colorPickerMetrics.paletteSelectedBorderWidth
                            return _touchActive ? Enums.border.thin : Enums.border.none
                        }
                        border.color: {
                            if (control.selectedColor.toString().toUpperCase() === String(modelData).toUpperCase())
                                return Enums.accentColor
                            return Enums.stateColor.border
                        }
                        
                        MouseArea {
                            id: cellArea
                            anchors.fill: parent
                            hoverEnabled: true
                            enabled: control.enabled
                            onClicked: {
                                control.selectedColor = modelData
                                control.colorSelected(modelData)
                            }
                        }
                    }
                }
            }
        }
        
        // Standard Colors section 标准色区域
        Column {
            width: parent.width
            spacing: Enums.spacing.s
            
            Label {
                type: Enums.label.type_caption
                text: control.standardColorsText
                color: Enums.accentColor
            }
            
            Row {
                spacing: control.cellSpacing
                
                Repeater {
                    model: control._safeStandardColors
                    
                    Rectangle {
                        // Touch has no hover preview: on touch the hover treatment follows the press
                        // 触摸没有 hover 预览: 触摸端 hover 视觉只在按压时生效, 避免松手后残留
                        readonly property bool _touchActive: Touch.feedback(stdArea.containsMouse,
                                                                           stdArea.pressed)

                        width: control.cellSize
                        height: control.cellSize
                        color: modelData || Enums.transparent
                        radius: Enums.radius.tiny
                        border.width: {
                            if (control.selectedColor.toString().toUpperCase() === String(modelData).toUpperCase()) return Enums.colorPickerMetrics.paletteSelectedBorderWidth
                            return _touchActive ? Enums.border.thin : Enums.border.none
                        }
                        border.color: {
                            if (control.selectedColor.toString().toUpperCase() === String(modelData).toUpperCase())
                                return Enums.accentColor
                            return Enums.stateColor.border
                        }
                        
                        MouseArea {
                            id: stdArea
                            anchors.fill: parent
                            hoverEnabled: true
                            enabled: control.enabled
                            onClicked: {
                                control.selectedColor = modelData
                                control.colorSelected(modelData)
                            }
                        }
                    }
                }
            }
        }
        
        // More Colors option 更多颜色选项
        Rectangle {
            // Touch has no hover preview: on touch the hover treatment follows the press
            // 触摸没有 hover 预览: 触摸端 hover 视觉只在按压时生效, 避免松手后残留
            readonly property bool _touchActive: Touch.feedback(moreArea.containsMouse, moreArea.pressed)

            visible: control.showMoreColors
            width: parent.width
            height: Enums.controlSize.inputHeight
            color: _touchActive ? Enums.stateColor.controlBgHover : Enums.transparent
            radius: Enums.radius.small
            
            Row {
                anchors.fill: parent
                anchors.leftMargin: Enums.spacing.m
                spacing: Enums.spacing.m
                
                Icon {
                    icon: Enums.icon.color
                    iconSize: Enums.iconSize.s
                    color: Enums.textColor.primary
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Label {
                    type: Enums.label.type_body
                    text: control.moreColorsText
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            
            MouseArea {
                id: moreArea
                anchors.fill: parent
                hoverEnabled: true
                enabled: control.enabled
                onContainsMouseChanged: {
                    if (containsMouse) control.moreColorsPrewarmRequested()
                }
                onClicked: control.moreColorsClicked()
            }
        }
    }
}
