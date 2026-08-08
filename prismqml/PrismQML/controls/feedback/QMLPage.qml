// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../.."
import QtQuick  // Keep native types unprefixed after library import 库导入后保留原生类型无前缀

// QMLPage - Reusable QML loading page with close ripple exit 可复用关闭涟漪退场的 QML 加载页
Rectangle {
    id: control

    // ==================== Public Props 公开属性 ====================
    property string text: { Translator._v; return Translator.tr("loading") }  // Loading message 加载提示
    property bool running: visible                  // Run animation while loading 加载时运行动画
    property color backgroundColor: Enums.backgroundColor  // Page background 页面背景
    property color exitBackgroundColor: backgroundColor  // Exit ripple backdrop 退场涟漪背板

    // ==================== Internal Props 内部属性 ====================
    readonly property bool finishing: _finishing     // Exit is running 正在退场
    property bool _finishing: false
    property bool _exitPrepared: false
    property bool _exitStartPending: false
    property bool _exitAnimating: false

    // ==================== Signals 信号 ====================
    signal finished()  // Emitted after the page is removed 页面移除后触发

    // ==================== Public Methods 公开方法 ====================
    function start() {
        control._finishing = false
        control._exitPrepared = false
        control._exitStartPending = false
        control._exitAnimating = false
        control.visible = true
        contentColumn.opacity = Enums.opacityLevel.visible
        contentColumn.scale = Enums.opacityLevel.visible
    }

    function prepareFinish() {
        if (!control.visible) return
        if (String(exitLoader.source) === "") {
            exitLoader.setSource(
                Qt.resolvedUrl("_internal/QMLPageExitDissolve.qml"),
                {
                    "sourceItem": control
                }
            )
        }
        control._exitPrepared = true
    }

    function finish() {
        if (control._finishing || !control.visible) return
        control._finishing = true
        control._exitStartPending = true
        control.prepareFinish()
        control._startExitAnimation()
    }

    // ==================== Internal Methods 内部方法 ====================
    function _startExitAnimation() {
        if (!control._exitStartPending || !exitLoader.item) return
        control._exitStartPending = false
        control._exitAnimating = true
        exitLoader.item.sourceItem = control
        exitLoader.item.start()
    }

    function _completeExitAnimation() {
        control.visible = false
        control.finished()
        control._finishing = false
        control._exitPrepared = false
        control._exitStartPending = false
        control._exitAnimating = false
    }

    color: control._exitAnimating ? control.exitBackgroundColor : Enums.transparent
    clip: true

    onVisibleChanged: {
        if (!visible && !control._finishing) {
            control._exitPrepared = false
            control._exitStartPending = false
            control._exitAnimating = false
        }
    }

    // Lazy exit effect loader 懒加载退场效果
    Loader {
        id: exitLoader

        objectName: "qmlPageExitLoader"
        anchors.fill: parent
        active: control._exitPrepared
        asynchronous: true

        onLoaded: control._startExitAnimation()
    }

    Connections {
        function onFinished() {
            control._completeExitAnimation()
        }

        target: exitLoader.item
        ignoreUnknownSignals: true
    }

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
