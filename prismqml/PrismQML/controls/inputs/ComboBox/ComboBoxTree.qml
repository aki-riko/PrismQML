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
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

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

    // ==================== Signals 信号 ====================
    signal itemSelected(string text, var path)

    // ==================== Public Methods 公开方法 ====================
    function openPopup() {
        _rebuildFlatModel()
        _popup.popupWidth = Math.max(control.width, Enums.comboBoxMetrics.treePopupMinWidth)
        var itemCount = _flatModel.length
        var searchHeight = searchEnabled ? Enums.comboBoxMetrics.searchBoxHeight : 0
        _popup.implicitContentHeight = Math.min(
            itemCount * Enums.comboBoxMetrics.itemHeight + searchHeight,
            Math.max(0, Enums.comboBoxMetrics.treePopupHeight
                - 2 * _popup.contentPadding))
        _popup.openAtControl(control)
        isOpen = true
    }

    // ==================== Internal Methods 内部方法 ====================
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
    
    function _expandAllNodes() {
        var expanded = {}
        _collectExpandableNodes(_safeModel, "root", expanded)
        _expandedNodes = expanded
    }
    
    function _collectExpandableNodes(nodes, parentId, result) {
        if (!nodes) return
        for (var i = 0; i < nodes.length; i++) {
            var node = nodes[i]
            if (!node) continue
            var nodeId = parentId + "_" + i
            if (node.children && node.children.length > 0) {
                result[nodeId] = true
                _collectExpandableNodes(node.children, nodeId, result)
            }
        }
    }
    
    function _rebuildFlatModel() {
        var flat = []
        var searchText = _searchText.toLowerCase()
        _flattenTree(_safeModel, [], 0, "root", flat, searchText)
        _flatModel = flat
    }
    
    function _flattenTree(nodes, parentPath, depth, parentId, result, searchText) {
        if (!nodes) return
        for (var i = 0; i < nodes.length; i++) {
            var node = nodes[i]
            if (!node) continue
            var nodeText = typeof node === "string" ? node : (node.text || "")
            var nodeId = parentId + "_" + i
            var path = parentPath.concat([nodeText])
            var hasChildren = !!(node.children && node.children.length > 0)
            var expanded = !!_expandedNodes[nodeId]
            var matchesSearch = !searchText || nodeText.toLowerCase().indexOf(searchText) >= 0
            
            var hasMatchingChildren = false
            if (!matchesSearch && hasChildren) {
                hasMatchingChildren = _hasMatchingDescendants(node.children, searchText)
            }
            
            if (matchesSearch || hasMatchingChildren || !_searchText) {
                result.push({ text: nodeText, depth: depth, nodeId: nodeId, path: path, hasChildren: hasChildren, expanded: expanded })
            }
            
            if (hasChildren && expanded) {
                _flattenTree(node.children, path, depth + 1, nodeId, result, searchText)
            }
        }
    }
    
    function _hasMatchingDescendants(children, searchText) {
        if (!children) return false
        for (var i = 0; i < children.length; i++) {
            var child = children[i]
            if (!child) continue
            var text = typeof child === "string" ? child : (child.text || "")
            if (text.toLowerCase().indexOf(searchText) >= 0) return true
            if (child.children
                    && _hasMatchingDescendants(child.children, searchText)) return true
        }
        return false
    }
    
    function _toggleExpand(nodeId) {
        var newExpanded = Object.assign({}, _expandedNodes)
        newExpanded[nodeId] = !newExpanded[nodeId]
        _expandedNodes = newExpanded
    }
    
    function _getPathText(path) {
        return showPathFromRoot ? path.join(delimiter) : path[path.length - 1]
    }
    
    function _selectNode(nodeText, path) {
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

    // ==================== Content 内容 ====================
    popupContent: Component {
        Column {
            anchors.fill: parent
            spacing: Enums.spacing.none
            
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
}
