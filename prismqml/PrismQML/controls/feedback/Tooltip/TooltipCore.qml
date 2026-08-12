// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../.."
import "../../data"
import "../../../effects"
import QtQuick.Window  // 置于库import后:原生Window名归库后不被覆盖
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// TooltipCore - Tooltip using native Window for cross-boundary display
// 提示基类 — 使用原生 Window 实现跨窗口边界显示
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property string text: ""
    property int showDelay: Enums.duration.tooltipShowDelay
    property int hideDelay: Enums.duration.none
    // 显示期间是否持续跟随锚点(parent)位置。用于手柄拖动这类
    // parent 会移动的场景:开启后 tooltip 窗口每帧重算全局坐标跟着走。
    property bool followAnchor: false

    // ==================== Internal Props 内部属性 ====================
    readonly property int _tooltipRadius: Enums.surfaceRadius(Enums.radius.small)
    readonly property color _tooltipBackground: Enums.cardColor
    readonly property int _tooltipBorderWidth: Enums.surfaceBorderWidth(Enums.border.thin)
    readonly property color _tooltipBorderColor: Enums.stateColor.border
    readonly property var _tooltipShadowLevel: Enums.shadow.level8
    readonly property int _tooltipShadowBlur: Enums.shadow.level8.blur
    readonly property int _tooltipShadowOffset: Enums.shadow.level8.offset
    property bool _pendingShow: false
    property bool _windowRequested: false
    property bool _openScheduled: false
    
    // ==================== Readonly State 只读状态 ====================
    readonly property bool _windowVisible: tooltipWindowLoader.item
                                           ? tooltipWindowLoader.item.windowVisible
                                           : false
    readonly property int tooltipWidth: tooltipMetrics.advanceWidth + Enums.spacing.xl
    readonly property int tooltipHeight: Enums.controlSize.tooltipHeight  // 28

    // ==================== Public Methods 公开方法 ====================
    function show() {
        _pendingShow = true
        _windowRequested = true
        _scheduleOpen()
    }

    function hide() {
        _pendingShow = false
        var host = tooltipWindowLoader.item
        if (host) host.close()
    }

    // ==================== Internal Methods 内部方法 ====================
    function _scheduleOpen() {
        if (_openScheduled) return
        _openScheduled = true
        Qt.callLater(function() {
            control._openScheduled = false
            control._doOpen()
        })
    }

    // 按当前锚点位置重算窗口全局坐标(show 时一次 + followAnchor 时持续)
    function _reposition() {
        if (!control.parent) return
        var host = tooltipWindowLoader.item
        if (!host) return
        var globalPos = control.parent.mapToGlobal(control.x, control.y)
        host.reposition(Math.round(globalPos.x), Math.round(globalPos.y))
    }

    function _doOpen() {
        if (!_pendingShow) return
        if (!control.parent) return
        var host = tooltipWindowLoader.item
        if (!host) return

        _reposition()
        host.open()
    }

    // ==================== Size 尺寸 ====================
    // 保持兼容：外部仍可设置 width/height（用于定位计算）
    width: tooltipWidth
    height: tooltipHeight
    visible: false  // Item 本身不可见，窗口独立渲染

    // 兼容旧 API：外部通过 visible 属性控制时自动转发到 show/hide
    onVisibleChanged: {
        if (visible) {
            show()
        } else {
            hide()
        }
    }

    // ==================== Content 内容 ====================
    // Keep width available before the window is created 窗口创建前保持宽度可用
    TextMetrics {
        id: tooltipMetrics

        text: control.text
        font.family: Enums.fontFamily
        font.pixelSize: Enums.typography.caption
        font.weight: Font.Normal
    }

    // Create the native window on first show 首次显示时创建原生窗口
    Loader {
        id: tooltipWindowLoader

        objectName: "tooltipWindowLoader"
        active: control._windowRequested
        sourceComponent: tooltipWindowComponent
        onLoaded: {
            if (control._pendingShow) control._scheduleOpen()
        }
    }

    Component {
        id: tooltipWindowComponent

        Item {
            id: windowHost

            readonly property bool windowVisible: tipWindow ? tipWindow.visible : false

            function reposition(globalX, globalY) {
                if (!tipWindow) return
                tipWindow.x = globalX
                tipWindow.y = globalY
            }

            function open() {
                if (!tipWindow) return
                animOut.stop()
                tipWindow.visible = true
                animIn.start()
            }

            function close() {
                if (!tipWindow) return
                animIn.stop()
                animOut.start()
            }

            objectName: "tooltipWindowHost"
            width: 0
            height: 0

            // Follow a moving anchor only after the native host exists.
            // 仅在原生宿主创建后跟随移动锚点。
            Timer {
                interval: 16
                repeat: true
                running: control.followAnchor && windowHost.windowVisible
                onTriggered: control._reposition()
            }

            // Tooltip window 独立提示窗口
            Window {
                id: tipWindow

                flags: Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
                color: Enums.transparent
                width: control.tooltipWidth
                height: control.tooltipHeight
                visible: false

                // Content container for scale animation 用于缩放动画的内容容器
                Item {
                    id: content

                    objectName: "tooltipContent"
                    anchors.fill: parent
                    opacity: 0
                    scale: 0.8
                    transformOrigin: Item.Center

                    // Background styling 背景样式
                    ShadowedRectangle {
                        id: tipBackground

                        anchors.fill: parent
                        radius: control._tooltipRadius
                        color: control._tooltipBackground
                        border.width: control._tooltipBorderWidth
                        border.color: control._tooltipBorderColor
                        shadowLevel: control._tooltipShadowLevel
                        shadowVisible: Enums.usesSoftElevation

                        // Neo hard shadow neo 硬阴影
                        NeoShadow {
                            target: tipBackground
                            visible: Enums.isNeobrutalism
                            z: -1
                        }

                        // ==================== Content 内容 ====================
                        Label {
                            anchors.centerIn: parent
                            text: control.text
                            type: Enums.label.type_caption
                            color: Enums.textColor.primary
                        }
                    }
                }

                // Animations 动画
                ParallelAnimation {
                    id: animIn

                    NumberAnimation { target: content; property: "opacity"; from: 0.0; to: 1.0; duration: Enums.duration.normal }
                    NumberAnimation { target: content; property: "scale"; from: 0.8; to: 1.0; duration: Enums.duration.normal; easing.type: Easing.OutBack }
                }
                ParallelAnimation {
                    id: animOut

                    onFinished: if (tipWindow) tipWindow.visible = false

                    NumberAnimation { target: content; property: "opacity"; from: 1.0; to: 0.0; duration: Enums.duration.normal }
                    NumberAnimation { target: content; property: "scale"; from: 1.0; to: 0.8; duration: Enums.duration.normal }
                }
            }
        }
    }
}
