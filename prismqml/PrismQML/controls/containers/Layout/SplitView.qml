// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "_internal" as LayoutInternal

// SplitView - Collapsible pane layout 可折叠分栏布局
// Fluent SplitView parity: display modes, pane toggling, light dismiss, resizable divider
// 对齐 Fluent SplitView：显示模式、面板开合、轻触关闭、可拖拽分隔
// Display modes 显示模式: Enums.flow.split_display_overlay / split_display_inline /
// split_display_compact_overlay / split_display_compact_inline
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    // Pane display mode 面板显示模式
    property int displayMode: Enums.flow.split_display_overlay
    // Pane open state 面板开合状态
    property bool paneOpen: false
    // Pane side 面板所在边 (Qt.LeftEdge / Qt.RightEdge)
    property int panePlacement: Qt.LeftEdge
    // Expanded pane extent 展开面板宽度
    property int openPaneLength: Enums.flow.split_open_pane_length
    // Compact rail extent 紧凑栏宽度
    property int compactPaneLength: Enums.flow.split_compact_pane_length
    // Minimum pane extent while dragging 拖拽时的最小面板宽度
    property int paneMinimumSize: Enums.flow.split_pane_minimum_size
    // Click outside closes an overlay pane 点击外部关闭覆盖面板
    property bool lightDismissEnabled: true
    // Built-in pane toggle 内置面板开关
    property bool paneToggleEnabled: true
    // Draggable divider while expanded 展开时可拖拽调整宽度
    property bool paneResizeEnabled: true

    // Content 内容
    default property alias content: contentHolder.content
    property alias paneContent: paneHolder.content

    // ==================== Readonly State 只读状态 ====================
    readonly property bool isPaneOpen: paneOpen
    readonly property bool isPaneRight: panePlacement === Qt.RightEdge
    // Overlay modes float the pane over the content 覆盖模式让面板浮于内容之上
    readonly property bool isOverlayMode:
        displayMode === Enums.flow.split_display_overlay
        || displayMode === Enums.flow.split_display_compact_overlay
    // Compact modes keep a rail visible while collapsed 紧凑模式收起时保留紧凑栏
    readonly property bool isCompactMode:
        displayMode === Enums.flow.split_display_compact_overlay
        || displayMode === Enums.flow.split_display_compact_inline
    readonly property bool isPaneVisible: paneOpen || isCompactMode
    // Rendered pane extent 面板渲染宽度
    readonly property real paneExtent: isPaneOpen
        ? _boundedPaneLength
        : (isCompactMode
            ? Math.min(Math.max(0, compactPaneLength), Math.max(0, width)) : 0)
    // Content offset caused by an inline pane 内联面板造成的内容偏移
    readonly property real contentOffset: isOverlayMode ? 0 : paneExtent
    // Overlay panes dismiss on an outside click 覆盖面板支持点击外部关闭
    readonly property bool isLightDismissActive:
        paneOpen && isOverlayMode && lightDismissEnabled
    // Expanded extent clamped into the current container 约束到当前容器内的展开宽度
    readonly property real _boundedPaneLength: _boundedLength(openPaneLength)

    // ==================== Internal Props 内部属性 ====================
    // True while a requested close is flipping paneOpen 请求式关闭翻转 paneOpen 期间为真
    property bool _closeRequested: false

    // ==================== Signals 信号 ====================
    signal paneOpening()
    signal paneOpened()
    // Cancelable: set `args.cancel = true` inside the handler to veto the close
    // 可取消：在处理器内设置 args.cancel = true 即可否决本次关闭
    signal paneClosing(var args)
    signal paneClosed()
    signal paneResized(real length)
    signal lightDismissed()

    // ==================== Public Methods 公开方法 ====================
    // openPane - Expand the pane 展开面板
    function openPane() {
        paneOpen = true
    }

    // closePane - Collapse the pane 收起面板
    function closePane() {
        _requestPaneClose()
    }

    // togglePane - Flip the pane open state 切换面板开合
    function togglePane() {
        if (paneOpen) _requestPaneClose()
        else paneOpen = true
    }

    // setPaneLength - Clamp and apply an expanded pane extent 约束并应用展开宽度
    function setPaneLength(length) {
        if (typeof length !== "number" || !isFinite(length)) return
        var bounded = _boundedLength(length)
        if (bounded === openPaneLength) return
        openPaneLength = bounded
        paneResized(bounded)
    }

    // ==================== Internal Methods 内部方法 ====================
    // Clamp a requested extent between the pane minimum and the container width
    // 将请求宽度约束在面板最小宽度与容器宽度之间
    function _boundedLength(length) {
        var minimum = Math.max(0, paneMinimumSize)
        var maximum = Math.max(minimum, Math.round(width))
        return Math.round(Math.max(minimum, Math.min(maximum, length)))
    }

    // Request a cancelable pane close 请求一次可取消的面板关闭
    // Returns true when the pane actually closed 实际关闭时返回 true
    function _requestPaneClose() {
        if (!paneOpen) return false
        paneClosingArgs.cancel = false
        paneClosing(paneClosingArgs)
        if (paneClosingArgs.cancel) return false
        _closeRequested = true
        paneOpen = false
        return true
    }

    // Close through the light dismiss scrim 通过轻触遮罩关闭
    function _handleLightDismiss() {
        if (!isLightDismissActive) return
        if (!_requestPaneClose()) return
        lightDismissed()
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.flow.split_open_pane_length
    implicitHeight: Enums.flow.layout_implicit_height
    onPaneOpenChanged: {
        if (paneOpen) {
            paneOpening()
            paneOpened()
        } else {
            // A direct `paneOpen = false` still notifies here; a requested close
            // already notified before flipping the state. 直接赋值仍在此通知；
            // 请求式关闭已在翻转状态前通知过。
            if (!_closeRequested) {
                paneClosingArgs.cancel = false
                paneClosing(paneClosingArgs)
            }
            _closeRequested = false
            paneClosed()
        }
    }

    // ==================== Content 内容 ====================
    // Cancelable pane-closing payload 可取消的面板关闭载荷
    QtObject {
        id: paneClosingArgs
        property bool cancel: false
    }

    // Content holders keep the entry free of the visual tree 内容持有者让入口不承载视觉树
    QtObject {
        id: contentHolder
        default property list<QtObject> content
    }

    QtObject {
        id: paneHolder
        default property list<QtObject> content
    }

    LayoutInternal.SplitViewContent {
        id: splitViewContent
        objectName: "splitViewSurface"
        anchors.fill: parent
        host: control
        content: contentHolder.content
        paneContent: paneHolder.content
    }
}
