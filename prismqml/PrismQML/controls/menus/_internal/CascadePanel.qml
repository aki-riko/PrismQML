// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../utils"
import "."
import "CascadeNodes.js" as CascadeNodes

// CascadePanel - A deeper cascade level 级联结构的更深层级
// One native popup surface per level, rendering the same CascadeRowList the root level
// uses, so every level of a cascade reads as one control. Submenu placement, native
// surfaces and the open/close lifecycle come from PopupWindowCore; the anchored
// submenu entry point is owned here because only MenuCore offers one and this level is
// a cascade panel rather than a menu. Button dropdowns and cascade combo boxes share
// this stack instead of each carrying its own.
// 每层一个原生弹层表面, 渲染与根层相同的 CascadeRowList, 因此级联的每一层读起来都是
// 同一个控件。子菜单定位、原生表面与开关生命周期来自 PopupWindowCore; 锚定式子菜单入口
// 由本组件持有, 因为只有 MenuCore 提供该入口, 而本层是级联面板而非菜单。下拉按钮与级联
// 下拉框共用这份栈, 而非各自持有一份。
// Each level owns at most one child level and tears it down depth-first, so a deeper
// level can never outlive the level it came from.
// 每层至多持有一个子层并按深度优先拆除, 更深层级绝不比其来源层存活更久。
PopupWindowCore {
    id: panel

    // ==================== Public Props 公开属性 ====================
    property var rows: []                    // Rows owned by this level 本层持有的行数据
    property Item parentRow: null            // Owner row used as the submenu anchor 子菜单锚点父行
    property int hostSelection: -1           // Host selection for indicator mirror 宿主选中下标

    // ==================== Internal Props 内部属性 ====================
    property var _childPanel: null
    property var _submenuComponent: null
    property int _hoveredRow: -1
    readonly property int _submenuDelay: Enums.duration.fast

    // ==================== Signals 信号 ====================
    // Named after MenuCore's dismissal signal: a cascade level closes as a popup,
    // independently of the host selection change that a plain `closed` would imply.
    // 命名沿用 MenuCore 的关闭信号: 级联层作为弹层关闭, 与普通 closed 所暗示的宿主选中变化无关。
    signal dismissed()
    signal itemSelected(int index, var path)

    // ==================== Internal Methods 内部方法 ====================
    function _closeChildPanel() {
        submenuOpenTimer.stop()
        _hoveredRow = -1
        var child = _childPanel
        if (!child) return
        _childPanel = null
        if (child.closeChildPanel) child.closeChildPanel()
        child.close()
        child.destroy(Enums.popupMetrics.closingDelayMs)
    }

    function _ensureSubmenuComponent() {
        if (_submenuComponent) return _submenuComponent
        _submenuComponent = Qt.createComponent(
            Qt.resolvedUrl("CascadePanel.qml"))
        if (!_submenuComponent || _submenuComponent.status === Component.Error) {
            console.warn("CascadePanel failed to load: "
                + (_submenuComponent ? _submenuComponent.errorString() : "null"))
            _submenuComponent = null
        }
        return _submenuComponent
    }

    function _openSubmenuForRow(rowIndex) {
        var row = rows[rowIndex]
        if (!row || !row.children || row.children.length === 0) return
        if (_childPanel && _hoveredRow === rowIndex) return

        // Depth-first teardown before a sibling level takes over.
        // 同级层接管前先按深度优先拆除。
        _closeChildPanel()
        var component = _ensureSubmenuComponent()
        if (!component) return
        var owner = rowList.rowDelegate(rowIndex)
        if (!owner) return

        // The deeper level continues this row's path: a committed value is the path
        // from the root, so the child level cannot restart paths at its own rows.
        // 更深层级承接本行的路径: 提交值是根路径, 因此子层不能以自身行作为路径起点。
        var childRows = CascadeNodes.buildRowsFrom(row.children, row.path)
        if (childRows.length === 0) return

        var child = component.createObject(null, {
            "rows": childRows,
            "parentRow": owner,
            "hostSelection": hostSelection,
            "stealFocus": false
        })
        if (!child) return

        _hoveredRow = rowIndex
        _childPanel = child
        child.itemSelected.connect(function (index, path) {
            panel.itemSelected(index, path)
        })
        child.dismissed.connect(function () {
            if (panel._childPanel === child) panel._closeChildPanel()
        })
        child.openAsSubmenu(owner)
    }

    // ==================== Public Methods 公开方法 ====================
    // Open as a child menu with both first rows aligned. Owned here rather than
    // inherited: the submenu entry point lives on MenuCore, while this level is a
    // cascade panel over the bare popup surface.
    // 作为子菜单打开并对齐父子首行。由本组件持有而非继承: 子菜单入口位于 MenuCore,
    // 而本层是建立在纯弹层表面之上的级联面板。
    function openAsSubmenu(parentAction) {
        if (!parentAction) return
        targetControl = parentAction
        _submenuPlacement = true
        _openWhenSurfaceReady()
    }

    // The surface host is created by a Loader that has not produced its window yet
    // while this panel is being constructed, and opening without a surface is a no-op.
    // Waiting here — instead of re-entering open every turn — keeps the lifecycle
    // completion timer free to fire.
    // 本面板构建期间, 弹层宿主由尚未生成窗口的 Loader 创建; 没有表面时打开是空操作。
    // 在此等待而非每拍重入 open, 使生命周期完成定时器得以触发。
    function _openWhenSurfaceReady() {
        if (!targetControl) return
        if (isOpen || isClosing) return
        if (!_popupWindow) {
            _nativeWindowRequested = true
            Qt.callLater(_openWhenSurfaceReady)
            return
        }
        var windowPos = _calcSubmenuPosition()
        _openAtPosition(windowPos.x, windowPos.y, true)
    }

    // Called by the owning level when this level must tear down its own subtree.
    // 当本层需要拆除自身子树时由归属层调用。
    function closeChildPanel() {
        _closeChildPanel()
    }

    // ==================== Size 尺寸 ====================
    // A cascade level is a hover-owned surface: it must not take focus from the level
    // that owns it, and it must not dismiss itself on a focus change. Dismissal is
    // owned by the parent level, which knows when a different branch takes over; a
    // focus-loss rule would also close the very surface the pointer is travelling to.
    // 级联层是悬停持有的表面: 不得夺走归属层焦点, 也不得因焦点变化自关。收起由父层持有,
    // 因为只有父层知道何时是另一条分支接管; 失焦规则还会关掉指针正前往的那个表面。
    stealFocus: false
    closeOnClickOutside: false
    implicitContentWidth: rowList.preferredWidth
    implicitContentHeight: rowList.preferredHeight

    onClosed: {
        _closeChildPanel()
        dismissed()
    }

    // ==================== Content 内容 ====================
    CascadeRowList {
        id: rowList

        anchors.fill: parent
        rows: panel.rows
        currentIndex: panel.hostSelection

        onRowClicked: (index, path) => panel.itemSelected(index, path)
        onSubmenuRequested: (index) => panel._openSubmenuForRow(index)
        onRowHoverChanged: (index, hovered) => {
            if (hovered) {
                submenuOpenTimer.stop()
                panel._hoveredRow = index
                submenuOpenTimer.restart()
            } else if (panel._hoveredRow === index) {
                submenuOpenTimer.stop()
                panel._hoveredRow = -1
            }
        }
    }

    Timer {
        id: submenuOpenTimer

        interval: panel._submenuDelay
        repeat: false
        onTriggered: {
            if (panel._hoveredRow >= 0) panel._openSubmenuForRow(panel._hoveredRow)
        }
    }
}
