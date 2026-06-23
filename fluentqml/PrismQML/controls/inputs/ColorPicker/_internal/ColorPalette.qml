// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../icons"
import "../../../data"

// ColorPalette - Theme colors + Standard colors grid 主题色+标准色网格
// Layout: Automatic option + Theme Colors (10x6) + Standard Colors (10x1) + More Colors
Item {
    id: control
    
    // ==================== Properties 属性 ====================
    property color selectedColor: Enums.accentColor
    property bool showAutomatic: true
    property bool showMoreColors: true
    property string automaticText: "Automatic"
    property string themeColorsText: "Theme Colors"
    property string standardColorsText: "Standard Colors"
    property string moreColorsText: "More Colors..."
    
    // Theme colors (10 columns x 6 rows) 主题色
    property var themeColors: Enums.colorPalette.themeColors
    
    // Standard colors (10 colors) 标准色
    property var standardColors: Enums.colorPalette.standardColors
    
    // ==================== Signals 信号 ====================
    signal colorSelected(color value)
    signal moreColorsClicked()
    
    // ==================== Size 尺寸 ====================
    property int cellSize: Enums.colorPickerMetrics.paletteCellSize
    property int cellSpacing: Enums.colorPickerMetrics.paletteCellSpacing
    property int columns: Enums.colorPickerMetrics.paletteColumns
    
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
            visible: control.showAutomatic
            width: parent.width
            height: Enums.controlSize.inputHeight
            color: autoArea.containsMouse ? Enums.stateColor.controlBgHover : Enums.transparent
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
                    model: control.themeColors
                    
                    Rectangle {
                        width: control.cellSize
                        height: control.cellSize
                        color: modelData
                        radius: Enums.radius.tiny
                        border.width: {
                            if (control.selectedColor.toString().toUpperCase() === modelData.toUpperCase()) return Enums.colorPickerMetrics.paletteSelectedBorderWidth
                            return cellArea.containsMouse ? Enums.border.thin : Enums.border.none
                        }
                        border.color: {
                            if (control.selectedColor.toString().toUpperCase() === modelData.toUpperCase()) 
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
                    model: control.standardColors
                    
                    Rectangle {
                        width: control.cellSize
                        height: control.cellSize
                        color: modelData
                        radius: Enums.radius.tiny
                        border.width: {
                            if (control.selectedColor.toString().toUpperCase() === modelData.toUpperCase()) return Enums.colorPickerMetrics.paletteSelectedBorderWidth
                            return stdArea.containsMouse ? Enums.border.thin : Enums.border.none
                        }
                        border.color: {
                            if (control.selectedColor.toString().toUpperCase() === modelData.toUpperCase()) 
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
            visible: control.showMoreColors
            width: parent.width
            height: Enums.controlSize.inputHeight
            color: moreArea.containsMouse ? Enums.stateColor.controlBgHover : Enums.transparent
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
                onClicked: control.moreColorsClicked()
            }
        }
    }
}
