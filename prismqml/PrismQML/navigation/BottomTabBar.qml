// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."
import "_internal/NavigationLayout.js" as NavigationLayout

// BottomTabBar - 移动端/窄屏底部 Tab 导航 (横向均分)
// 与桌面 NavigationBar(左侧竖直)互补: WindowsBar 据 PlatformInfo.isCompact 二选一。
// 复用 NavigationBarItem, 横向布局, 触摸友好高度。
Rectangle {
    id: control

    // ==================== Public Props 公开属性 ====================
    property var model: []
    property int currentIndex: 0
    property bool window_micaActiveFallback: false

    // ==================== Readonly State 只读状态 ====================
    readonly property var _safeModel:
        model === null || model === undefined ? []
        : (typeof model.length === "number" ? model : [])
    readonly property int _visibleItemCount: Math.max(1, NavigationLayout.visibleCount(_safeModel))

    // Touch target height: defensive PlatformInfo read, default uses metrics 触摸目标高度：防御式读 PlatformInfo，默认使用度量常量
    readonly property int barHeight:
        (typeof PlatformInfo !== "undefined" && PlatformInfo && PlatformInfo.touchTargetSize > 0)
            ? Math.max(Enums.controlSize.bottomTabBarHeight, PlatformInfo.touchTargetSize + Enums.spacing.m)
            : Enums.controlSize.bottomTabBarHeight
    readonly property color _bottomTabBackground: window_micaActiveFallback ? Enums.transparent : Enums.backgroundColor
    readonly property color _bottomTabDividerColor: Enums.dividerColor
    readonly property real _bottomTabDividerHeight: Enums.border.thin

    // ==================== Signals 信号 ====================
    signal itemClicked(int index)

    // ==================== Size 尺寸 ====================
    implicitHeight: barHeight
    height: implicitHeight
    color: _bottomTabBackground

    // ==================== Content 内容 ====================
    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: control._bottomTabDividerHeight
        color: control._bottomTabDividerColor
    }

    Row {
        anchors.fill: parent
        anchors.topMargin: control._bottomTabDividerHeight

        Repeater {
            id: rep
            model: control._safeModel

            delegate: Item {
                readonly property bool itemVisible: !modelData || modelData.visible !== false

                visible: itemVisible
                width: itemVisible ? control.width / control._visibleItemCount : 0
                height: itemVisible ? control.height : 0

                NavigationBarItem {
                    objectName: "bottomNavigationItem_" + text
                    anchors.fill: parent
                    visible: itemVisible
                    text: modelData ? (modelData.text || "") : ""
                    icon: modelData ? (modelData.icon || "") : ""
                    selectedIcon: modelData ? (modelData.selectedIcon || "") : ""
                    badgeCount: modelData ? (modelData.badgeCount || 0) : 0
                    selected: itemVisible && index === control.currentIndex
                    onClicked: control.itemClicked(index)
                }
            }
        }
    }
}
