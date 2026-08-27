// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

pragma ComponentBehavior: Bound
import QtQuick
import "../../.."

// LazyPageCpuTransition - CPU drop and circuit expansion for lazy pages
// LazyPageCpuTransition - 懒加载页面 CPU 下落后电路展开过渡
Item {
    id: transition

    // ==================== Public Props 公开属性 ====================
    property int revealDuration: Enums.lazyLoadingTransitionMetrics.revealDuration
    property int coverDuration: Enums.lazyLoadingTransitionMetrics.coverDuration
    property int revealEasing: Easing.OutQuint
    property int coverEasing: Easing.InOutQuad
    property bool revealTarget: false
    property bool keepSourceHiddenOnExpand: false
    property bool collapseToCenter: false
    property bool preferOverlayWindow: false

    // ==================== Readonly State 只读状态 ====================
    readonly property bool running: pageTransition.running
        || dropAnimation.running || circuitAnimation.running
    readonly property bool active: pageTransition.active
        || dropAnimation.running || circuitAnimation.running
    readonly property bool collapsing: _operationCollapsing
    readonly property bool collapsed: _collapsed
    readonly property real progress: pageTransition.progress
    readonly property real revealMinimumRadiusPixels:
        pageTransition.revealMinimumRadiusPixels
    readonly property real revealMaximumRadiusPixels:
        pageTransition.revealMaximumRadiusPixels
    readonly property real revealRadiusPixels: pageTransition.revealRadiusPixels
    readonly property bool _capturePending: pageTransition._capturePending
    readonly property int _overlayFrameStage: pageTransition._overlayFrameStage
    readonly property bool _dissolving: pageTransition._dissolving
    readonly property bool _usingPageLayer: pageTransition._usingPageLayer
    readonly property bool _inWindowStartPending: pageTransition._inWindowStartPending
    readonly property bool _mainFramePending: pageTransition._mainFramePending
    readonly property string _lastFallbackReason: pageTransition._lastFallbackReason

    // ==================== Internal Props 内部属性 ====================
    readonly property QtObject _cpuMetrics: Enums.lazyLoadingTransitionMetrics.cpu
    property bool _operationCollapsing: false
    property bool _collapsed: false
    property bool _visualVisible: false
    property real _circuitProgress: Enums.opacityLevel.invisible
    property bool _collapsePageFinished: false
    property bool _dropFinished: false
    property bool _expandPageFinished: false
    property bool _circuitFinished: false
    readonly property real _chipRestX: (width - _cpuMetrics.chipWidth) / 2
    readonly property real _chipRestY: (height - _cpuMetrics.chipHeight) / 2
    readonly property real _chipStartY: _chipRestY - _cpuMetrics.dropDistance

    // ==================== Signals 信号 ====================
    signal collapseStarted()
    signal expandStarted()
    signal collapseFinished()
    signal expandFinished()

    // ==================== Public Methods 公开方法 ====================
    function collapse(sourceItem) {
        transition.stop()
        transition._operationCollapsing = true
        transition._visualVisible = true
        transition._collapsed = false
        transition._collapsePageFinished = false
        transition._dropFinished = false
        chip.y = transition._chipStartY
        chip.opacity = Enums.opacityLevel.invisible
        chip.scale = transition._cpuMetrics.dropStartScale
        transition._circuitProgress = Enums.opacityLevel.invisible
        dropAnimation.restart()
        return pageTransition.collapse(sourceItem)
    }

    function expand(sourceItem) {
        dropAnimation.stop()
        transition._operationCollapsing = false
        transition._collapsed = false
        transition._visualVisible = true
        transition._expandPageFinished = false
        transition._circuitFinished = false
        chip.x = transition._chipRestX
        chip.y = transition._chipRestY
        chip.opacity = Enums.opacityLevel.visible
        chip.scale = Enums.opacityLevel.visible
        transition._circuitProgress = Enums.opacityLevel.invisible
        circuitAnimation.restart()
        return pageTransition.expand(sourceItem)
    }

    function stop() {
        if (dropAnimation) dropAnimation.stop()
        if (circuitAnimation) circuitAnimation.stop()
        if (pageTransition) pageTransition.stop()
        transition._operationCollapsing = false
        transition._collapsed = false
        transition._visualVisible = false
        transition._collapsePageFinished = false
        transition._dropFinished = false
        transition._expandPageFinished = false
        transition._circuitFinished = false
        transition._circuitProgress = Enums.opacityLevel.invisible
        if (chip) {
            chip.x = transition._chipRestX
            chip.y = transition._chipRestY
            chip.opacity = Enums.opacityLevel.invisible
            chip.scale = Enums.opacityLevel.visible
        }
    }

    function _restoreHostWindowAfterOverlay() {
        if (pageTransition && typeof pageTransition._restoreHostWindowAfterOverlay === "function")
            pageTransition._restoreHostWindowAfterOverlay()
    }

    // ==================== Internal Methods 内部方法 ====================
    function _maybeFinishCollapse() {
        if (!transition._operationCollapsing || !transition._collapsePageFinished
                || !transition._dropFinished || transition._collapsed) return
        transition._collapsed = true
        transition.collapseFinished()
    }

    function _maybeFinishExpand() {
        if (transition._operationCollapsing || !transition._expandPageFinished
                || !transition._circuitFinished) return
        transition._visualVisible = false
        transition.expandFinished()
    }

    anchors.fill: parent
    Component.onDestruction: transition.stop()

    // ==================== Content 内容 ====================
    LazyPageCircleTransition {
        id: pageTransition

        anchors.fill: parent
        revealDuration: transition.revealDuration
        revealEasing: transition.revealEasing
        coverDuration: transition.coverDuration
        coverEasing: transition.coverEasing
        revealTarget: transition.revealTarget
        keepSourceHiddenOnExpand: transition.keepSourceHiddenOnExpand
        collapseToCenter: transition.collapseToCenter
        preferOverlayWindow: transition.preferOverlayWindow
    }

    Item {
        id: cpuVisual

        objectName: "cpuTransitionVisual"
        anchors.fill: parent
        visible: transition._visualVisible
        opacity: Enums.opacityLevel.visible
        z: transition._operationCollapsing
            ? Enums.zIndex.controls : Enums.zIndex.controlsAbove

        Rectangle {
            id: chip

            objectName: "cpuTransitionChip"
            x: transition._chipRestX
            y: transition._chipRestY
            width: transition._cpuMetrics.chipWidth
            height: transition._cpuMetrics.chipHeight
            radius: Enums.radius.small
            color: Enums.cardColor
            border.width: Enums.border.normal
            border.color: Enums.accentColor
            transformOrigin: Item.Center

            Rectangle {
                anchors.centerIn: parent
                width: parent.width - Enums.spacing.l
                height: parent.height - Enums.spacing.l
                radius: Enums.radius.micro
                color: Enums.accentColor
                opacity: Enums.opacityLevel.light
            }

            Text {
                anchors.centerIn: parent
                text: "CPU"
                color: Enums.accentColorLight
                font.family: Enums.fontMonospace
                font.pixelSize: Enums.typography.bodyLarge
                font.bold: true
            }
        }

        Repeater {
            model: transition._cpuMetrics.pinCount
            delegate: Rectangle {
                required property int index

                x: transition._chipRestX + transition._cpuMetrics.pinInset
                    + index * (transition._cpuMetrics.chipWidth
                        - transition._cpuMetrics.pinInset * 2)
                        / Math.max(1, transition._cpuMetrics.pinCount - 1)
                y: chip.y - height
                width: transition._cpuMetrics.pinWidth
                height: transition._cpuMetrics.pinLength
                color: Enums.accentColorLight
                opacity: chip.opacity
            }
        }

        Repeater {
            model: transition._cpuMetrics.pinCount
            delegate: Rectangle {
                required property int index

                x: transition._chipRestX + transition._cpuMetrics.pinInset
                    + index * (transition._cpuMetrics.chipWidth
                        - transition._cpuMetrics.pinInset * 2)
                        / Math.max(1, transition._cpuMetrics.pinCount - 1)
                y: chip.y + chip.height
                width: transition._cpuMetrics.pinWidth
                height: transition._cpuMetrics.pinLength
                color: Enums.accentColorLight
                opacity: chip.opacity
            }
        }

        Repeater {
            model: transition._cpuMetrics.sidePinCount
            delegate: Rectangle {
                required property int index

                x: chip.x - width
                y: chip.y + transition._cpuMetrics.pinInset
                    + index * (transition._cpuMetrics.chipHeight
                        - transition._cpuMetrics.pinInset * 2)
                        / Math.max(1, transition._cpuMetrics.sidePinCount - 1)
                width: transition._cpuMetrics.pinLength
                height: transition._cpuMetrics.pinWidth
                color: Enums.accentColorLight
                opacity: chip.opacity
            }
        }

        Repeater {
            model: transition._cpuMetrics.sidePinCount
            delegate: Rectangle {
                required property int index

                x: chip.x + chip.width
                y: chip.y + transition._cpuMetrics.pinInset
                    + index * (transition._cpuMetrics.chipHeight
                        - transition._cpuMetrics.pinInset * 2)
                        / Math.max(1, transition._cpuMetrics.sidePinCount - 1)
                width: transition._cpuMetrics.pinLength
                height: transition._cpuMetrics.pinWidth
                color: Enums.accentColorLight
                opacity: chip.opacity
            }
        }

        Rectangle {
            id: topTrace

            x: transition._chipRestX + transition._cpuMetrics.chipWidth / 2
                - width / 2
            y: chip.y - transition._cpuMetrics.pinLength - height
            width: Math.max(
                transition._cpuMetrics.traceWidth,
                transition._circuitProgress * transition._cpuMetrics.traceLength)
            height: transition._cpuMetrics.traceWidth
            color: Enums.accentColorLight
            opacity: transition._circuitProgress
        }

        Rectangle {
            id: bottomTrace

            x: transition._chipRestX + transition._cpuMetrics.chipWidth / 2
                - width / 2
            y: chip.y + chip.height + transition._cpuMetrics.pinLength
            width: Math.max(
                transition._cpuMetrics.traceWidth,
                transition._circuitProgress * transition._cpuMetrics.traceLength)
            height: transition._cpuMetrics.traceWidth
            color: Enums.accentColorLight
            opacity: transition._circuitProgress
        }

        Rectangle {
            id: leftTrace

            x: chip.x - transition._cpuMetrics.pinLength - width
            y: transition._chipRestY + transition._cpuMetrics.chipHeight / 2
                - height / 2
            width: transition._cpuMetrics.traceWidth
            height: Math.max(
                transition._cpuMetrics.traceWidth,
                transition._circuitProgress * transition._cpuMetrics.traceLength)
            color: Enums.accentColorLight
            opacity: transition._circuitProgress
        }

        Rectangle {
            id: rightTrace

            x: chip.x + chip.width + transition._cpuMetrics.pinLength
            y: transition._chipRestY + transition._cpuMetrics.chipHeight / 2
                - height / 2
            width: transition._cpuMetrics.traceWidth
            height: Math.max(
                transition._cpuMetrics.traceWidth,
                transition._circuitProgress * transition._cpuMetrics.traceLength)
            color: Enums.accentColorLight
            opacity: transition._circuitProgress
        }

        Repeater {
            model: transition._cpuMetrics.traceNodeCount
            delegate: Rectangle {
                required property int index
                readonly property bool verticalNode: index >= 2

                width: transition._cpuMetrics.traceNodeSize
                height: width
                radius: width / 2
                color: Enums.accentColor
                opacity: transition._circuitProgress
                x: verticalNode
                    ? (index === 2 ? leftTrace.x - width / 2
                                   : rightTrace.x - width / 2)
                    : transition._chipRestX + transition._cpuMetrics.chipWidth / 2
                        - width / 2
                y: verticalNode
                    ? transition._chipRestY + transition._cpuMetrics.chipHeight / 2
                        - height / 2
                    : (index === 0
                        ? topTrace.y - height / 2 : bottomTrace.y - height / 2)
            }
        }
    }

    ParallelAnimation {
        id: dropAnimation

        onFinished: {
            transition._dropFinished = true
            transition._maybeFinishCollapse()
        }

        NumberAnimation {
            target: chip
            property: "y"
            from: transition._chipStartY
            to: transition._chipRestY
            duration: transition.coverDuration
            easing.type: Easing.OutBack
        }

        NumberAnimation {
            target: chip
            property: "opacity"
            from: Enums.opacityLevel.invisible
            to: Enums.opacityLevel.visible
            duration: transition.coverDuration
            easing.type: Easing.OutCubic
        }

        NumberAnimation {
            target: chip
            property: "scale"
            from: transition._cpuMetrics.dropStartScale
            to: Enums.opacityLevel.visible
            duration: transition.coverDuration
            easing.type: Easing.OutBack
        }

    }

    ParallelAnimation {
        id: circuitAnimation

        onFinished: {
            transition._circuitFinished = true
            transition._maybeFinishExpand()
        }

        NumberAnimation {
            target: transition
            property: "_circuitProgress"
            from: Enums.opacityLevel.invisible
            to: Enums.opacityLevel.visible
            duration: transition.revealDuration
            easing.type: Easing.OutCubic
        }

        SequentialAnimation {
            PauseAnimation {
                duration: transition.revealDuration
                    * transition._cpuMetrics.circuitPauseRatio
            }
            NumberAnimation {
                target: chip
                property: "scale"
                from: Enums.opacityLevel.visible
                to: Enums.opacityLevel.strong
                duration: transition.revealDuration
                    * transition._cpuMetrics.circuitPulseInRatio
                easing.type: Easing.OutCubic
            }
            NumberAnimation {
                target: chip
                property: "scale"
                from: Enums.opacityLevel.strong
                to: Enums.opacityLevel.visible
                duration: transition.revealDuration
                    * transition._cpuMetrics.circuitPulseOutRatio
                easing.type: Easing.InOutSine
            }
        }

    }

    Connections {
        function onCollapseStarted() { transition.collapseStarted() }
        function onExpandStarted() { transition.expandStarted() }
        function onCollapseFinished() {
            transition._collapsePageFinished = true
            transition._maybeFinishCollapse()
        }
        function onExpandFinished() {
            transition._expandPageFinished = true
            transition._maybeFinishExpand()
        }

        target: pageTransition
    }
}
