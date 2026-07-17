// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../../.."
import "../../../../effects"
import "../../../data"
import "../../../utils"
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// TagSuggestionPopup - Autocomplete dropdown for TagLineEdit 标签输入自动完成下拉
// Uses PopupWindowCore for proper layering outside parent bounds 使用PopupWindowCore确保在父组件外正确渲染
Item {
    id: root

    // ==================== Public Props 公开属性 ====================
    property var control  // Parent TagLineEdit 父标签输入框
    property var filteredItems: []
    property bool showSuggestions: false

    // ==================== Internal Methods 内部方法 ====================
    // Handle item selection (called from TagLineEdit) 处理选项选择
    function _handleItemSelected(text) {
        if (!control) return
        control.addTag(text)
        if (control.textInput) {
            control.textInput.text = ""
        }
        control._forceShowAll = false
        popup.close()
    }

    // Keep popup visibility synchronized with input focus and matches.
    // 保持弹窗可见性与输入焦点及匹配项同步。
    onShowSuggestionsChanged: {
        if (showSuggestions && control && filteredItems.length > 0) {
            popup.openAtControl(control)
        } else if (!showSuggestions) {
            popup.close()
        }
    }

    onFilteredItemsChanged: {
        // Update popup height when items change 项目变化时更新高度
        if (popup.isOpen) {
            popup.popupHeight = Math.min(
                filteredItems.length * Enums.controlSize.inputHeight + Enums.spacing.m,
                Enums.controlSize.listDefaultHeight
            )
        }
    }

    // ==================== Content 内容 ====================
    PopupWindowCore {
        id: popup

        // ==================== Internal Props 内部属性 ====================
        // Pass data to Window context 传递数据到Window上下文
        property var listModel: root.filteredItems

        // ==================== Signals 信号 ====================
        // Signal relay for delegate clicks 代理点击信号中继
        signal itemSelected(string text)

        // ==================== Size 尺寸 ====================
        popupWidth: root.control ? root.control.width : Enums.controlSize.listDefaultWidth
        popupHeight: Math.min(
            root.filteredItems.length * Enums.controlSize.inputHeight + Enums.spacing.m,
            Enums.controlSize.listDefaultHeight
        )
        popupRadius: Enums.isPrismDesign ? Enums.prismDesign.radiusPopup : Enums.radius.large
        closeOnClickOutside: false  // Don't auto close, controlled by focus 不自动关闭，由焦点控制
        stealFocus: false  // Keep focus on input field 保持输入框焦点

        // ==================== Content 内容 ====================
        ListView {
            id: suggestionList
            anchors.fill: parent
            model: popup.listModel
            clip: true

            delegate: TagSuggestionDelegate {
                width: ListView.view ? ListView.view.width : suggestionList.width
                itemText: typeof modelData === 'string' ? modelData : (modelData.text || '')
                onItemClicked: function(text) {
                    popup.itemSelected(text)
                }
            }
        }
    }

    // Relay popup selection to the owning tag input.
    // 将弹窗选中项转发给所属标签输入框。
    Connections {
        function onItemSelected(text) {
            root._handleItemSelected(text)
        }

        target: popup
    }
}
