// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import ".."
import "../../data/Label"

// RatingCore - Star rating component base class 星级评分组件基类（Fluent Design风格）
Item {
    id: control

    property int value: 0
    property int maxValue: 5
    property bool editable: true
    property int starSize: Enums.typography.display
    property color fillColor: Enums.starColor  // Star fill color 填充星星的颜色
    property color outlineColor: Enums.gray.text  // Outline star color 未填充星星的边框颜色
    property int spacing: Enums.spacing.xxs  // Star spacing 星星间距

    signal ratingChanged(int newValue)
    
    
    // ==================== Public Methods 公共方法 ====================
    // Set value 设置评分值
    function setValue(v) { value = Math.max(0, Math.min(maxValue, v)) }
    function getValue() { return value }
    
    
    implicitWidth: row.implicitWidth
    implicitHeight: starSize
    
    Row {
        id: row
        spacing: control.spacing
        
        Repeater {
            model: maxValue
            
            // Fluent style star Fluent风格星星
            Item {
                width: starSize
                height: starSize
                
                property bool filled: index < control.value
                property bool hovered: starArea.containsMouse
                
                // Star text (using Segoe Fluent Icons font) 星星文字
                Text {
                    anchors.centerIn: parent
                    text: parent.filled ? "\uE735" : "\uE734"  // FavoriteStar filled/outline
                    font.family: "Segoe Fluent Icons"
                    font.pixelSize: starSize
                    color: parent.filled ? control.fillColor : 
                           (parent.hovered ? control.fillColor : control.outlineColor)
                    
                    scale: parent.hovered ? 1.15 : 1.0
                    Behavior on scale { NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutBack } }
                    Behavior on color { ColorAnimation { duration: Enums.duration.normal } }
                }
                
                MouseArea {
                    id: starArea
                    anchors.fill: parent
                    enabled: control.editable
                    hoverEnabled: true
                    onClicked: { control.value = index + 1; control.ratingChanged(control.value) }
                }
            }
        }
    }
}
