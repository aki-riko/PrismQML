// ComboBoxCascade - External and model-backed menu ownership 下拉级联菜单所有者
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../menus"

Item {
    id: cascade

    required property var comboControl
    readonly property var menu: cascadeMenuLoader.item

    width: 0
    height: 0
    visible: true

    function modelHasChildren(values) {
        var items = values === null || values === undefined ? [] : values
        if (typeof items.length !== "number") return false
        for (var i = 0; i < items.length; i++) {
            var item = items[i]
            if (item && typeof item === "object"
                    && item.children && typeof item.children.length === "number"
                    && item.children.length > 0) return true
        }
        return false
    }

    function sync() {
        var control = comboControl
        if (!menu || !modelHasChildren(control._safeModel)
                || control._cascadeSyncedRevision === control._cascadeModelRevision) return
        if (menu.isOpen) menu.close()
        menu.clear()
        menu.addNodes(control._safeModel, [])
        control._cascadeSyncedRevision = control._cascadeModelRevision
    }

    function menuIndexForPath(path) {
        var control = comboControl
        if (!path || path.length === 0) return -1
        for (var i = 0; i < control._safeModel.length; i++) {
            if (control._getItemText(i) === path[0]) return i
        }
        return -1
    }

    function openPopup() {
        var control = comboControl
        if (control.isOpen) return
        if (control._useExternalMenu()) {
            control.menu.openAtControl(control)
            control.isOpen = true
            return
        }
        if (modelHasChildren(control._safeModel)) {
            sync()
            if (menu) {
                menu.openAtControl(control)
                control.isOpen = true
                return
            }
        }

        control._popupContentRequested = true
        var contentWidth = control._calcContentWidth()
        control._popup.popupWidth = control.popupWidthOverride > 0
            ? control.popupWidthOverride : Math.max(contentWidth, control.width)
        var itemCount = control._search.visibleModel.length
        var maxContentHeight = control.maxVisibleItems > 0
            ? control.maxVisibleItems * control.popupItemHeight
            : Math.max(0, Enums.comboBoxMetrics.popupMaxHeight
                - 2 * control._popup.contentPadding)
        control._popup.implicitContentHeight = Math.min(
            itemCount * control.popupItemHeight, maxContentHeight)
        control._popup.openAtControl(control)
        control.isOpen = true
        console.log("CASCADE_OPEN_DONE", control.isOpen, control._popup.isOpen, control._popup.isClosing)
    }

    function closePopup() {
        var control = comboControl
        if (control._useExternalMenu()) {
            if (typeof control.menu.close === "function") control.menu.close()
            if (control.isOpen) control.isOpen = false
            return
        }
        if (modelHasChildren(control._safeModel)) {
            if (menu && menu.isOpen) menu.close()
            control._popup.close()
            if (control.isOpen) control.isOpen = false
            return
        }
        if (!control.isOpen) return
        control._popup.close()
        control.isOpen = false
    }

    function onMenuAction(sourceMenu, actionId) {
        var control = comboControl
        var picked = sourceMenu && typeof sourceMenu.leafPath === "function"
            ? sourceMenu.leafPath(actionId) : null
        if (picked === null) return
        control.currentText = picked.length > 0 ? picked[picked.length - 1] : ""
        var selectedIndex = menuIndexForPath(picked)
        if (selectedIndex >= 0) control.currentIndex = selectedIndex
        if (sourceMenu && typeof sourceMenu.close === "function") sourceMenu.close()
        if (control.isOpen) control.isOpen = false
        control.textActivated(control.currentText)
    }

    Loader {
        id: cascadeMenuLoader
        active: cascade.modelHasChildren(cascade.comboControl._safeModel)

        sourceComponent: MenuCore {
            useQtPopupWindow: true
            closeOnClickOutside: cascade.comboControl.popupCloseOnClickOutside
        }
    }

    Connections {
        function onActionTriggered(actionId) {
            cascade.onMenuAction(cascade.comboControl.menu, actionId)
        }
        function onClosed() {
            if (cascade.comboControl.isOpen) cascade.comboControl.isOpen = false
        }
        target: cascade.comboControl.menu
        ignoreUnknownSignals: true
    }

    Connections {
        function onActionTriggered(actionId) {
            cascade.onMenuAction(cascade.menu, actionId)
        }
        function onClosed() {
            if (cascade.comboControl.isOpen) cascade.comboControl.isOpen = false
        }
        target: cascade.menu
        ignoreUnknownSignals: true
    }
}
