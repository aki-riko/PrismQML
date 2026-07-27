// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import ".."
import "../../icons"

// RatingCore - Star rating component base class 星级评分组件基类（Fluent Design风格）
Item {
    id: control

    property int value: 0
    property int maxValue: 5
    property bool editable: true
    property int starSize: Enums.iconSize.xxl
    property color fillColor: Enums.starColor  // Star fill color 填充星星的颜色
    property color outlineColor: Enums.gray.text  // Outline star color 未填充星星的边框颜色
    property int spacing: Enums.spacing.xxs  // Star spacing 星星间距
    readonly property color _effectiveFillColor: enabled ? fillColor : Enums.textColor.disabled
    readonly property color _effectiveOutlineColor: {
        if (!enabled) return Enums.textColor.disabled
        return outlineColor
    }
    readonly property color _effectiveHoverColor: enabled ? fillColor : Enums.textColor.disabled

    signal ratingChanged(int newValue)
    
    
    // ==================== Public Methods 公开方法 ====================
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
                property bool filled: index < control.value
                property bool hovered: starArea.containsMouse

                width: starSize
                height: starSize
                
                // Star icon 星星图标
                Icon {
                    anchors.centerIn: parent
                    icon: parent.filled ? Enums.icon.star_filled : Enums.icon.star_outline
                    iconSize: starSize
                    color: parent.filled ? control._effectiveFillColor :
                           (parent.hovered ? control._effectiveHoverColor : control._effectiveOutlineColor)
                    
                    scale: parent.hovered ? 1.15 : 1.0
                    Behavior on scale { NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutBack } }
                    Behavior on color { ColorAnimation { duration: Enums.duration.normal } }
                }
                
                MouseArea {
                    id: starArea
                    anchors.fill: parent
                    enabled: control.enabled && control.editable
                    hoverEnabled: true
                    onClicked: { control.value = index + 1; control.ratingChanged(control.value) }
                }
            }
        }
    }
}
