// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../.."
import "../../../effects"
import QtQuick.Effects
import "../../data"
import "../../icons"
import "../../utils"
import ".."
import "../../containers"
import "../../containers/ScrollBar"
import "../../menus"
import "_internal"
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖
import QtQuick.Window  // 置于库import后:去前缀后保原生Window不被库覆盖

// ComboBoxMultiTree - Tree multi-select dropdown with search 带搜索的树形多选下拉框
// Extends ComboBoxCore for consistent styling 继承ComboBoxCore保持样式一致
ComboBoxCore {
    id: control

    // ==================== Public Props 公开属性 ====================
    property var selectedPaths: []  // Selected node paths 已选节点路径 [["root", "child"], ...]
    property string delimiter: ", "
    property int maxDisplay: 3  // Max items to display 最多显示数量
    property bool searchEnabled: true
    property string searchPlaceholder: {
        Translator._v
        return Translator.tr("placeholder_keyword")
    }

    // ==================== Internal Props 内部属性 ====================
    property var _expandedNodes: ({})
    property string _searchText: ""
    property real _targetX: 0
    property real _smoothContentX: 0

    // ==================== Readonly State 只读状态 ====================
    readonly property var _safeSelectedPaths: {
        var values = selectedPaths
        if (!values || typeof values.length !== "number") return []
        var result = []
        for (var i = 0; i < values.length; i++) {
            if (Array.isArray(values[i])) result.push(values[i])
        }
        return result
    }
    // Filter out parent nodes, only show leaf nodes in token 过滤父节点，token只显示叶子节点
    readonly property var _leafSelectedPaths: {
        var leaves = []
        for (var i = 0; i < _safeSelectedPaths.length; i++) {
            if (Array.isArray(_safeSelectedPaths[i]) && !_nodeHasChildren(_safeSelectedPaths[i])) {
                leaves.push(_safeSelectedPaths[i])
            }
        }
        return leaves
    }

    readonly property string displayText: {
        if (_leafSelectedPaths.length === 0) return ""
        var texts = []
        for (var i = 0; i < _leafSelectedPaths.length && i < maxDisplay; i++) {
            texts.push(_leafSelectedPaths[i][_leafSelectedPaths[i].length - 1])
        }
        var result = texts.join(delimiter)
        if (_leafSelectedPaths.length > maxDisplay) result += " +" + (_leafSelectedPaths.length - maxDisplay)
        return result
    }

    // ==================== Signals 信号 ====================
    signal selectionChanged(var paths)

    // ==================== Internal Methods 内部方法 ====================
    function _initTree() {
        if (_safeModel.length > 0) {
            _expandAllNodes()
            _rebuildFlatModel()
        }
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
        _flatListModel.clear()
        var searchText = _searchText.toLowerCase()
        _flattenTree(_safeModel, [], 0, "root", searchText)
    }

    // Get selection state for a node 获取节点的选中状态
    // Returns: 0=none, 1=partial, 2=all 返回：0=未选中，1=部分选中，2=全选
    function _getSelectionState(node, path) {
        if (!node.children || node.children.length === 0) {
            // Leaf node 叶子节点
            return _isSelected(path) ? 2 : 0
        }
        // Parent node: check all descendants 父节点：检查所有后代
        var leafPaths = _getLeafPaths(node, path)
        var selectedCount = 0
        for (var i = 0; i < leafPaths.length; i++) {
            if (_isSelected(leafPaths[i])) selectedCount++
        }
        if (selectedCount === 0) return 0
        if (selectedCount === leafPaths.length) return 2
        return 1
    }

    function _flattenTree(nodes, parentPath, depth, parentId, searchText) {
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

            // Check if any children match search 检查子节点是否匹配搜索
            var hasMatchingChildren = false
            if (!matchesSearch && hasChildren) {
                hasMatchingChildren = _hasMatchingDescendants(node.children, searchText)
            }

            // Calculate selection state 计算选中状态
            var selectionState = _getSelectionState(node, path)

            if (matchesSearch || hasMatchingChildren || !_searchText) {
                _flatListModel.append({
                    text: nodeText,
                    depth: depth,
                    nodeId: nodeId,
                    path: JSON.stringify(path),  // ListModel needs primitive types ListModel需要基本类型
                    hasChildren: hasChildren,
                    expanded: expanded,
                    selected: selectionState === 2,
                    isPartialSelected: selectionState === 1
                })
            }

            // Add children if expanded 如果展开则添加子节点
            if (hasChildren && expanded) {
                _flattenTree(node.children, path, depth + 1, nodeId, searchText)
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

    function _pathToString(path) {
        return path.join("→")
    }

    function _isSelected(path) {
        var pathStr = _pathToString(path)
        for (var i = 0; i < _safeSelectedPaths.length; i++) {
            if (_pathToString(_safeSelectedPaths[i]) === pathStr) return true
        }
        return false
    }

    // Find node by path 根据路径查找节点
    function _findNodeByPath(path) {
        if (!path || path.length === 0 || _safeModel.length === 0) return null
        var nodes = _safeModel
        var node = null
        for (var i = 0; i < path.length; i++) {
            var found = false
            for (var j = 0; j < nodes.length; j++) {
                var n = nodes[j]
                if (!n) continue
                var text = typeof n === "string" ? n : (n.text || "")
                if (text === path[i]) {
                    node = n
                    nodes = n.children || []
                    found = true
                    break
                }
            }
            if (!found) return null
        }
        return node
    }

    // Get all leaf paths under a node 获取节点下所有叶子节点路径
    function _getLeafPaths(node, currentPath) {
        var leaves = []
        if (!node) return leaves
        var children = node.children
        if (!children || children.length === 0) {
            // This is a leaf node 这是叶子节点
            leaves.push(currentPath.slice())
        } else {
            // Recurse into children 递归子节点
            for (var i = 0; i < children.length; i++) {
                var child = children[i]
                if (!child) continue
                var childText = typeof child === "string" ? child : (child.text || "")
                var childPath = currentPath.concat([childText])
                var childLeaves = _getLeafPaths(child, childPath)
                for (var j = 0; j < childLeaves.length; j++) {
                    leaves.push(childLeaves[j])
                }
            }
        }
        return leaves
    }

    // Check if node has children 检查节点是否有子节点
    function _nodeHasChildren(path) {
        var node = _findNodeByPath(path)
        return node && node.children && node.children.length > 0
    }

    function _toggleSelection(path) {
        var node = _findNodeByPath(path)
        var hasChildren = node && node.children && node.children.length > 0

        if (hasChildren) {
            // Parent node: toggle all leaf descendants 父节点：切换所有叶子后代
            var leafPaths = _getLeafPaths(node, path)
            var allSelected = true
            for (var i = 0; i < leafPaths.length; i++) {
                if (!_isSelected(leafPaths[i])) {
                    allSelected = false
                    break
                }
            }

            var newPaths = _safeSelectedPaths.slice()
            if (allSelected) {
                // Deselect all leaves 取消选中所有叶子
                for (var i = 0; i < leafPaths.length; i++) {
                    var leafStr = _pathToString(leafPaths[i])
                    newPaths = newPaths.filter(function(p) { return _pathToString(p) !== leafStr })
                }
            } else {
                // Select all leaves 选中所有叶子
                for (var i = 0; i < leafPaths.length; i++) {
                    if (!_isSelected(leafPaths[i])) {
                        newPaths.push(leafPaths[i].slice())
                    }
                }
            }
            selectedPaths = newPaths
        } else {
            // Leaf node: toggle single 叶子节点：切换单个
            var pathStr = _pathToString(path)
            var newPaths = []
            var found = false
            for (var i = 0; i < _safeSelectedPaths.length; i++) {
                if (_pathToString(_safeSelectedPaths[i]) === pathStr) {
                    found = true
                } else {
                    newPaths.push(_safeSelectedPaths[i])
                }
            }
            if (!found) newPaths.push(path.slice())
            selectedPaths = newPaths
        }

        selectionChanged(selectedPaths)
        _updateSelectionStates()  // Only update selection states, not rebuild 只更新选中状态，不重建
    }

    // Update selection states in ListModel without rebuilding 更新ListModel中的选中状态而不重建
    function _updateSelectionStates() {
        for (var i = 0; i < _flatListModel.count; i++) {
            var item = _flatListModel.get(i)
            var path = JSON.parse(item.path)
            var node = _findNodeByPath(path)
            var selectionState = _getSelectionState(node, path)
            _flatListModel.setProperty(i, "selected", selectionState === 2)
            _flatListModel.setProperty(i, "isPartialSelected", selectionState === 1)
        }
    }

    // ==================== Public Methods 公开方法 ====================
    function smoothScrollTo(x) {
        _targetX = Math.max(0, Math.min(x, tokenFlickable.contentWidth - tokenFlickable.width))
        _smoothContentX = _targetX
    }

    function openPopup() {
        _rebuildFlatModel()
        _popup.popupWidth = Math.max(control.width, Enums.comboBoxMetrics.treePopupMinWidth)
        _popup.popupHeight = Enums.comboBoxMetrics.treePopupHeight
        _popup.openAtControl(control)
        isOpen = true
        _searchText = ""
    }

    // Base property overrides 基类属性覆盖
    showFocusedBorder: false  // No focus line for multi-tree 多选树不显示聚焦下划线
    useDefaultContent: false
    // Only intercept wheel when content overflows 仅当内容溢出时拦截滚轮
    acceptWheel: tokenFlickable.contentWidth > tokenFlickable.width

    // ==================== Size 尺寸 ====================
    implicitWidth: 280

    // Popup content override 弹窗内容覆盖
    popupContent: Component {
        Column {
            anchors.fill: parent
            spacing: Enums.spacing.none

            // Search box 搜索框
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
                    model: control._flatListModel

                    delegate: TreeMenuDelegate {
                        width: treeListView.width
                        text: model.text
                        depth: model.depth
                        hasChildren: model.hasChildren
                        expanded: model.expanded
                        checkable: true
                        checkState: model.selected ? 2 : (model.isPartialSelected ? 1 : 0)

                        onToggleExpand: control._toggleExpand(model.nodeId)
                        onCheckToggled: control._toggleSelection(JSON.parse(model.path))
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
                    active: treeContainer.needsScroll
                    sourceComponent: ScrollBarEntry {
                        flickable: treeListView
                        width: Enums.comboBoxMetrics.scrollBarWidth
                    }
                }
            }
        }
    }

    Behavior on _smoothContentX { NumberAnimation { duration: Enums.duration.medium; easing.type: Easing.OutCubic } }

    // Keep the flattened model synchronized with source and filters.
    // 保持扁平模型与源数据及筛选条件同步。
    Component.onCompleted: _initTree()
    onModelChanged: _initTree()
    on_ExpandedNodesChanged: _rebuildFlatModel()
    on_SearchTextChanged: _rebuildFlatModel()
    on_SmoothContentXChanged: tokenFlickable.contentX = _smoothContentX

    // Use base class wheel signal 使用基类滚轮信号
    onWheelScrolled: (delta) => smoothScrollTo(_targetX - delta * 0.8)

    // ==================== Content 内容 ====================
    // Use ListModel for animation support 使用ListModel以支持动画
    property alias _flatListModel: _internalFlatListModel
    ListModel {
        id: _internalFlatListModel
    }

    // Token Display Area 标签显示区域 (use base class arrow) 使用基类箭头
    Flickable {
        id: tokenFlickable
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: Enums.spacing.m
        anchors.rightMargin: Enums.comboBoxMetrics.arrowAreaWidth
        height: Enums.spacing.xxxl
        contentWidth: tokenRow.width
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        flickableDirection: Flickable.HorizontalFlick
        interactive: false  // Disable drag, use wheel only 禁用拖拽，仅用滚轮

        Row {
            id: tokenRow
            height: Enums.spacing.xxxl
            spacing: Enums.spacing.xs

            // Placeholder text 占位符文本
            Label {
                type: Enums.label.type_body
                text: control.placeholderText
                color: Enums.textColor.disabled
                visible: control._leafSelectedPaths.length === 0
                anchors.verticalCenter: parent.verticalCenter
            }

            // Token tags 标签 (only show leaf nodes 只显示叶子节点)
            Repeater {
                model: control._leafSelectedPaths

                delegate: MultiSelectToken {
                    id: tokenDelegate
                    required property int index
                    required property var modelData

                    readonly property var _control: control  // Capture control reference 捕获control引用

                    text: modelData[modelData.length - 1] || ""
                    tokenIndex: index
                    anchors.verticalCenter: parent.verticalCenter

                    onRemoveClicked: (idx) => {
                        // Find the path in selectedPaths by matching 通过匹配在selectedPaths中找到路径
                        var pathToRemove = tokenDelegate._control._leafSelectedPaths[idx]
                        var pathStr = tokenDelegate._control._pathToString(pathToRemove)
                        var newPaths = tokenDelegate._control._safeSelectedPaths.filter(function(p) {
                            return tokenDelegate._control._pathToString(p) !== pathStr
                        })
                        tokenDelegate._control.selectedPaths = newPaths
                        tokenDelegate._control.selectionChanged(tokenDelegate._control._safeSelectedPaths)
                        tokenDelegate._control._updateSelectionStates()
                    }
                }
            }
        }
    }

}
