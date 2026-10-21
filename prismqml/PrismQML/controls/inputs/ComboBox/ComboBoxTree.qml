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
    property real _animatedPopupContentHeight: 0

    // ==================== Readonly State 只读状态 ====================
    readonly property bool _popupHeightAnimating: popupHeightAnimation.running

    // ==================== Signals 信号 ====================
    signal itemSelected(string text, var path)

    // ==================== Public Methods 公开方法 ====================
    function openPopup() {
        _rebuildFlatModel()
        _popup.popupWidth = Math.max(control.width, Enums.comboBoxMetrics.treePopupMinWidth)
        _popup.openAtControl(control)
        isOpen = true
    }

    // ==================== Internal Methods 内部方法 ====================
    function _updatePopupContentHeight() {
        var itemCount = _flatModel.length
        var searchHeight = searchEnabled ? Enums.comboBoxMetrics.searchBoxHeight : 0
        var targetHeight = Math.min(
            itemCount * Enums.comboBoxMetrics.itemHeight + searchHeight,
            Math.max(0, Enums.comboBoxMetrics.treePopupHeight
                - 2 * _popup.contentPadding))
        popupHeightAnimation.stop()
        if (!isOpen || _animatedPopupContentHeight === targetHeight) {
            _animatedPopupContentHeight = targetHeight
            return
        }
        popupHeightAnimation.from = _animatedPopupContentHeight
        popupHeightAnimation.to = targetHeight
        popupHeightAnimation.start()
    }

    function _syncOpenPopupGeometry() {
        _popup.stabilizeInteraction()
        _popup._clipHeight = _popup.popupHeight
        var popupWindow = _popup._popupWindow
        if (!popupWindow) return
        popupWindow.width = _popup._outerWidth
        popupWindow.height = _popup._outerHeight
        _popup._applyTrackedPosition(control.mapToGlobal(0, 0))
        var bounds = _popup._screenBoundsAt(popupWindow.x, popupWindow.y, control)
        if (!bounds) return
        popupWindow.x = Math.max(
            bounds.left,
            Math.min(popupWindow.x, bounds.right - _popup._outerWidth)
        )
        popupWindow.y = Math.max(
            bounds.top,
            Math.min(popupWindow.y, bounds.bottom - _popup._outerHeight)
        )
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
        _updatePopupContentHeight()
    }

    function _toggleExpand(nodeId) {
        _expandedNodes = TreeNodes.toggleExpanded(_expandedNodes, nodeId)
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
    on_AnimatedPopupContentHeightChanged: {
        _popup.implicitContentHeight = Math.round(_animatedPopupContentHeight)
        if (isOpen) _syncOpenPopupGeometry()
    }
    onIsOpenChanged: {
        if (!isOpen) popupHeightAnimation.stop()
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

                readonly property bool needsScroll: treeListView.contentHeight > treeListView.height

                width: parent.width
                height: parent.height - (control.searchEnabled ? Enums.comboBoxMetrics.searchBoxHeight : 0)

                ListView {
                    id: treeListView
                    anchors.fill: parent
                    anchors.rightMargin: treeContainer.needsScroll ? Enums.comboBoxMetrics.scrollBarRightMargin : 0
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds
                    interactive: false  // Disable native scroll, use smooth scroll 禁用原生滚动，使用平滑滚动
                    model: control._flatModel
                    
                    delegate: TreeMenuDelegate {
                        width: treeListView.width
                        text: modelData.text
                        depth: modelData.depth
                        hasChildren: modelData.hasChildren
                        expanded: modelData.expanded
                        checkable: false
                        
                        onToggleExpand: control._toggleExpand(modelData.nodeId)
                        onClicked: control._selectNode(modelData.text, modelData.path)
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

    NumberAnimation {
        id: popupHeightAnimation

        target: control
        property: "_animatedPopupContentHeight"
        duration: Enums.duration.fast
        easing.type: Easing.OutCubic
    }
}
