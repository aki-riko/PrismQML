// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Window

/*
 * WindowDragHandle - 浮动窗口拖拽手柄 / Floating window drag handle
 *
 * 用 Qt 6 的 Window.startSystemMove() 让操作系统接管拖动,完全规避手算
 * mouse delta 在多 DPI / Qt::Tool 下的闪回与漂移问题。
 *
 * Use Qt 6 Window.startSystemMove() so the OS handles the drag - avoids
 * jitter / snap-back caused by manual mouse-delta math on multi-DPI setups.
 *
 * 用法 / Usage:
 *
 *   Window {
 *       Rectangle {
 *           anchors.fill: parent
 *           // 整窗可拖
 *           WindowDragHandle { anchors.fill: parent }
 *       }
 *   }
 *
 *   // 仅标题栏可拖,带双击切换最大化
 *   WindowDragHandle {
 *       anchors.fill: titleBarItem
 *       enableDoubleClickMaximize: true
 *   }
 *
 * 信号(沿用 MouseArea 内置):
 *   - clicked(mouse): 单击;若拖动已发生则不触发
 *   - doubleClicked(mouse): 双击
 *   - pressed(mouse) / released(mouse): 透传
 *
 * 子节点(如标题栏里的输入框/按钮)如不希望被拖拽,把自己的 MouseArea
 * accepted 设为 true 截住事件即可,WindowDragHandle 底层 z-index 较低。
 */
MouseArea {
    id: root

    // ==================== Public Props 公开属性 ====================
    // 双击是否切换最大化/还原(默认 false,因为浮窗一般不用)
    property bool enableDoubleClickMaximize: false
    // 鼠标移动多少像素后判定为拖动(用于区分 click vs drag)
    property int dragThreshold: 4

    // ==================== Public Signals 公开信号 ====================
    // 拖动正式开始(超过 dragThreshold)时发射一次
    // 注意:不重声明 clicked,沿用 MouseArea 内置信号(它在 release 且未拖动时触发)
    signal dragStarted()

    // ==================== Internal State 内部状态 ====================
    property point _pressPoint: Qt.point(0, 0)
    property bool _dragging: false

    // ==================== Behavior 行为 ====================
    // 默认接受左键;使用方可用 acceptedButtons 覆盖(如 Qt.LeftButton | Qt.RightButton)
    acceptedButtons: Qt.LeftButton
    cursorShape: Qt.ArrowCursor
    hoverEnabled: false  // 不抢 hover,让上层 ToolTip/Button 正常工作

    onPressed: (mouse) => {
        _pressPoint = Qt.point(mouse.x, mouse.y)
        _dragging = false
    }

    onPositionChanged: (mouse) => {
        if (!pressed || _dragging) return
        var dx = mouse.x - _pressPoint.x
        var dy = mouse.y - _pressPoint.y
        if (Math.abs(dx) >= dragThreshold || Math.abs(dy) >= dragThreshold) {
            _dragging = true
            dragStarted()
            // 把控制权交给系统;此后 mouse 事件由 OS 处理,本 MouseArea 不再触发 release
            // 因此 MouseArea 内置 clicked 也不会触发(符合预期 — 拖动不算点击)
            var win = Window.window
            if (win) {
                win.startSystemMove()
            }
        }
    }

    onDoubleClicked: (mouse) => {
        if (enableDoubleClickMaximize) {
            var win = Window.window
            if (win) {
                if (win.visibility === Window.Maximized) {
                    win.showNormal()
                } else {
                    win.showMaximized()
                }
            }
        }
    }
}
