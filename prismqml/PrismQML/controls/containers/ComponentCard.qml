// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."
import "../data/Label"

// ComponentCard - Component demo wrapper 组件演示包装
// Displays a component with its label below 显示组件及其下方标签
Column {
    id: control
    
    property string label: ""  // Label text (e.g. enum name) 标签文本
    default property alias content: contentItem.children
    
    spacing: Enums.spacing.xs
    
    // Content container 内容容器
    Item {
        id: contentItem
        objectName: "contentItem"
        // Use childrenRect for auto-sizing 使用childrenRect自动计算尺寸
        implicitWidth: childrenRect.width > 0 ? childrenRect.width : 80
        implicitHeight: childrenRect.height > 0 ? childrenRect.height : 32
        width: implicitWidth
        height: implicitHeight
    }
    
    // Label 标签
    Label {
        type: Enums.label.type_caption
        width: Math.max(contentItem.width, implicitWidth)
        text: control.label
        color: Enums.accentColor
        visible: control.label !== ""
        horizontalAlignment: Text.AlignHCenter  // Center text 文本居中
    }
}
