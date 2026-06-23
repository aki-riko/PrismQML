// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../data"

// ChartTitle - Chart title and subtitle component 图表标题组件
// Unified title styling for all chart types 统一的标题样式，适用于所有图表类型

Column {
    id: root
    
    // ==================== Props 属性 ====================
    property string title: ""
    property string subtitle: ""
    
    // ==================== Layout 布局 ====================
    spacing: Enums.spacing.xxs
    visible: root.title !== ""
    
    Label {
        anchors.horizontalCenter: parent.horizontalCenter
        type: Enums.label.type_subtitle
        text: root.title
    }
    
    Label {
        anchors.horizontalCenter: parent.horizontalCenter
        type: Enums.label.type_caption
        text: root.subtitle
        color: Enums.textColor.tertiary
        visible: root.subtitle !== ""
    }
}
