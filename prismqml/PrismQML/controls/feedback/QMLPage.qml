// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../.."
import QtQuick  // Keep native types unprefixed after library import 库导入后保留原生类型无前缀

// QMLPage - Reusable loading page with reversible ripple transitions 可复用双向涟漪过渡的 QML 加载页
Rectangle {
    id: control

    // ==================== Public Props 公开属性 ====================
    property string text: { Translator._v; return Translator.tr("loading") }  // Loading message 加载提示
    property bool running: visible                  // Run animation while loading 加载时运行动画
    property color backgroundColor: Enums.backgroundColor  // Page background 页面背景
    property color exitBackgroundColor: backgroundColor  // Exit ripple backdrop 退场涟漪背板
    property real transitionBackgroundOpacity: Enums.opacityLevel.strong  // Transition transparency 过渡透明度

    // ==================== Internal Props 内部属性 ====================
    readonly property bool entering: _entering       // Entrance is running 正在入场
    readonly property bool finishing: _finishing     // Exit is running 正在退场
    readonly property color _transitionBackgroundColor: Qt.rgba(
        exitBackgroundColor.r,
        exitBackgroundColor.g,
        exitBackgroundColor.b,
        exitBackgroundColor.a * Math.max(0, Math.min(1, transitionBackgroundOpacity))
    )
    property bool _entering: false
    property bool _finishing: false
    property bool _exitPrepared: false
    property bool _finishRequested: false
    property bool _transitionOpaque: false
    property int _transitionPhase: 0

    // ==================== Signals 信号 ====================
    signal entered()   // Emitted after the loading page covers the old page 加载页覆盖旧页后触发
    signal finished()  // Emitted after the page is removed 页面移除后触发

    // ==================== Public Methods 公开方法 ====================
    function start() {
        if (exitLoader.item && exitLoader.item.stop) exitLoader.item.stop()
        control._entering = true
        control._finishing = false
        control._finishRequested = false
        control._transitionOpaque = false
        control._transitionPhase = 1
        control.visible = true
        contentColumn.opacity = Enums.opacityLevel.invisible
        contentColumn.scale = Enums.opacityLevel.visible
        control.prepareFinish()
        control._startTransitionAnimation()
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
        if (control._entering) {
            control._finishRequested = true
            return
        }
        control.prepareFinish()
        control._beginExitAnimation()
    }

    // ==================== Internal Methods 内部方法 ====================
    function _beginExitAnimation() {
        control._transitionPhase = 2
        control._transitionOpaque = true
        contentColumn.opacity = Enums.opacityLevel.visible
        control._startTransitionAnimation()
    }

    function _startTransitionAnimation() {
        if (control._transitionPhase === 0 || !exitLoader.item) return
        control._transitionOpaque = true
        contentColumn.opacity = Enums.opacityLevel.visible
        exitLoader.item.sourceItem = control
        exitLoader.item.reverse = control._transitionPhase === 1
        exitLoader.item.start()
    }

    function _completeEnterAnimation() {
        control._transitionPhase = 0
        control._entering = false
        control.entered()
        if (!control._finishRequested) return
        control._finishRequested = false
        control._beginExitAnimation()
    }

    function _completeExitAnimation() {
        control.visible = false
        control.finished()
        control._entering = false
        control._finishing = false
        control._exitPrepared = false
        control._finishRequested = false
        control._transitionOpaque = false
        control._transitionPhase = 0
    }

    function _completeTransitionWithoutEffect() {
        if (control._transitionPhase === 1) {
            control._transitionOpaque = true
            contentColumn.opacity = Enums.opacityLevel.visible
            control._completeEnterAnimation()
            return
        }
        if (control._transitionPhase === 2) control._completeExitAnimation()
    }

    color: control._transitionOpaque
        ? control._transitionBackgroundColor : control.backgroundColor
    clip: true

    onVisibleChanged: {
        if (!visible && !control._finishing) {
            if (exitLoader.item && exitLoader.item.stop) exitLoader.item.stop()
            control._entering = false
            control._exitPrepared = false
            control._finishRequested = false
            control._transitionOpaque = false
            control._transitionPhase = 0
        }
    }

    // Lazy exit effect loader 懒加载退场效果
    Loader {
        id: exitLoader

        objectName: "qmlPageExitLoader"
        anchors.fill: parent
        active: control._exitPrepared
        asynchronous: true

        onLoaded: control._startTransitionAnimation()
        onStatusChanged: {
            if (status !== Loader.Error) return
            console.error("QMLPage: ripple transition failed to load")
            control._completeTransitionWithoutEffect()
        }
    }

    Connections {
        function onFinished() {
            if (control._transitionPhase === 1) {
                control._completeEnterAnimation()
                return
            }
            if (control._transitionPhase === 2) control._completeExitAnimation()
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
