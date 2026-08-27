// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

pragma ComponentBehavior: Bound
import QtQuick
import "../../../effects"
import "../../.."

// LazyPageCpuTransition - Outline CPU and circuit reveal for lazy pages
// LazyPageCpuTransition - 懒加载页面描边 CPU 与电路辐射揭幕
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
    readonly property bool running: dropAnimation.running || circuitAnimation.running
    readonly property bool active: _visualVisible || running
    readonly property bool collapsing: _operationCollapsing
    readonly property bool collapsed: _collapsed
    readonly property real progress: _progress
    // CPU mode has no circular radius; these properties remain for the public facade contract.
    // CPU 模式没有圆形半径；保留这些属性以满足公开门面合同。
    readonly property real revealMinimumRadiusPixels: 0
    readonly property real revealMaximumRadiusPixels: 0
    readonly property real revealRadiusPixels: 0
    readonly property bool _capturePending: false
    readonly property int _overlayFrameStage: 0
    readonly property bool _dissolving: false
    readonly property bool _usingPageLayer: false
    readonly property bool _inWindowStartPending: false
    readonly property bool _mainFramePending: false
    readonly property string _lastFallbackReason: ""

    // ==================== Internal Props 内部属性 ====================
    readonly property QtObject _cpuMetrics: Enums.lazyLoadingTransitionMetrics.cpu
    property bool _operationCollapsing: false
    property bool _collapsed: false
    property bool _visualVisible: false
    property real _progress: Enums.opacityLevel.invisible
    property real _circuitProgress: Enums.opacityLevel.invisible
    property Item _sourceItem: null
    property bool _savedSourceVisible: false
    readonly property real _chipRestX: (width - _cpuMetrics.chipWidth) / 2
    readonly property real _chipRestY: (height - _cpuMetrics.chipHeight) / 2
    readonly property real _chipStartY: _chipRestY - _cpuMetrics.dropDistance
    readonly property real _horizontalReach: Math.max(
        0, (width - _cpuMetrics.chipWidth) / 2 - _cpuMetrics.pinLength)
    readonly property real _verticalReach: Math.max(
        0, (height - _cpuMetrics.chipHeight) / 2 - _cpuMetrics.pinLength)
    readonly property real _branchProgress: Math.max(
        0, Math.min(1, (_circuitProgress - _cpuMetrics.branchStartRatio)
            / (1 - _cpuMetrics.branchStartRatio)))
    readonly property real _coverOpacity: _operationCollapsing ? 1
        : Math.max(0, 1 - Math.max(0, Math.min(1,
            (_circuitProgress - _cpuMetrics.coverFadeStart)
                / (1 - _cpuMetrics.coverFadeStart))))

    // ==================== Signals 信号 ====================
    signal collapseStarted()
    signal expandStarted()
    signal collapseFinished()
    signal expandFinished()

    // ==================== Public Methods 公开方法 ====================
    function collapse(sourceItem) {
        transition.stop()
        transition._sourceItem = sourceItem
        transition._savedSourceVisible = sourceItem ? sourceItem.visible : false
        transition._operationCollapsing = true
        transition._collapsed = false
        transition._visualVisible = true
        transition._progress = Enums.opacityLevel.invisible
        transition._circuitProgress = Enums.opacityLevel.invisible
        if (!sourceItem) {
            transition._visualVisible = false
            transition._collapsed = true
            transition.collapseStarted()
            transition.collapseFinished()
            return false
        }
        sourceItem.visible = true
        chip.x = transition._chipRestX
        chip.y = transition._chipStartY
        chip.opacity = Enums.opacityLevel.invisible
        chip.scale = transition._cpuMetrics.dropStartScale
        transition.collapseStarted()
        dropAnimation.restart()
        return true
    }

    function expand(sourceItem) {
        transition.stop()
        transition._sourceItem = sourceItem
        transition._savedSourceVisible = sourceItem ? sourceItem.visible : false
        transition._operationCollapsing = false
        transition._collapsed = false
        transition._visualVisible = true
        transition._progress = Enums.opacityLevel.invisible
        transition._circuitProgress = Enums.opacityLevel.invisible
        if (!sourceItem) {
            transition._visualVisible = false
            transition.expandStarted()
            transition.expandFinished()
            return false
        }
        sourceItem.visible = true
        chip.x = transition._chipRestX
        chip.y = transition._chipRestY
        chip.opacity = Enums.opacityLevel.visible
        chip.scale = Enums.opacityLevel.visible
        transition.expandStarted()
        circuitAnimation.restart()
        return true
    }

    function stop() {
        if (dropAnimation) dropAnimation.stop()
        if (circuitAnimation) circuitAnimation.stop()
        if (transition._sourceItem) {
            transition._sourceItem.visible = transition._savedSourceVisible
        }
        transition._sourceItem = null
        transition._savedSourceVisible = false
        transition._operationCollapsing = false
        transition._collapsed = false
        transition._visualVisible = false
        transition._progress = Enums.opacityLevel.invisible
        transition._circuitProgress = Enums.opacityLevel.invisible
        if (chip) {
            chip.x = transition._chipRestX
            chip.y = transition._chipRestY
            chip.opacity = Enums.opacityLevel.invisible
            chip.scale = Enums.opacityLevel.visible
        }
    }

    function _restoreHostWindowAfterOverlay() {
        // CPU reveal stays in the page window and never hides the host window.
        // CPU 揭幕始终在页面窗口内完成，不会隐藏宿主窗口。
    }

    // ==================== Internal Methods 内部方法 ====================
    function _finishCollapse() {
        if (!transition._operationCollapsing) return
        if (transition._sourceItem) transition._sourceItem.visible = false
        transition._sourceItem = null
        transition._savedSourceVisible = false
        transition._progress = Enums.opacityLevel.visible
        transition._collapsed = true
        transition.collapseFinished()
    }

    function _finishExpand() {
        if (transition._operationCollapsing) return
        if (transition._sourceItem) {
            transition._sourceItem.visible = transition.keepSourceHiddenOnExpand
                ? false : true
        }
        transition._sourceItem = null
        transition._savedSourceVisible = false
        transition._progress = Enums.opacityLevel.visible
        transition._visualVisible = false
        transition._collapsed = false
        transition.expandFinished()
    }

    anchors.fill: parent
    Component.onDestruction: transition.stop()

    // ==================== Content 内容 ====================
    Item {
        id: cpuVisual

        objectName: "cpuTransitionVisual"
        anchors.fill: parent
        visible: transition._visualVisible
        z: Enums.zIndex.overlay

        Rectangle {
            id: revealCover

            objectName: "cpuTransitionCover"
            anchors.fill: parent
            color: Enums.backgroundColor
            opacity: transition._coverOpacity
            layer.enabled: true
            layer.effect: OpacityMask {
                invert: true
                mask: ShaderEffectSource {
                    hideSource: false
                    live: true
                    smooth: true
                    sourceItem: circuitArtwork
                }
            }
        }

        Item {
            id: circuitArtwork

            objectName: "cpuTransitionCircuit"
            anchors.fill: parent
            visible: transition._visualVisible

            Rectangle {
                id: topTrace

                x: transition._chipRestX + transition._cpuMetrics.chipWidth / 2
                    - width / 2
                y: chip.y - transition._cpuMetrics.pinLength - height
                width: transition._cpuMetrics.traceWidth
                height: transition._circuitProgress * transition._verticalReach
                color: Enums.accentColorLight
                opacity: transition._circuitProgress
            }

            Rectangle {
                id: bottomTrace

                x: transition._chipRestX + transition._cpuMetrics.chipWidth / 2
                    - width / 2
                y: chip.y + chip.height + transition._cpuMetrics.pinLength
                width: transition._cpuMetrics.traceWidth
                height: transition._circuitProgress * transition._verticalReach
                color: Enums.accentColorLight
                opacity: transition._circuitProgress
            }

            Rectangle {
                id: leftTrace

                x: chip.x - transition._cpuMetrics.pinLength - width
                y: transition._chipRestY + transition._cpuMetrics.chipHeight / 2
                    - height / 2
                width: transition._circuitProgress * transition._horizontalReach
                height: transition._cpuMetrics.traceWidth
                color: Enums.accentColorLight
                opacity: transition._circuitProgress
            }

            Rectangle {
                id: rightTrace

                x: chip.x + chip.width + transition._cpuMetrics.pinLength
                y: transition._chipRestY + transition._cpuMetrics.chipHeight / 2
                    - height / 2
                width: transition._circuitProgress * transition._horizontalReach
                height: transition._cpuMetrics.traceWidth
                color: Enums.accentColorLight
                opacity: transition._circuitProgress
            }

            // Short orthogonal branches make the reveal read as a circuit rather than a circle.
            // 短正交分支让揭幕呈现电路链路，而不是圆形扩散。
            Rectangle {
                x: transition._chipRestX + transition._cpuMetrics.chipWidth / 2
                    - width / 2
                y: transition._chipRestY - transition._cpuMetrics.pinLength
                    - transition._verticalReach * transition._cpuMetrics.branchOffsetRatio
                width: transition._branchProgress * transition._horizontalReach
                    * transition._cpuMetrics.branchSpanRatio
                height: transition._cpuMetrics.traceWidth
                color: Enums.accentColorLight
                opacity: transition._branchProgress
            }

            Rectangle {
                x: transition._chipRestX + transition._cpuMetrics.chipWidth / 2
                    - width / 2
                y: transition._chipRestY + transition._cpuMetrics.chipHeight
                    + transition._cpuMetrics.pinLength
                    + transition._verticalReach * transition._cpuMetrics.branchOffsetRatio
                width: transition._branchProgress * transition._horizontalReach
                    * transition._cpuMetrics.branchSpanRatio
                height: transition._cpuMetrics.traceWidth
                color: Enums.accentColorLight
                opacity: transition._branchProgress
            }

            Rectangle {
                x: transition._chipRestX - transition._cpuMetrics.pinLength
                    - transition._horizontalReach * transition._cpuMetrics.branchOffsetRatio
                y: transition._chipRestY + transition._cpuMetrics.chipHeight / 2
                    - height / 2
                width: transition._cpuMetrics.traceWidth
                height: transition._branchProgress * transition._verticalReach
                    * transition._cpuMetrics.branchSpanRatio
                color: Enums.accentColorLight
                opacity: transition._branchProgress
            }

            Rectangle {
                x: transition._chipRestX + transition._cpuMetrics.chipWidth
                    + transition._cpuMetrics.pinLength
                    + transition._horizontalReach * transition._cpuMetrics.branchOffsetRatio
                y: transition._chipRestY + transition._cpuMetrics.chipHeight / 2
                    - height / 2
                width: transition._cpuMetrics.traceWidth
                height: transition._branchProgress * transition._verticalReach
                    * transition._cpuMetrics.branchSpanRatio
                color: Enums.accentColorLight
                opacity: transition._branchProgress
            }

            Repeater {
                model: transition._cpuMetrics.traceNodeCount
                delegate: Rectangle {
                    required property int index

                    width: transition._cpuMetrics.traceNodeSize
                    height: width
                    radius: width / 2
                    color: Enums.accentColorLight
                    opacity: transition._circuitProgress
                    x: index < 2
                        ? transition._chipRestX
                            + transition._cpuMetrics.chipWidth / 2 - width / 2
                        : (index === 2 ? leftTrace.x - width / 2
                                       : rightTrace.x + leftTrace.width - width / 2)
                    y: index < 2
                        ? (index === 0 ? topTrace.y - height / 2
                                       : bottomTrace.y + bottomTrace.height - height / 2)
                        : transition._chipRestY
                            + transition._cpuMetrics.chipHeight / 2 - height / 2
                }
            }
        }

        // Outline-only CPU body; no icon or text is rendered in this transition.
        // 仅描边 CPU 外壳；此过渡不渲染任何图标或文字。
        Rectangle {
            id: chip

            objectName: "cpuTransitionChip"
            x: transition._chipRestX
            y: transition._chipRestY
            width: transition._cpuMetrics.chipWidth
            height: transition._cpuMetrics.chipHeight
            radius: Enums.radius.small
            color: Enums.transparent
            border.width: Enums.border.normal
            border.color: Enums.accentColor
            transformOrigin: Item.Center
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
    }

    // ==================== Transition Animations 过渡动画 ====================
    ParallelAnimation {
        id: dropAnimation

        onFinished: transition._finishCollapse()

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

        onFinished: transition._finishExpand()

        NumberAnimation {
            target: transition
            property: "_progress"
            from: Enums.opacityLevel.invisible
            to: Enums.opacityLevel.visible
            duration: transition.revealDuration
            easing.type: transition.revealEasing
        }

        NumberAnimation {
            target: transition
            property: "_circuitProgress"
            from: Enums.opacityLevel.invisible
            to: Enums.opacityLevel.visible
            duration: transition.revealDuration
            easing.type: transition.revealEasing
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
}
