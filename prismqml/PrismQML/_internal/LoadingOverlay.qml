// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."
import "../controls/data/Label"

// LoadingOverlay - Reusable loading spinner overlay 可复用的加载动画覆盖层
// Extracted from Window*/WindowsBar/WindowsFilled 从三个窗口组件中提取
Rectangle {
    id: root
    
    property bool loading: false
    property string text: Translator.tr("loading")
    property color backgroundColor: Enums.backgroundColor

    color: backgroundColor
    visible: loading
    z: Enums.zIndex.popup
    
    Column {
        anchors.centerIn: parent
        spacing: Enums.spacing.xl
        
        ProgressRing {
            width: Enums.controlSize.navBarHeight
            height: Enums.controlSize.navBarHeight
            anchors.horizontalCenter: parent.horizontalCenter
            indeterminate: root.loading
            indeterminateStyle: Enums.progress.indeterminate_style_fixed_arc
            strokeWidth: Enums.controlSize.progressStrokeWidth
            spinDuration: Enums.duration.scroll
            trackColorLight: Enums.transparent
            trackColorDark: Enums.transparent
        }
        
        Label {
            type: Enums.label.type_body
            text: root.text
            anchors.horizontalCenter: parent.horizontalCenter
        }
    }
}
