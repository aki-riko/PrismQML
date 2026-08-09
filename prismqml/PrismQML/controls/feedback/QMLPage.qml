// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../.."
import QtQuick  // Keep native types unprefixed after library import 库导入后保留原生类型无前缀

// QMLPage - Reusable QML loading page with a progress ring 可复用进度环 QML 加载页
Rectangle {
    id: control

    // ==================== Public Props 公开属性 ====================
    property string text: { Translator._v; return Translator.tr("loading") }  // Loading message 加载提示
    property bool running: visible                  // Run animation while loading 加载时运行动画
    property color backgroundColor: Enums.backgroundColor  // Page background 页面背景

    // ==================== Signals 信号 ====================
    signal finished()  // Emitted after the page is removed 页面移除后触发

    // ==================== Public Methods 公开方法 ====================
    function start() {
        control.visible = true
        contentColumn.opacity = Enums.opacityLevel.visible
        contentColumn.scale = Enums.opacityLevel.visible
    }

    function finish() {
        if (!control.visible) return
        control.visible = false
        control.finished()
    }

    color: control.backgroundColor
    clip: true

    // ==================== Content 内容 ====================
    Column {
        id: contentColumn

        objectName: "qmlPageContent"
        anchors.centerIn: parent
        opacity: Enums.opacityLevel.visible
        scale: Enums.opacityLevel.visible
        transformOrigin: Item.Center
        spacing: Enums.spacing.xl

        ProgressRing {
            id: progressRing

            objectName: "qmlPageProgressRing"
            anchors.horizontalCenter: parent.horizontalCenter
            width: Enums.controlSize.navBarHeight
            height: Enums.controlSize.navBarHeight
            indeterminate: control.running
            indeterminateStyle: Enums.progress.indeterminate_style_fixed_arc
            paused: !control.running
            strokeWidth: Enums.controlSize.progressStrokeWidth
            spinDuration: Enums.duration.scroll
            trackColorLight: Enums.transparent
            trackColorDark: Enums.transparent
        }

        Label {
            objectName: "qmlPageLabel"
            anchors.horizontalCenter: parent.horizontalCenter
            text: control.text
            type: Enums.label.type_body
            visible: control.text !== ""
        }
    }
}
