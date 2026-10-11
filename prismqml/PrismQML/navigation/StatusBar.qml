// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."
import "../controls/containers"
import "../controls/data/Label"
import "../controls/icons"
import "../controls/feedback/Progress"
import "../controls/utils"

pragma ComponentBehavior: Bound

// StatusBar - Pure QtQuick implementation 状态栏纯QtQuick实现
// Display status info at window bottom 显示窗口底部状态信息
Rectangle {
    id: control

    // ==================== Public Props 公开属性 ====================
    property string message: ""
    property var leftItems: []  // Left items 左侧项
    property var rightItems: [] // Right items 右侧项
    property int level: -1  // Overall semantic level, -1 keeps neutral text 总体语义级别,-1保持中性文字
    property bool busy: false  // Indeterminate work state 是否正在执行不确定进度任务
    property real progress: -1  // Determinate progress 0..1, -1 hides the indicator 确定进度0..1,-1隐藏指示器
    property string accessibleName: ""  // Accessible group name 无障碍状态组名称

    // ==================== Readonly State 只读状态 ====================
    readonly property color _statusBarBackground: Enums.surfaceColor
    readonly property color _statusBarDividerColor: Enums.dividerColor
    readonly property color _statusBarTextColor: Enums.textColor.secondary
    readonly property var _safeLeftItems:
        leftItems === null || leftItems === undefined ? []
        : (typeof leftItems.length === "number" ? leftItems : [])
    readonly property var _safeRightItems:
        rightItems === null || rightItems === undefined ? []
        : (typeof rightItems.length === "number" ? rightItems : [])
    readonly property var _leftItemModel: _wrapItems(_safeLeftItems, "left")
    readonly property var _rightItemModel: _wrapItems(_safeRightItems, "right")
    readonly property bool _hasProgress: busy || progress >= 0
    readonly property real _progressValue: progress < 0
        ? 0 : Math.max(0, Math.min(1, progress))
    readonly property color _messageColor: _statusColor(level, _statusBarTextColor)
    readonly property string _accessibleGroupName: accessibleName !== ""
        ? accessibleName : message

    // ==================== Signals 信号 ====================
    signal itemClicked(int index, var item, string side)

    // ==================== Public Methods 公开方法 ====================
    function _isObject(item) {
        return item !== null && item !== undefined && typeof item === "object"
    }

    function _itemText(item) {
        var value = _isObject(item) ? item.text : item
        return value === null || value === undefined ? "" : String(value)
    }

    function _itemIcon(item) {
        if (!_isObject(item) || item.icon === null || item.icon === undefined) return ""
        return String(item.icon)
    }

    function _itemLevel(item) {
        return _isObject(item) && item.level !== undefined ? item.level : control.level
    }

    function _statusColor(levelValue, fallbackColor) {
        if (levelValue === null || levelValue === undefined) return fallbackColor
        if (typeof levelValue === "string") return Enums.statusLevel.getColor(levelValue)
        var numericLevel = Number(levelValue)
        return numericLevel >= Enums.statusLevel.info
            ? Enums.statusLevel.getColorByLevel(numericLevel) : fallbackColor
    }

    function _itemColor(item) {
        return _statusColor(_itemLevel(item), _statusBarTextColor)
    }

    function _itemTooltip(item) {
        if (!_isObject(item) || item.tooltip === null || item.tooltip === undefined) return ""
        return String(item.tooltip)
    }

    function _itemAccessibleName(item) {
        if (_isObject(item) && item.accessibleName) return String(item.accessibleName)
        return _itemText(item)
    }

    function _itemVisible(item) {
        if (_isObject(item) && item.visible === false) return false
        return _itemText(item) !== "" || _itemIcon(item) !== ""
    }

    function _itemEnabled(item) {
        return !_isObject(item) || item.enabled !== false
    }

    function _itemClickable(item) {
        return _isObject(item) && item.clickable === true && _itemEnabled(item)
    }

    function _wrapItems(items, side) {
        var wrapped = []
        for (var i = 0; i < items.length; ++i) {
            wrapped.push({ "value": items[i], "side": side })
        }
        return wrapped
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: parent ? parent.width : 400
    implicitHeight: Enums.controlSize.statusBarHeight
    color: control._statusBarBackground

    // ==================== Content 内容 ====================
    A11ySurface {
        target: control
        role: Enums.accessibility.role_group
        name: control._accessibleGroupName
        description: control.message
    }

    // Top separator 顶部分隔线
    Separator {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        lineColor: control._statusBarDividerColor
    }

    Item {
        id: contentArea

        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.bottomMargin: control._hasProgress ? Enums.controlSize.progressBarHeight : 0

        // Left content 左侧内容
        Row {
            id: leftContent

            property int cellCount: 1 + control._leftItemModel.length
            readonly property real cellWidth: cellCount > 0
                ? Math.max(0, (width - spacing * Math.max(0, cellCount - 1)) / cellCount)
                : 0

            anchors.left: parent.left
            anchors.right: rightContent.left
            anchors.rightMargin: Enums.spacing.m
            anchors.verticalCenter: parent.verticalCenter
            height: parent.height
            spacing: Enums.spacing.xl
            clip: true

            // Message text 消息文本
            Label {
                width: control.message !== "" ? leftContent.cellWidth : 0
                type: Enums.label.type_caption
                text: control.message
                color: control._messageColor
                visible: control.message !== ""
                elide: Text.ElideRight
            }

            // Instantiator lets the row own dynamic cells for stable geometry.
            // 使用 Instantiator 让行直接持有动态条目, 保持几何稳定。
            Instantiator {
                model: control._leftItemModel
                delegate: statusItemDelegate
                onObjectAdded: function(index, object) { object.parent = leftContent }
                onObjectRemoved: function(index, object) { object.parent = null }
            }
        }

        // Right content 右侧内容
        Row {
            id: rightContent

            property int cellCount: control._rightItemModel.length
            readonly property real cellWidth: cellCount > 0
                ? Math.max(0, (width - spacing * Math.max(0, cellCount - 1)) / cellCount)
                : 0

            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            width: Math.max(0, parent.width / 2)
            height: parent.height
            spacing: Enums.spacing.xl
            clip: true

            Instantiator {
                model: control._rightItemModel
                delegate: statusItemDelegate
                onObjectAdded: function(index, object) { object.parent = rightContent }
                onObjectRemoved: function(index, object) { object.parent = null }
            }
        }
    }

    // Progress indicator 进度指示器
    Progress {
        id: progressIndicator

        objectName: "statusBarProgress"
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: Enums.controlSize.progressBarHeight
        type: Enums.progress.type_bar
        from: 0
        to: 1
        value: control._progressValue
        indeterminate: control.busy
        error: control.level === Enums.statusLevel.error
        showText: false
        visible: control._hasProgress
    }

    A11ySurface {
        target: progressIndicator
        role: Enums.accessibility.role_progressbar
        name: control._accessibleGroupName
        description: control.message
        ignored: !progressIndicator.visible
    }

    // Shared structured item delegate 共享结构化条目委托
    Component {
        id: statusItemDelegate

        Widget {
            id: itemSurface

            required property var modelData
            required property int index

            readonly property var itemData: modelData ? modelData.value : null
            readonly property string side: modelData ? modelData.side : ""
            readonly property string itemText: control._itemText(itemData)
            readonly property string itemIcon: control._itemIcon(itemData)
            readonly property color itemColor: control._itemColor(itemData)
            readonly property bool itemVisible: control._itemVisible(itemData)
            readonly property bool itemEnabled: control._itemEnabled(itemData)
            readonly property bool itemClickable: control._itemClickable(itemData)
            readonly property bool _touchActive: Touch.feedback(hoverHandler.hovered, tapHandler.pressed)

            objectName: "statusBarItem_" + side + "_" + index
            visible: itemVisible
            enabled: itemEnabled
            contentWidth: (itemSurface.itemIcon !== ""
                ? Enums.iconSize.xs + contentRow.spacing : 0) + itemLabel.implicitWidth
            contentHeight: Enums.controlSize.statusBarHeight
            width: parent && parent.cellWidth !== undefined
                ? (itemSurface.itemVisible ? parent.cellWidth : 0) : implicitWidth
            toolTipText: control._itemTooltip(itemData)
            toolTipPosition: Enums.position.top

            A11ySurface {
                target: itemSurface
                role: itemClickable
                    ? Enums.accessibility.role_button
                    : Enums.accessibility.role_statictext
                name: control._itemAccessibleName(itemData)
                description: control._itemTooltip(itemData)
                ignored: !itemSurface.itemVisible
            }

            Rectangle {
                anchors.fill: parent
                radius: Enums.radius.small
                color: tapHandler.pressed ? Enums.stateColor.pressed : Enums.stateColor.hover
                visible: itemSurface.itemClickable && itemSurface._touchActive
            }

            Row {
                id: contentRow

                anchors.left: parent.left
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                spacing: itemSurface.itemIcon !== "" && itemSurface.itemText !== ""
                    ? Enums.spacing.s : 0

                Icon {
                    id: itemIcon

                    icon: itemSurface.itemIcon
                    iconSize: Enums.iconSize.xs
                    color: itemSurface.itemColor
                    visible: itemSurface.itemIcon !== ""
                    anchors.verticalCenter: parent.verticalCenter
                }

                Label {
                    id: itemLabel

                    type: Enums.label.type_caption
                    text: itemSurface.itemText
                    color: itemSurface.itemColor
                    visible: itemSurface.itemText !== ""
                    width: Math.max(0, itemSurface.width - itemIcon.width - contentRow.spacing)
                    elide: Text.ElideRight
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            HoverHandler {
                id: hoverHandler

                enabled: itemSurface.itemClickable
                cursorShape: Qt.PointingHandCursor
            }

            TapHandler {
                id: tapHandler

                enabled: itemSurface.itemClickable
                acceptedButtons: Qt.LeftButton
                onTapped: control.itemClicked(index, itemSurface.itemData, itemSurface.side)
            }
        }
    }
}
