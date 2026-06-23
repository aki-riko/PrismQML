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
    property int showDelay: 500
    property int hideDelay: 0
    
    // ==================== Size 尺寸 ====================
    readonly property int tooltipWidth: tooltipText.implicitWidth + Enums.spacing.xl
    readonly property int tooltipHeight: Enums.controlSize.tooltipHeight  // 28
    
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

    // ==================== Internal 内部状态 ====================
    property bool _pendingShow: false

    // ==================== Methods 方法 ====================
    function show() {
        _pendingShow = true
        Qt.callLater(_doOpen)
    }

    function hide() {
        _pendingShow = false
        _animIn.stop()
        _animOut.start()
    }

    function _doOpen() {
        if (!_pendingShow) return
        if (!control.parent) return

        // 将本地 x/y 映射到全局屏幕坐标
        var globalPos = control.parent.mapToGlobal(control.x, control.y)
        _tipWindow.x = Math.round(globalPos.x)
        _tipWindow.y = Math.round(globalPos.y)

        _animOut.stop()
        _tipWindow.visible = true
        _animIn.start()
    }

    // ==================== Tooltip Window 独立提示窗口 ====================
    Window {
        id: _tipWindow
        
        flags: Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        color: "transparent"
        
        width: control.tooltipWidth
        height: control.tooltipHeight
        
        visible: false
        
        // ==================== Content Container 内容容器（用于 scale 动画）====================
        Item {
            id: _content
            anchors.fill: parent
            opacity: 0
            scale: 0.8
            transformOrigin: Item.Center
            
            // ==================== Background 样式 ====================
            ShadowedRectangle {
                id: _tipBg
                anchors.fill: parent
                radius: Enums.isNeobrutalism ? Enums.neo.radius : Enums.radius.small
                color: Enums.cardColor
                border.width: Enums.isNeobrutalism ? Enums.neo.borderWidth : Enums.border.thin
                border.color: Enums.stateColor.border
                shadowLevel: Enums.shadow.level2
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
        
        // ==================== Animation 动画 ====================
        ParallelAnimation {
            id: _animIn
            NumberAnimation { target: _content; property: "opacity"; from: 0.0; to: 1.0; duration: Enums.duration.normal }
            NumberAnimation { target: _content; property: "scale"; from: 0.8; to: 1.0; duration: Enums.duration.normal; easing.type: Easing.OutBack }
        }
        ParallelAnimation {
            id: _animOut
            NumberAnimation { target: _content; property: "opacity"; from: 1.0; to: 0.0; duration: Enums.duration.normal }
            NumberAnimation { target: _content; property: "scale"; from: 1.0; to: 0.8; duration: Enums.duration.normal }
            onFinished: _tipWindow.visible = false
        }
    }
}
