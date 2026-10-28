// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../.."
import "../../../effects"
import "../../icons"
import "../../utils"
import ".."
import "../../containers"
import "../../containers/ScrollBar"
import "../../menus"
import "_internal"
import "_internal/ComboBoxTreeNodes.js" as TreeNodes
import "_internal/ComboBoxTreeRows.js" as TreeRows
import QtQuick  // After library import: unprefixed native types stay unshadowed 置于库import后:去前缀后保原生类型不被库覆盖

// ComboBoxTree - Tree combo box with search and expandable nodes 树形下拉框
// Extends ComboBoxCore for consistent styling 继承ComboBoxCore保持样式一致
ComboBoxCore {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property bool searchEnabled: true
    property string searchPlaceholder: {
        Translator._v
        return Translator.tr("placeholder_keyword")
    }
    property string delimiter: " → "
    property bool showPathFromRoot: true

    // ==================== Internal Props 内部属性 ====================
    property var _expandedNodes: ({})
    property string _searchText: ""
    property var _flatModel: []
    property bool _initialized: false
    //: 弹层里搜索框的引用（由 popupContent 实例化时回写）。用于「点分类展开后把焦点还给搜索框」：
    //: 弹层内容是独立 Component，外层函数作用域够不到它的 id。
    property var _searchBox: null
    //: 弹层高度（按行数算 + 生长动画 + 原生窗口跟随）由共用件持有，
    //: 单树与多选树同一套口径。
    property var _sizer: treePopupSizer
    //: 下一次重建是否给「插入/删除的行」走过渡动画。只有展开/折叠置位；搜索收窄与
    //: 换模型走整体重建，避免逐键闪动。
    property bool _animateRowChange: false

    // ==================== Readonly State 只读状态 ====================
    readonly property bool _popupHeightAnimating: treePopupSizer.running
    //: 行视图模型（`_flatModel` 的增量镜像）。委托绑它而不是整表替换的数组，
    //: 展开/折叠才有「插入/删除/让位」可动；`_flatModel` 仍是数据真相源。
    readonly property var _rowModel: treeRowModel

    // ==================== Signals 信号 ====================
    signal itemSelected(string text, var path)

    // ==================== Public Methods 公开方法 ====================
    function openPopup() {
        _rebuildFlatModel()
        _popup.popupWidth = Math.max(control.width, Enums.comboBoxMetrics.treePopupMinWidth)
        _popup.openAtControl(control)
        isOpen = true
        _focusPopupSearch()
    }

    /// 非可编辑树的弹层自己抢焦点、搜索框就在弹层里：打开即把焦点交给它，用户可以直接
    /// 打字收窄（旧实现要先用鼠标点一下搜索框，体感像坏了）。可编辑树把焦点留在宿主
    /// 输入框（`onTextEdited` 镜像进 `_searchText`），不能抢。
    ///
    /// ⚠️ `_searchBox` 由弹层内容的 `Component.onCompleted` 回写，而弹层窗口是**懒创建**
    /// 的（预热/首次 open 之后才实例化），所以 `openPopup()` 里这一刻可能还是 null：
    /// 先立刻试一次，没拿到就等下一次窗口可见再试。
    function _focusPopupSearch() {
        if (editable || !searchEnabled || !isOpen) return
        if (_searchBox) {
            _searchBox.focusInput()
            return
        }
        // 下一拍再试：弹层窗口的懒创建/预热发生在本次调用之后。弹层已关或表面已建好
        // 却没有搜索框时不再重试（`isOpen`/`_searchBox` 两个出口都在上面）。
        Qt.callLater(_focusPopupSearch)
    }

    // ==================== Internal Methods 内部方法 ====================
    function _updatePopupContentHeight() {
        treePopupSizer.itemCount = _flatModel.length
        treePopupSizer.searchEnabled = searchEnabled
        treePopupSizer.update()
    }

    function _initTree() {
        // Component.onCompleted can run before ComboBoxCore's derived
        // _safeModel binding is ready in an asynchronous Loader. Read the
        // public base property and validate it before touching length.
        // 异步 Loader 中 Component.onCompleted 可能早于 ComboBoxCore 的
        // _safeModel 派生绑定就绪；先校验基类公开 model，再读取 length。
        var sourceModel = control.model
        if (sourceModel === null || sourceModel === undefined
                || typeof sourceModel.length !== "number"
                || sourceModel.length <= 0) return

        _expandAllNodes()
        _rebuildFlatModel()
    }
    
    // Traversal is owned by TreeNodes 遍历由 TreeNodes 持有
    function _expandAllNodes() {
        _expandedNodes = TreeNodes.expandAll(_safeModel)
    }

    function _rebuildFlatModel() {
        var flat = []
        var searchText = _searchText.toLowerCase()
        TreeNodes.flatten(
            _safeModel,
            { expandedNodes: _expandedNodes, searchText: searchText },
            function (row) {
                flat.push({
                    text: row.text,
                    depth: row.depth,
                    nodeId: row.nodeId,
                    path: row.path,
                    hasChildren: row.hasChildren,
                    expanded: row.expanded
                })
            })
        _flatModel = flat
        var animate = _animateRowChange
        _animateRowChange = false
        _syncRows(flat, animate)
        _updatePopupContentHeight()
    }

    /// 一行在视图模型里的可存字段（`path` 是数组，留给 `_flatModel` 按 nodeId 反查）。
    function _rowData(row) {
        return {
            text: row.text,
            depth: row.depth,
            nodeId: row.nodeId,
            hasChildren: row.hasChildren,
            expanded: row.expanded
        }
    }

    function _resetRows(flat) {
        var rows = []
        for (var i = 0; i < flat.length; i++) rows.push(_rowData(flat[i]))
        TreeRows.resetRows(treeRowModel, rows)
    }

    /// 把 `treeRowModel` 调整成 `flat`。
    ///
    /// 展开/折叠永远是**单段插入或单段删除**（被展开节点的整棵子树连续出现/消失），
    /// 只有这两条会触发过渡动画；其它变更（搜索收窄、换模型）整体重建，逐键不闪。
    /// 差异算法在共用件 `ComboBoxTreeRows.js` 里（单树与多选树同一套）。
    function _syncRows(flat, animate) {
        var rows = []
        for (var i = 0; i < flat.length; i++) rows.push(_rowData(flat[i]))
        TreeRows.syncRows(treeRowModel, rows, "nodeId", animate)
        TreeRows.syncRowFields(treeRowModel, rows, "nodeId", ["expanded", "text"])
    }

    function _toggleExpand(nodeId) {
        _animateRowChange = true
        _expandedNodes = TreeNodes.toggleExpanded(_expandedNodes, nodeId)
    }

    /// 该 nodeId 在**当前可见模型**里的那一行（找不到返回 null）。
    function _rowForNodeId(nodeId) {
        for (var i = 0; i < _flatModel.length; i++) {
            if (_flatModel[i].nodeId === nodeId) return _flatModel[i]
        }
        return null
    }

    /// 弹层里点一行。委托只上报 nodeId（行视图模型里不放数组字段），
    /// `path` 由 `_flatModel` 反查后仍走 `_selectNode`，选中语义与旧实现一致。
    function _selectRow(nodeId) {
        var row = _rowForNodeId(nodeId)
        if (row) _selectNode(row.text, row.path)
    }
    
    function _getPathText(path) {
        return showPathFromRoot ? path.join(delimiter) : path[path.length - 1]
    }
    
    /// 该 path 在**当前可见模型**里的那一行（找不到返回 null）。
    /// `path` 由 `TreeNodes.flatten` 产出，与模型一一对应；用 JSON 比较避免数组引用差异。
    function _rowForPath(path) {
        var target = JSON.stringify(path || [])
        for (var i = 0; i < _flatModel.length; i++) {
            if (JSON.stringify(_flatModel[i].path) === target) return _flatModel[i]
        }
        return null
    }

    /// 选中 / 展开一个节点。
    ///
    /// 🔴 2026-10-21：点**有子节点的行**（级联菜单的分类/分组）只展开/折叠，**不关闭弹层**。
    /// 旧实现无条件 `closePopup()`：用户点「分类」想看下面的账号，弹层直接消失——
    /// 级联菜单等于没法用（Kaleidos 百战助手实测反馈「点级联菜单就自动收起」）。
    /// 只有点**叶子**才算真正选中并关闭。
    ///
    /// ⚠️ 签名**必须保持 `(nodeText, path)` 两个参数**：QML 函数一旦声明 4 个形参，
    /// 引擎就按 4 参数对外暴露，既有调用方（含 `_assert_path_selection` 这类测试）
    /// 用两参数会直接 `TypeError`。所以 `nodeId` / `hasChildren` 由本函数自己按 `path`
    /// 在 `_flatModel` 里查（一次 O(可见行数) 的查找，点击频率下可忽略）。
    function _selectNode(nodeText, path) {
        var row = _rowForPath(path)
        if (row && row.hasChildren && row.nodeId !== undefined && row.nodeId !== null) {
            _toggleExpand(row.nodeId)
            // 展开/折叠会重建 `_flatModel`；把焦点还给弹层里的搜索框，用户可以继续输入收窄。
            // （`PopupSearchBox` 提供 `focusInput()`；`_search` 是 ComboBoxSearchState，
            //   不含输入框引用，别往那边猜。）
            if (searchEnabled && _searchBox) _searchBox.focusInput()
            return
        }
        currentText = _getPathText(path)
        itemSelected(nodeText, path)
        closePopup()
    }
    
    // ==================== Size 尺寸 ====================
    implicitWidth: 200
    showFocusedBorder: false  // No focus line for tree 树不显示聚焦下划线
    Component.onCompleted: _initTree()
    onModelChanged: _initTree()
    on_ExpandedNodesChanged: _rebuildFlatModel()
    on_SearchTextChanged: _rebuildFlatModel()
    onSearchEnabledChanged: _updatePopupContentHeight()
    onIsOpenChanged: {
        if (!isOpen) treePopupSizer.heightAnimation.stop()
    }
    // 可编辑模式下候选展开期间焦点留在宿主输入框（弹层刻意不抢焦点），因此「输入即
    // 搜索」只能由输入框驱动：把输入文字镜像进 `_searchText`，弹层里的搜索框同步显示，
    // 两处永远同一个查询。
    onTextEdited: function(text) {
        _searchText = text
        if (_searchBox && _searchBox.text !== text) _searchBox.text = text
    }
    // 候选表面真正消失后才丢弃上一次查询（与 ComboBoxSearchState 同口径：查询要活过
    // 收起动画，否则收起中的列表会跳回全量），否则下一次展开会带着过期过滤条件。
    onPopupVisibleChanged: {
        if (popupVisible) return
        _searchText = ""
        if (_searchBox) _searchBox.clear()
    }

    // ==================== Content 内容 ====================
    popupContent: Component {
        Column {
            anchors.fill: parent
            spacing: Enums.spacing.none

            Component.onCompleted: control._searchBox = searchBox

            // Search box 搜索框 (复用PopupSearchBox)
            PopupSearchBox {
                id: searchBox
                width: parent.width
                searchEnabled: control.searchEnabled
                placeholderText: control.searchPlaceholder
                onSearchTextChanged: (text) => control._searchText = text
            }
            
            // Tree content 树内容
            Item {
                id: treeContainer

                // 需要滚动条 = 行数 × 行高 超过可视高度。
                // 🔴 不能拿 `treeListView.contentHeight` 判：展开/收起的让位动画期间它逐帧
                // 变化，而它又驱动 rightMargin → 宽度 → 内容高度，正好凑成绑定环
                // （实测报 "Binding loop detected for needsScroll"）。行高固定，
                // 用数据行数算才是稳定量。
                readonly property bool needsScroll: control._flatModel.length
                    * Enums.comboBoxMetrics.itemHeight > treeListView.height

                width: parent.width
                height: parent.height - (control.searchEnabled ? Enums.comboBoxMetrics.searchBoxHeight : 0)

                ListView {
                    id: treeListView
                    anchors.fill: parent
                    anchors.rightMargin: treeContainer.needsScroll ? Enums.comboBoxMetrics.scrollBarRightMargin : 0
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds
                    interactive: false  // Disable native scroll, use smooth scroll 禁用原生滚动，使用平滑滚动
                    model: control._rowModel
                    
                    delegate: TreeMenuDelegate {
                        width: treeListView.width
                        text: model.text
                        depth: model.depth
                        hasChildren: model.hasChildren
                        expanded: model.expanded
                        checkable: false

                        onToggleExpand: control._toggleExpand(model.nodeId)
                        onClicked: control._selectRow(model.nodeId)
                    }

                    // 展开/收起动画：下面的行先平滑让位，新行再淡入。
                    //
                    // 顺序不能反：新行一旦先摆到终点位置再淡入，旧行还在路上，前者会压在
                    // 后者身上出现文字重影（实测抓帧确认）。所以 add 先 Pause 让 displaced
                    // 走完再显形。弹层高度顶到 `treePopupHeight`（滚动条接管）时，高度动画
                    // 无从发生，动画就全靠这一层。
                    add: Transition {
                        SequentialAnimation {
                            // 先立刻透明（否则暂停期间它还是全不透明，一样压在旧行上），
                            // 等下面的行让位到位后再淡入。
                            PropertyAction { property: "opacity"; value: 0 }
                            PauseAnimation { duration: Enums.duration.ultraFast }
                            NumberAnimation {
                                property: "opacity"
                                from: 0
                                to: 1
                                duration: Enums.duration.fast
                                easing.type: Easing.OutCubic
                            }
                        }
                    }
                    displaced: Transition {
                        NumberAnimation {
                            property: "y"
                            duration: Enums.duration.fast
                            easing.type: Easing.OutCubic
                        }
                    }

                    // Smooth scroll 平滑滚动
                    PopupSmoothScroll { flickable: treeListView; enabled: treeContainer.needsScroll }
                }
                
                Loader {
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.margins: Enums.spacing.xxs
                    width: Enums.comboBoxMetrics.scrollBarWidth
                    active: parent.needsScroll
                    sourceComponent: ScrollBarEntry {
                        flickable: treeListView
                        width: Enums.comboBoxMetrics.scrollBarWidth
                    }
                }
            }
        }
    }

    // Popup height owner (shared with the multi-select tree) 弹层高度所有者（与多选树共用）
    TreePopupSizer {
        id: treePopupSizer

        host: control
    }

    // Row view model for the popup ListView: incremental mirror of `_flatModel`
    // 弹层 ListView 的行视图模型：`_flatModel` 的增量镜像（展开/折叠时只增删对应的行）
    ListModel {
        id: treeRowModel
    }
}
