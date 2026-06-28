// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."

// BottomTabBar - 移动端/窄屏底部 Tab 导航 (横向均分)
// 与桌面 NavigationBar(左侧竖直)互补: WindowsBar 据 PlatformInfo.isCompact 二选一。
// 复用 NavigationBarItem, 横向布局, 触摸友好高度。
Rectangle {
    id: control

    // ==================== Public Props 公开属性 ====================
    property var model: []
    property int currentIndex: 0

    // ==================== Signals 信号 ====================
    signal itemClicked(int index)

    // 触摸目标高度: 防御式读 PlatformInfo, 缺省 56 (Material 底部导航栏标准高)
    readonly property int barHeight:
        (typeof PlatformInfo !== "undefined" && PlatformInfo.touchTargetSize > 0)
            ? Math.max(56, PlatformInfo.touchTargetSize + 8) : 56

    implicitHeight: barHeight
    color: window_micaActiveFallback ? Enums.transparent : Enums.backgroundColor
    // 顶部分隔线
    property bool window_micaActiveFallback: false

    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: 1
        color: Enums.dividerColor
    }

    Row {
        anchors.fill: parent
        anchors.topMargin: 1

        Repeater {
            id: rep
            model: control.model

            delegate: Item {
                width: control.width / Math.max(1, rep.count)
                height: control.height

                NavigationBarItem {
                    anchors.centerIn: parent
                    text: modelData.text || ""
                    icon: modelData.icon || ""
                    selectedIcon: modelData.selectedIcon || ""
                    selected: index === control.currentIndex
                    onClicked: control.itemClicked(index)
                }
            }
        }
    }
}
