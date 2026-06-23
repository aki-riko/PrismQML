// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import ".."

// ToolBar - Pure QtQuick implementation 工具栏纯QtQuick实现
// Simple horizontal toolbar 简单水平工具栏
Rectangle {
    id: control
    
    // Content area 内容区域
    default property alias content: contentRow.data
    property int spacing: Enums.spacing.xs
    property int padding: Enums.spacing.m
    
    // Size 尺寸
    implicitWidth: contentRow.implicitWidth + padding * 2
    implicitHeight: Enums.controlSize.navBarHeight
    
    color: Enums.cardColor
    
    Row {
        id: contentRow
        anchors.left: parent.left
        anchors.leftMargin: control.padding
        anchors.verticalCenter: parent.verticalCenter
        spacing: control.spacing
    }
    
    // Bottom separator 底部分隔线
    Separator {
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        lineColor: Enums.stateColor.inputBorder
    }
}
