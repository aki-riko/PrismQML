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
    readonly property int _tooltipRadius: Enums.isNeobrutalism ? Enums.neo.radius : (Enums.isPrismDesign ? Enums.prismDesign.radiusPopup : Enums.radius.small)
    readonly property color _tooltipBackground: Enums.isPrismDesign ? Enums.dialogColor : Enums.cardColor
    readonly property int _tooltipBorderWidth: Enums.isNeobrutalism ? Enums.neo.borderWidth : Enums.border.thin
    readonly property color _tooltipBorderColor: Enums.stateColor.border
    readonly property var _tooltipShadowLevel: Enums.shadow.level8
    readonly property int _tooltipShadowBlur: Enums.shadow.level8.blur
    readonly property int _tooltipShadowOffset: Enums.shadow.level8.offset
    property bool _pendingShow: false
    
    // ==================== Readonly State 只读状态 ====================
    readonly property int tooltipWidth: tooltipText.implicitWidth + Enums.spacing.xl
    readonly property int tooltipHeight: Enums.controlSize.tooltipHeight  // 28

    // ==================== Public Methods 公开方法 ====================
    function show() {
        _pendingShow = true
        Qt.callLater(_doOpen)
    }

    function hide() {
        _pendingShow = false
        _animIn.stop()
        _animOut.start()
    }

    // ==================== Internal Methods 内部方法 ====================
    // 按当前锚点位置重算窗口全局坐标(show 时一次 + followAnchor 时持续)
    function _reposition() {
        if (!control.parent) return
        var globalPos = control.parent.mapToGlobal(control.x, control.y)
        _tipWindow.x = Math.round(globalPos.x)
        _tipWindow.y = Math.round(globalPos.y)
    }

    function _doOpen() {
        if (!_pendingShow) return
        if (!control.parent) return

        _reposition()
        _animOut.stop()
        _tipWindow.visible = true
        _animIn.start()
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

    // followAnchor 开启且窗口可见时,持续跟随锚点位置(手柄拖动时 tooltip 不掉队)
    Timer {
        interval: 16
        repeat: true
        running: control.followAnchor && _tipWindow.visible
        onTriggered: control._reposition()
    }

    // ==================== Content 内容 ====================
    // Tooltip window 独立提示窗口
    Window {
        id: _tipWindow
        
        flags: Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        color: Enums.transparent
        
        width: control.tooltipWidth
        height: control.tooltipHeight
        
        visible: false
        
        // Content container for scale animation 用于缩放动画的内容容器
        Item {
            id: _content
            anchors.fill: parent
            opacity: 0
            scale: 0.8
            transformOrigin: Item.Center
            
            // Background styling 背景样式
            ShadowedRectangle {
                id: _tipBg
                anchors.fill: parent
                radius: control._tooltipRadius
                color: control._tooltipBackground
                border.width: control._tooltipBorderWidth
                border.color: control._tooltipBorderColor
                shadowLevel: control._tooltipShadowLevel
                shadowVisible: !Enums.isNeobrutalism  // neo 关软阴影, 用下方硬阴影

                // neo 硬阴影
                NeoShadow {
                    target: _tipBg
                    visible: Enums.isNeobrutalism
                    z: -1
                }
                
                // ==================== Content 内容 ====================
                Label {
                    id: tooltipText
                    anchors.centerIn: parent
                    text: control.text
                    type: Enums.label.type_caption
                    color: Enums.textColor.primary
                }
            }
        }
        
        // Animations 动画
        ParallelAnimation {
            id: _animIn
            NumberAnimation { target: _content; property: "opacity"; from: 0.0; to: 1.0; duration: Enums.duration.normal }
            NumberAnimation { target: _content; property: "scale"; from: 0.8; to: 1.0; duration: Enums.duration.normal; easing.type: Easing.OutBack }
        }
        ParallelAnimation {
            id: _animOut
            onFinished: _tipWindow.visible = false

            NumberAnimation { target: _content; property: "opacity"; from: 1.0; to: 0.0; duration: Enums.duration.normal }
            NumberAnimation { target: _content; property: "scale"; from: 1.0; to: 0.8; duration: Enums.duration.normal }
        }
    }
}
