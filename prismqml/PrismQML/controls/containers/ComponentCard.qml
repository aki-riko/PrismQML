// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "../data/Label"

// ComponentCard - Component demo wrapper 组件演示包装
// Displays a component with its label below 显示组件及其下方标签
Column {
    id: control
    
    property string label: ""  // Label text (e.g. enum name) 标签文本
    default property alias content: contentHost.children
    readonly property int _contentWidth: contentHost.childrenRect.width > 0 ? contentHost.childrenRect.width : Enums.controlSize.buttonMinWidth
    readonly property int _contentHeight: contentHost.childrenRect.height > 0 ? contentHost.childrenRect.height : Enums.controlSize.buttonHeight
    readonly property int _labelWidth: labelItem.visible ? labelItem.implicitWidth : 0
    readonly property int _prismWidth: Math.max(_contentWidth, Enums.controlSize.buttonMinWidth)
    readonly property int _effectiveWidth: Enums.isPrismDesign ? _prismWidth : Math.max(_contentWidth, _labelWidth)
    
    width: _effectiveWidth
    spacing: Enums.spacing.xs
    
    // Content container 内容容器
    Item {
        id: contentItem
        objectName: "contentItem"
        width: control._effectiveWidth
        height: control._contentHeight

        Item {
            id: contentHost
            objectName: "contentHost"
            width: control._contentWidth
            height: control._contentHeight
            anchors.horizontalCenter: parent.horizontalCenter
        }
    }
    
    // Label 标签
    Label {
        id: labelItem
        type: Enums.label.type_caption
        width: control._effectiveWidth
        text: control.label
        color: Enums.isPrismDesign ? Enums.textColor.tertiary : Enums.accentColor
        visible: control.label !== ""
        maximumLineCount: 1
        elide: Enums.isPrismDesign ? Text.ElideRight : Text.ElideNone
        horizontalAlignment: Text.AlignLeft  // Left-align text 文本左对齐
    }
}
