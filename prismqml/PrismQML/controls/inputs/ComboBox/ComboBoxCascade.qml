// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import ".."
import "_internal"
import "_internal/CascadeNodes.js" as CascadeNodes

// ComboBoxCascade - Cascade (nested submenu) combo box 级联下拉框
// The root level renders inside the host popup; every deeper level is a sibling
// native panel opened as a submenu anchored to its owner row, so a branch that
// does not fit the host window still opens completely. Owner rows never select:
// only leaves commit, and a committed leaf reports the path from the root.
// 根层渲染在宿主弹层内；更深层级都是以其父行为锚点、以子菜单形式打开的独立原生面板，
// 因此放不下的分支仍能完整展开。含子节点的行不提交选择，仅叶子提交，且提交时上报根路径。
ComboBoxCore {
    id: control

    // ==================== Public Props 公开属性 ====================
    property string delimiter: " → "         // Path separator used for currentText 路径分隔符
    property bool showPathFromRoot: true      // Commit the full path instead of the leaf 提交根路径而非叶子文本
    property bool searchEnabled: true
    property string searchPlaceholder: {
        Translator._v
        return Translator.tr("placeholder_keyword")
    }
    property int panelMinWidth: Enums.comboBoxMetrics.treePopupMinWidth
    property int panelMaxHeight: Enums.comboBoxMetrics.treePopupHeight
    property int submenuOpenDelay: Enums.duration.fast
    property var activatedPath: []            // Committed path from the root 已提交的根路径
    property int activatedSourceIndex: -1     // Committed source model index 已提交的源模型下标

    // ==================== Internal Props 内部属性 ====================
    property string _searchText: ""
    // Explicitly rebuilt: a revision-keyed binding over its own row set reads as a
    // self-dependent binding, so the visible rows are derived in one place instead.
    // 显式重建: 用版本号键控自身行集合的绑定会被判为自依赖, 因此可见行改为在一处派生。
    property var _visibleRows: []
    property var _submenuPanel: null
    property var _submenuComponent: null
    property int _openRowIndex: -1
    property int _hoveredRow: -1
    property var _rootDelegates: ({})

    // ==================== Readonly State 只读状态 ====================
    // Public view of the open branch: a cascade consumer needs to know which level is
    // showing without reaching into the popup surfaces.
    // 已展开分支的公开视图: 级联的使用方需要知道当前显示到哪一层, 而无需深入弹层表面。
    readonly property bool submenuOpen: _submenuPanel !== null && _submenuPanel.isOpen
    readonly property int submenuRowCount:
        _submenuPanel !== null ? _submenuPanel.rows.length : 0
    readonly property int _selectedVisibleIndex: {
        var count = _visibleRows.length
        for (var i = 0; i < count; i++) {
            var row = _visibleRows[i]
            if (row.path.length === activatedPath.length
                    && row.path.join("\u0000") === activatedPath.join("\u0000")) {
                return row.visibleIndex
            }
        }
        return -1
    }

    // ==================== Signals 信号 ====================
    signal pathSelected(var path)             // Full path committed 完整路径已提交
    signal itemSelected(string text, var path)  // Leaf committed, ComboBoxEntry-compatible 叶子已提交, 与入口组件同形

    // ==================== Internal Methods 内部方法 ====================
    // Opening a submenu is host work in both places: here for the root level and inside
    // the panel for deeper ones, and both must tear the previous branch down first.
    // 打开子菜单在两处都是宿主职责: 根层在此, 更深层在面板内; 两处都必须先拆除上一条分支。
    function _teardownRootSubmenu() {
        _openRowIndex = -1
        var panel = _submenuPanel
        if (!panel) return
        _submenuPanel = null
        if (panel.closeChildPanel) panel.closeChildPanel()
        panel.close()
        panel.destroy(Enums.popupMetrics.closingDelayMs)
    }

    function _openRootSubmenu(rowIndex) {
        control.openSubmenu(rowIndex)
    }

    // The hover timer's indirection only forwards to the public entry point.
    // 悬停定时器仅转发到公开入口。
    function openSubmenu(rowIndex) {
        var row = _visibleRows[rowIndex]
        if (!row || !row.children || row.children.length === 0) return
        if (_submenuPanel && _openRowIndex === rowIndex) return

        _teardownRootSubmenu()
        // Resolved through the host-owned registry: an id declared inside the popup
        // content component is not visible from this scope.
        // 经宿主持有的注册表解析: 弹层内容组件内声明的 id 在本作用域不可见。
        var owner = _rootDelegates[rowIndex]
        if (!owner) return

        if (!_submenuComponent) {
            _submenuComponent = Qt.createComponent(
                Qt.resolvedUrl("_internal/ComboBoxCascadePanel.qml"))
        }
        if (!_submenuComponent || _submenuComponent.status === Component.Error) {
            console.warn("ComboBoxCascadePanel failed to load: "
                + (_submenuComponent ? _submenuComponent.errorString() : "null"))
            _submenuComponent = null
            return
        }

        var childRows = CascadeNodes.buildRowsFrom(row.children, row.path)
        if (childRows.length === 0) return

        var panel = _submenuComponent.createObject(null, {
            "rows": childRows,
            "parentRow": owner,
            "hostSelection": _selectedVisibleIndex
        })
        if (!panel) return

        _submenuPanel = panel
        _openRowIndex = rowIndex
        panel.itemSelected.connect(function (index, path) {
            control.selectRow(path, index)
        })
        panel.dismissed.connect(function () {
            if (control._submenuPanel === panel) control._teardownRootSubmenu()
        })
        panel.openAsSubmenu(owner)
    }

    function _pathText(nodePath) {
        if (!nodePath || nodePath.length === 0) return ""
        if (!showPathFromRoot) return nodePath[nodePath.length - 1]
        var text = ""
        for (var i = 0; i < nodePath.length; i++) {
            if (i > 0) text += delimiter
            text += nodePath[i]
        }
        return text
    }

    // Overrides the base measurement: a cascade commits the path, so the host sizes
    // itself for the path and not for the leaf label alone.
    // 覆盖基类测量: 级联提交路径, 宿主因此按路径而非仅叶子标签计算宽度。
    function _calcContentWidth() {
        var comboTextMeasure = comboTextMeasureLoader.item
        if (!comboTextMeasure) return 0
        var maxW = 0
        for (var i = 0; i < _visibleRows.length; i++) {
            comboTextMeasure.text = _pathText(_visibleRows[i].path)
            maxW = Math.max(maxW, comboTextMeasure.advanceWidth)
        }
        return Math.ceil(maxW)
    }

    // Aspect that the base class already derives itself; only the extra host margin
    // for the search field and the row gutters is added here.
    // 其余尺寸交给基类自身的推导, 这里只补搜索框与行内边距所需的额外宿主余量。
    function _syncPopupWidth() {
        var textWidth = _calcContentWidth()
        popupWidthOverride = Math.max(
            control.width,
            panelMinWidth,
            textWidth + Enums.spacing.l * 4 + Enums.spacing.xs * 4)
    }

    function _activateFromPath(nodePath) {
        if (!nodePath || nodePath.length === 0) return
        var wanted = nodePath.join("\u0000")
        var rows = _visibleRows
        for (var i = 0; i < rows.length; i++) {
            if (rows[i].path.join("\u0000") === wanted) {
                currentIndex = rows[i].visibleIndex
                return
            }
        }
    }

    // The derived row set is written explicitly, so every input that can move it
    // calls the single rebuild owner below.
    // 派生行集合由显式写入, 因此每个能影响它的输入都调用下面这个唯一的重建归属。
    function _rebuildVisibleRows() {
        // Visible rows carry their own position, so a panel mirrors the host
        // selection by value instead of re-deriving an index through the filter.
        // 可见行自带位置, 面板因此按值镜像宿主选中, 无需在过滤后重新推导下标。
        var rows = CascadeNodes.filterRows(
            CascadeNodes.buildRows(control._safeModel), _searchText.toLowerCase())
        var positioned = []
        for (var i = 0; i < rows.length; i++) {
            positioned.push({
                text: rows[i].text,
                icon: rows[i].icon,
                enabled: rows[i].enabled,
                path: rows[i].path,
                children: rows[i].children,
                visibleIndex: i
            })
        }
        _visibleRows = positioned
        _syncPopupWidth()
        _activateFromPath(activatedPath)
    }

    // ==================== Public Methods 公开方法 ====================
    // Commits a leaf row: records its path, mirrors it on the host text and closes
    // the whole cascade, deepest level first.
    // 提交叶子行: 记录路径, 在宿主文本上镜像, 并自最深层级起关闭整条级联。
    function selectRow(nodePath, sourceIndex) {
        if (!nodePath || nodePath.length === 0) return
        activatedPath = nodePath
        activatedSourceIndex = sourceIndex === undefined ? -1 : sourceIndex
        currentText = _pathText(nodePath)
        pathSelected(nodePath)
        itemSelected(currentText, nodePath)
        textActivated(currentText)
        closePopupTree()
    }

    function closePopupTree() {
        _teardownRootSubmenu()
        closePopup()
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.comboBoxMetrics.defaultWidth
    // The visible-row cap owns the popup height: maxVisibleItems multiplies it by
    // popupItemHeight, so the candidate surface never exceeds the panel budget.
    // 可见行上限决定弹层高度: maxVisibleItems 与 popupItemHeight 相乘, 候选表面因此
    // 不会超出面板预算。
    popupItemHeight: Enums.comboBoxMetrics.itemHeight
    maxVisibleItems: Math.max(1, Math.floor(
        (panelMaxHeight - (searchEnabled ? Enums.comboBoxMetrics.searchBoxHeight : 0))
        / Enums.comboBoxMetrics.itemHeight))

    Component.onCompleted: {
        // The host measures the committed path, so the shared text measurer must be
        // live before the first open; a Loader that activates on open is still null
        // while the popup is sizing the surface.
        // 宿主按已提交路径测宽, 因此共享文本测量器必须在首次展开前就绪; 展开时才激活的
        // Loader 在弹层定尺寸那一刻仍为 null。
        _popupContentRequested = true
        _rebuildVisibleRows()
    }
    onModelChanged: _rebuildVisibleRows()
    // The query lives on this control, so its own change handler drives the refresh.
    // 查询文本属于本控件, 因此由它自己的变更处理器驱动刷新。
    on_SearchTextChanged: _rebuildVisibleRows()
    onSearchEnabledChanged: _syncPopupWidth()
    onPanelMaxHeightChanged: _syncPopupWidth()

    // ==================== Content 内容 ====================
    popupContent: Component {
        CascadeRowList {
            id: rootRowList

            withSearch: control.searchEnabled
            arrowFollowsChildren: true
            rows: control._visibleRows
            currentIndex: control._selectedVisibleIndex
            maxHeight: control.panelMaxHeight
            searchPlaceholder: control.searchPlaceholder
            hostRegistry: control._rootDelegates

            onRowClicked: (index, path) => control.selectRow(path, index)
            onSubmenuRequested: (index) => control._openRootSubmenu(index)
            onSearchTextChanged: (text) => control._searchText = text
            // Owner rows open their branch on hover after the shared delay, exactly as
            // a deeper level does; the root level is the only one whose rows live in
            // the host popup rather than in a panel-owned surface.
            // 父行在共享延迟后于悬停时展开其分支, 与更深层级一致; 根层是唯一其行位于宿主
            // 弹层而非面板自有表面中的层级。
            onRowHoverChanged: (index, hovered) => {
                if (hovered) {
                    rootSubmenuTimer.stop()
                    control._hoveredRow = index
                    rootSubmenuTimer.restart()
                } else if (control._hoveredRow === index) {
                    rootSubmenuTimer.stop()
                    control._hoveredRow = -1
                }
            }
        }
    }

    Timer {
        id: rootSubmenuTimer

        interval: control.submenuOpenDelay
        repeat: false
        onTriggered: {
            if (control._hoveredRow >= 0) control._openRootSubmenu(control._hoveredRow)
        }
    }

    // Each deeper level is created on demand and owns at most one native popup, so a
    // branch that does not fit the host window still opens completely. The lifecycle is
    // owned by _openRootSubmenu/_teardownRootSubmenu rather than by a Loader, because a
    // Loader cannot hand out the previous instance while a new one is being created.
    // 每个更深层级按需创建并至多持有一个原生弹层, 因此宿主窗口放不下的分支仍能完整展开。
    // 生命周期由 _openRootSubmenu/_teardownRootSubmenu 持有而非 Loader: Loader 无法在
    // 创建新实例时先交回旧实例。

}
