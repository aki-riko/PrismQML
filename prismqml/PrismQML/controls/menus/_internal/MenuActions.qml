// MenuActions - Imperative menu item operations 菜单命令式项目操作
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

QtObject {
    id: operations

    required property var host
    required property var itemContainer
    required property Component separatorFactory
    required property Component mouseAreaFactory

    function addWidget(widget, selectable, onClick) {
        if (!widget) return
        widget.parent = itemContainer
        host._registerMenuItem(widget)
        widget.width = Qt.binding(function() { return itemContainer.width })
        if (selectable && onClick) {
            mouseAreaFactory.createObject(widget, {
                "anchors.fill": widget,
                "onClicked": onClick
            })
        }
        Qt.callLater(host._updateSize)
    }

    function addSeparator() {
        var separator = separatorFactory.createObject(itemContainer)
        host._registerMenuItem(separator)
        Qt.callLater(host._updateSize)
    }

    function addActions(actionsArray) {
        var actions = actionsArray && typeof actionsArray.length === "number" ? actionsArray : []
        for (var i = 0; i < actions.length; i++) {
            var action = actions[i]
            if (action) host.addAction(action.text, action.icon, action.shortcut, action)
        }
    }

    function getAction(actionId) {
        var items = host._menuItems()
        for (var i = 0; i < items.length; i++) {
            var child = items[i]
            if (child && child.actionId === actionId) return child
        }
        return null
    }

    function updateAction(actionId, props) {
        var action = getAction(actionId)
        if (!action) return false
        if (props.text !== undefined) action.text = props.text
        if (props.icon !== undefined) action.icon = props.icon
        if (props.shortcut !== undefined) action.shortcut = props.shortcut
        if (props.checkable !== undefined) action.checkable = props.checkable
        if (props.checked !== undefined) action.checked = props.checked
        if (props.enabled !== undefined) action.enabled = props.enabled
        if (props.toolTip !== undefined) action.toolTip = props.toolTip
        Qt.callLater(host._updateSize)
        return true
    }

    function removeAction(actionId) {
        var action = getAction(actionId)
        if (!action) return false
        host._unregisterMenuItem(action)
        action.destroy()
        Qt.callLater(host._updateSize)
        return true
    }

    function addSubmenu(text, icon, submenuComponent) {
        var action = host.addAction(text, icon, "", { "hasSubmenu": true })
        return host._bindSubmenuAction(action, submenuComponent, {})
    }

    function addSubmenuActions(text, icon, actionsArray) {
        var action = host.addAction(text, icon, "", {
            "actionId": "_submenu_" + text,
            "hasSubmenu": true
        })
        var submenuComponent = host._createDataSubmenuComponent()
        return host._bindSubmenuAction(action, submenuComponent, {
            "initialActions": actionsArray || []
        })
    }

    function leafPath(actionId) {
        var id = String(actionId)
        if (id.indexOf("leaf:") !== 0) return null
        return id.slice(5).split("\u0001")
    }

    function addNodes(nodes, basePath) {
        var created = []
        var list = nodes && typeof nodes.length === "number" ? nodes : []
        var prefix = basePath || []
        for (var i = 0; i < list.length; i++) {
            var node = list[i]
            if (node === null || node === undefined) continue
            var isText = typeof node === "string"
            var text = isText ? node : (node.text || "")
            var icon = isText ? "" : (node.icon || "")
            var enabled = isText ? true : (node.enabled === undefined ? true : !!node.enabled)
            var path = prefix.concat([text])
            var children = isText ? null : node.children
            if (children && typeof children.length === "number" && children.length > 0) {
                var owner = host.addAction(text, icon, "", {
                    "hasSubmenu": true,
                    "enabled": enabled
                })
                if (!owner) continue
                owner._submenuData = { "nodes": children, "basePath": path }
                host._bindSubmenuAction(owner, null, {})
                created.push(owner)
                continue
            }
            var leaf = host.addAction(text, icon, "", {
                "actionId": "leaf:" + path.join("\u0001"),
                "enabled": enabled
            })
            if (leaf) created.push(leaf)
        }
        Qt.callLater(host._updateSize)
        return created
    }
}
