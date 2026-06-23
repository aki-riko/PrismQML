// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

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
    
    // ==================== Tree Specific Props 树特有属性 ====================
    property bool searchEnabled: true
    property string searchPlaceholder: "请输入关键字"
    property string delimiter: " → "
    property bool showPathFromRoot: true
    
    // ==================== Override Base Props 覆盖基类属性 ====================
    showFocusedBorder: false  // No focus line for tree 树不显示聚焦下划线
    
    // ==================== Signals 信号 ====================
    signal itemSelected(string text, var path)
    
    // ==================== Internal State 内部状态 ====================
    property var _expandedNodes: ({})
    property string _searchText: ""
    property var _flatModel: []
    property bool _initialized: false
    
    // ==================== Flatten Tree Model 扁平化树模型 ====================
    Component.onCompleted: _initTree()
    onModelChanged: _initTree()
    on_ExpandedNodesChanged: _rebuildFlatModel()
    on_SearchTextChanged: _rebuildFlatModel()
    
    function _initTree() {
        if (model && model.length > 0) {
            _expandAllNodes()
            _rebuildFlatModel()
        }
    }
    
    function _expandAllNodes() {
        var expanded = {}
        _collectExpandableNodes(model, "root", expanded)
        _expandedNodes = expanded
    }
    
    function _collectExpandableNodes(nodes, parentId, result) {
        if (!nodes) return
        for (var i = 0; i < nodes.length; i++) {
            var node = nodes[i]
            var nodeId = parentId + "_" + i
            if (node.children && node.children.length > 0) {
                result[nodeId] = true
                _collectExpandableNodes(node.children, nodeId, result)
            }
        }
    }
    
    function _rebuildFlatModel() {
        var flat = []
        _flattenTree(model, [], 0, "root", flat)
        _flatModel = flat
    }
    
    function _flattenTree(nodes, parentPath, depth, parentId, result) {
        if (!nodes) return
        for (var i = 0; i < nodes.length; i++) {
            var node = nodes[i]
            var nodeText = typeof node === "string" ? node : (node.text || "")
            var nodeId = parentId + "_" + i
            var path = parentPath.concat([nodeText])
            var hasChildren = !!(node.children && node.children.length > 0)
            var expanded = !!_expandedNodes[nodeId]
            var matchesSearch = !_searchText || nodeText.toLowerCase().indexOf(_searchText.toLowerCase()) >= 0
            
            var hasMatchingChildren = false
            if (!matchesSearch && hasChildren) hasMatchingChildren = _hasMatchingDescendants(node.children)
            
            if (matchesSearch || hasMatchingChildren || !_searchText) {
                result.push({ text: nodeText, depth: depth, nodeId: nodeId, path: path, hasChildren: hasChildren, expanded: expanded })
            }
            
            if (hasChildren && expanded) _flattenTree(node.children, path, depth + 1, nodeId, result)
        }
    }
    
    function _hasMatchingDescendants(children) {
        if (!children) return false
        for (var i = 0; i < children.length; i++) {
            var child = children[i]
            var text = typeof child === "string" ? child : (child.text || "")
            if (text.toLowerCase().indexOf(_searchText.toLowerCase()) >= 0) return true
            if (child.children && _hasMatchingDescendants(child.children)) return true
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
    
    // ==================== Override Size 覆盖尺寸 ====================
    implicitWidth: 200
    
    // ==================== Override Popup Content 覆盖弹出内容 ====================
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
                width: parent.width
                height: parent.height - (control.searchEnabled ? Enums.comboBoxMetrics.searchBoxHeight : 0)
                
                readonly property bool needsScroll: treeListView.contentHeight > treeListView.height
                
                ListView {
                    id: treeListView
                    anchors.fill: parent
                    anchors.rightMargin: treeContainer.needsScroll ? Enums.comboBoxMetrics.scrollBarRightMargin : 0
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds
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
    
    // ==================== Override Popup Open 覆盖弹出打开 ====================
    function openPopup() {
        _rebuildFlatModel()
        _popup.popupWidth = Math.max(control.width, 200)
        // Set reference width for center alignment 设置参考宽度用于居中对齐
        _popup.referenceControlWidth = control.width
        var itemCount = _flatModel.length
        var searchHeight = searchEnabled ? Enums.comboBoxMetrics.searchBoxHeight : 0
        _popup.popupHeight = Math.min(itemCount * Enums.comboBoxMetrics.itemHeight + searchHeight + Enums.spacing.m, Enums.comboBoxMetrics.treePopupHeight)
        _popup.openAtControl(control)
        isOpen = true
    }
}
