// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Window
import "../../../.."
import "../../../utils"
import "../../../data/Label"

// SearchPopup — 通用 popup 容器,根据 popupMode 决定锚定策略.
//
// 内部用 PopupWindowCore (Qt.ToolTip 真子窗,可跨主窗溢出),
// 跟 ComboBox 下拉一致.
//
// popupMode:
//   0 = AnchoredBelow  → openAtControl: 底层自动处理 panelOffset(8) +
//                        controlGap(2) + centerOffset, 不再自己算
//   1 = CenteredOverlay → 居中屏幕,固定宽 600
//
// 高度: 完全跟 rootContent.implicitHeight 走, 任何变化触发 popupBase
// 重新设尺寸.
Item {
    id: popupRoot

    // ==================== Public Props ====================
    property Item anchorTarget: null    // 锚控件 (AnchoredBelow 模式贴它下方)
    property int popupMode: 0           // 0=AnchoredBelow / 1=CenteredOverlay
    property var rootContent: null      // SearchResultList 实例,父级注入

    // isOpen 直接绑底层 PopupWindowCore 的状态,避免两份独立状态不同步
    readonly property bool isOpen: popupBase.isOpen

    // ==================== Computed Sizing ====================
    readonly property int _resolvedWidth: {
        if (popupMode === 0 && anchorTarget) {
            return Math.max(240, anchorTarget.width)
        }
        return 600  // CenteredOverlay
    }
    readonly property int _resolvedHeight: {
        if (rootContent && rootContent.implicitHeight > 0) {
            return rootContent.implicitHeight
        }
        return 56  // 兜底: 一行高度,避免 0/极小值
    }

    // ==================== Signals ====================
    signal opened()
    signal dismissed()

    // 当 rootContent 高度变化时(空态/有结果切换),同步 popupBase
    onRootContentChanged: _bindContentHeight()
    Component.onCompleted: _bindContentHeight()

    function _bindContentHeight() {
        if (!rootContent) return
        // 用 callLater 确保 rootContent 已经布局完成
        Qt.callLater(function() {
            popupBase.popupWidth = popupRoot._resolvedWidth
            popupBase.popupHeight = popupRoot._resolvedHeight
        })
    }

    // ==================== Public API ====================
    function open() {
        if (popupBase.isOpen) return

        // 实时同步尺寸 (rootContent 可能在 open 调用前刚换内容)
        popupBase.popupWidth = popupRoot._resolvedWidth
        popupBase.popupHeight = popupRoot._resolvedHeight

        if (popupMode === 0 && anchorTarget) {
            // AnchoredBelow: 让底层 openAtControl 自动处理 panelOffset
            // (8) + controlGap (2) + centerOffset 偏移,等宽锚定
            popupBase.openAtControl(anchorTarget)
        } else {
            // CenteredOverlay: 居中屏幕,上 1/3 黄金分割
            var screenW = Screen.width
            var screenH = Screen.height
            var x = (screenW - popupRoot._resolvedWidth) / 2
            var y = (screenH - popupRoot._resolvedHeight) / 3
            popupBase.open(x, y)
        }
    }

    function dismiss() {
        popupBase.close()
    }

    // 高度变化时实时同步
    Connections {
        target: popupRoot.rootContent
        ignoreUnknownSignals: true
        function onImplicitHeightChanged() {
            popupBase.popupWidth = popupRoot._resolvedWidth
            popupBase.popupHeight = popupRoot._resolvedHeight
        }
    }

    // ==================== Internal popup base ====================
    PopupWindowCore {
        id: popupBase
        targetControl: popupRoot.anchorTarget
        modal: false
        closeOnClickOutside: true
        stealFocus: true
        popupWidth: popupRoot._resolvedWidth
        popupHeight: popupRoot._resolvedHeight

        onOpened: popupRoot.opened()
        onClosed: popupRoot.dismissed()

        // 把外部塞进 popupRoot 的 rootContent 转发进 PopupWindowCore 的 popupContent
        Item {
            anchors.fill: parent
            data: popupRoot.rootContent ? [popupRoot.rootContent] : []

            // 让 rootContent 撑满 (它自己 anchors.fill 也行,但 ResultList
            // 默认是 implicitWidth/Height,不主动 fill,所以这里强制 fill)
            Component.onCompleted: {
                if (popupRoot.rootContent) {
                    popupRoot.rootContent.anchors.fill = popupRoot.rootContent.parent
                }
            }
        }
    }
}
