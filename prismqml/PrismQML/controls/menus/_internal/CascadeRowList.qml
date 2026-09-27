// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick as Native
import "../../.."
import "../../containers/ScrollBar"
// The search field is shared with the ComboBox series rather than duplicated: a
// cascade level's search box must behave exactly like a dropdown's.
// 搜索框与 ComboBox 系列共用而非复制: 级联层的搜索框行为必须与下拉框完全一致。
import "../../inputs/ComboBox/_internal"

// CascadeRowList - One cascade level's rows 级联结构单层的行列表
// Owns how a level looks and scrolls; it never owns a window. The root level renders
// inside its host popup, every deeper level inside its own popup surface, so both hosts
// share exactly this rendering and nothing else.
// 持有单层的呈现与滚动, 从不持有窗口。根层渲染在宿主弹层内, 更深层级渲染在各自的弹层
// 表面内, 因此两种宿主只共享这份呈现, 不共享其他任何东西。
Item {
    id: rowList

    // ==================== Public Props 公开属性 ====================
    property var rows: []                    // Rows owned by this level 本层持有的行数据
    property int currentIndex: -1            // Host selection for indicator mirror 宿主选中下标
    property bool withSearch: false          // Root level only 仅根层
    property bool arrowFollowsChildren: false // Root draws arrows, deeper levels keep the column 根层绘制箭头
    property string searchPlaceholder: {
        Translator._v
        return Translator.tr("placeholder_keyword")
    }
    property int rowHeight: Enums.comboBoxMetrics.itemHeight
    property int maxHeight: Enums.comboBoxMetrics.treePopupHeight
    // Delegates are registered into a registry owned by the host, because a host that
    // lives in another component cannot resolve an id declared inside this component.
    // 委托注册到宿主持有的注册表: 位于其他组件中的宿主无法解析本组件内声明的 id。
    property var hostRegistry: null

    // ==================== Internal Props 内部属性 ====================
    property var _rowDelegates: ({})
    // Measured below instead of bound: a binding would read a width that this value
    // itself sizes, which QML reports as a binding loop.
    // 在下方显式测量而不使用绑定: 绑定会读取由本值决定的宽度, QML 会判为绑定循环。
    property int _contentWidth: 0
    // Arrow glyph and its gutters stay reserved even when no arrow is drawn, so a
    // deeper level keeps the root level text column. 即使不绘制箭头也保留箭头字形与边距,
    // 使更深层级保持根层的文本列。
    readonly property int _arrowReserve:
        Enums.iconSize.xs + Enums.spacing.s + Enums.spacing.l
    readonly property int _searchReserve:
        withSearch ? Enums.comboBoxMetrics.searchBoxHeight : 0

    // ==================== Readonly State 只读状态 ====================
    readonly property int listHeight: rows.length * rowHeight
    readonly property int preferredWidth: Math.max(
        Enums.comboBoxMetrics.minPopupWidth,
        _contentWidth
            + (rows.length > 0 && rows[0].icon !== "" ? Enums.iconSize.m + Enums.spacing.m : 0)
            + _arrowReserve + 2 * Enums.spacing.l)
    readonly property int preferredHeight: Math.min(
        listHeight + _searchReserve,
        Math.max(0, maxHeight))
    readonly property bool needsScroll:
        listHeight + _searchReserve > Math.max(0, maxHeight)

    // ==================== Signals 信号 ====================
    signal rowClicked(int index, var path)
    signal rowHoverChanged(int index, bool hovered)
    signal submenuRequested(int index)
    signal searchTextChanged(string text)

    // ==================== Internal Methods 内部方法 ====================
    function _measureRows() {
        var widest = 0
        for (var i = 0; i < rows.length; i++) {
            rowMeasure.text = rows[i].text || ""
            if (rowMeasure.advanceWidth > widest) widest = rowMeasure.advanceWidth
        }
        _contentWidth = Math.ceil(widest)
    }

    function rowDelegate(index) {
        if (hostRegistry) {
            var shared = hostRegistry[index]
            if (shared) return shared
        }
        return _rowDelegates[index] ? _rowDelegates[index] : null
    }

    function _registerRow(index, delegate) {
        _rowDelegates[index] = delegate
        if (hostRegistry) hostRegistry[index] = delegate
    }

    function _unregisterRow(index, delegate) {
        if (_rowDelegates[index] === delegate) delete _rowDelegates[index]
        if (hostRegistry && hostRegistry[index] === delegate) delete hostRegistry[index]
    }

    function clearRowDelegates() {
        _rowDelegates = ({})
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: preferredWidth
    implicitHeight: preferredHeight

    onRowsChanged: Qt.callLater(_measureRows)
    Component.onCompleted: Qt.callLater(_measureRows)

    // ==================== Content 内容 ====================
    TextMetrics {
        id: rowMeasure
        font.family: Enums.fontFamily
        font.pixelSize: Enums.typography.body
    }

    Column {
        anchors.fill: parent
        spacing: Enums.spacing.none

        PopupSearchBox {
            id: searchBox

            width: parent.width
            searchEnabled: rowList.withSearch
            placeholderText: rowList.searchPlaceholder
            onSearchTextChanged: (text) => rowList.searchTextChanged(text)
        }

        Item {
            id: listContainer

            width: parent.width
            height: parent.height - rowList._searchReserve

            // Qualified through the alias: the PrismQML module registers its own
            // `ListView` (a framed data list) which shadows the native view here.
            // 经别名限定: PrismQML 模块注册了自有 ListView（带边框的数据列表）,
            // 它在本作用域遮蔽了原生视图。
            Native.ListView {
                id: listView

                anchors.fill: parent
                anchors.rightMargin: listContainer.width > 0 && rowList.needsScroll
                    ? Enums.comboBoxMetrics.scrollBarRightMargin : 0
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                // Disable native scroll, use smooth scroll 禁用原生滚动，使用平滑滚动
                interactive: false
                model: rowList.rows

                delegate: CascadeItemDelegate {
                    width: listView.width
                    text: modelData.text
                    icon: modelData.icon
                    itemEnabled: modelData.enabled
                    itemIndex: index
                    hasChildren: modelData.children && modelData.children.length > 0
                    selected: rowList.currentIndex === index

                    Component.onCompleted: rowList._registerRow(index, this)
                    Component.onDestruction: rowList._unregisterRow(index, this)

                    onHoverChanged: rowList.rowHoverChanged(index, hovered)
                    onClicked: rowList.rowClicked(index, modelData.path)
                    onSubmenuRequested: rowList.submenuRequested(index)
                }

                // Smooth scroll 平滑滚动
                PopupSmoothScroll { flickable: listView; enabled: rowList.needsScroll }
            }

            Loader {
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.margins: Enums.spacing.xxs
                width: Enums.comboBoxMetrics.scrollBarWidth
                active: rowList.needsScroll
                sourceComponent: ScrollBarEntry {
                    flickable: listView
                    width: Enums.comboBoxMetrics.scrollBarWidth
                }
            }
        }
    }
}
