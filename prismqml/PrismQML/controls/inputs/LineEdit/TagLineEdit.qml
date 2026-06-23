// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import ".."
import "../../icons"
import "../../buttons"
import "../../data"
import "./_internal"
import "../_internal" as InputsInternal

// TagLineEdit - Tag input field (extends InputCore) 标签输入框
// Input becomes tags 输入内容变成标签
InputCore {
    id: control

    // ==================== Public Props 公开属性 ====================
    property var tags: []
    property string separator: " "  // Separator 分隔符
    property string placeholderText: ""
    property int maxTags: -1  // Max tags, -1=unlimited 最大标签数
    property bool showSearchButton: true  // Search button visible 搜索按钮可见
    property string tagIcon: ""  // Default tag icon 默认标签图标
    property var suggestions: []  // Autocomplete suggestions 自动完成建议
    property bool allowCustomTags: true  // Allow custom tags 允许自定义标签
    property var extraSeparators: []  // Extra separator chars, e.g. [",",";"] 额外分隔符,粘贴/输入时一并拆分
    property var validateTag: null  // Optional function(text)->bool, reject when returns false 可选校验回调,返回false拒绝
    property var tagColors: ({})  // Optional {tagText: colorString} per-tag tint 可选按标签着色映射

    // Filtered suggestions 过滤后的建议列表
    property bool _forceShowAll: false  // Force show all items 强制显示全部
    readonly property var _filteredItems: {
        // Show all when forced, filter when typing 强制时显示全部，输入时过滤
        if (_forceShowAll) {
            return suggestions.filter(function(item) {
                var text = typeof item === 'string' ? item : (item.text || '')
                return tags.indexOf(text) < 0  // Exclude already added 排除已添加
            }).slice(0, 8)
        }
        if (!inputField.text.trim()) return []
        var query = inputField.text.trim().toLowerCase()
        return suggestions.filter(function(item) {
            var text = typeof item === 'string' ? item : (item.text || '')
            return text.toLowerCase().indexOf(query) >= 0 && tags.indexOf(text) < 0
        }).slice(0, 8)  // Max 8 items 最多8个
    }
    readonly property bool _showSuggestions: _filteredItems.length > 0 && inputField.activeFocus

    // ==================== Signals 信号 ====================
    signal tagAdded(string tag)
    signal tagRemoved(int index, string tag)
    signal tagsModified(var newTags)
    signal searched(string text)  // Search signal 搜索信号

    // ==================== Methods 方法 ====================
    // All separator chars (primary + extras) 全部分隔符集合
    function _allSeparators() {
        var list = (separator && separator.length) ? [separator] : []
        if (extraSeparators && extraSeparators.length) {
            for (var i = 0; i < extraSeparators.length; i++) {
                var s = extraSeparators[i]
                if (s && list.indexOf(s) < 0) list.push(s)
            }
        }
        return list
    }

    // Whether text matches one of the suggestions 文本是否命中建议项 (兼容字符串/对象形态)
    function _isSuggested(text) {
        for (var i = 0; i < suggestions.length; i++) {
            var item = suggestions[i]
            var label = typeof item === 'string' ? item : (item.text || '')
            if (label === text) return true
        }
        return false
    }

    // Unified gate shared by addTag() and key/paste paths 统一校验闸门
    // 去重 / maxTags / allowCustomTags / validateTag 集中一处, 避免逻辑散落
    function _canAcceptTag(text) {
        if (!text) return false
        if (maxTags > 0 && tags.length >= maxTags) return false
        if (tags.indexOf(text) >= 0) return false  // Block duplicate 拒绝重复
        if (!allowCustomTags && !_isSuggested(text)) return false  // Only suggested 仅允许建议项
        if (validateTag && !validateTag(text)) return false  // User validation 用户校验
        return true
    }

    function addTag(text, icon) {
        var trimmed = (text || "").trim()
        if (!_canAcceptTag(trimmed)) return
        // QML array needs reassign to trigger update QML数组重新赋值触发更新
        var newTags = tags.slice()
        newTags.push(trimmed)
        tags = newTags
        tagsModified(tags)
        tagAdded(trimmed)
    }

    // Split raw text by all separators and add each accepted segment 按分隔符拆分并批量添加
    // 用于粘贴 "a,b,c" 场景; 返回是否消费了输入 (含分隔符即消费)
    function _addSplit(raw) {
        var seps = _allSeparators()
        if (!seps.length) return false
        var hasSep = false
        for (var s = 0; s < seps.length; s++) {
            if (raw.indexOf(seps[s]) >= 0) { hasSep = true; break }
        }
        if (!hasSep) return false
        // Build a regex-safe split on any separator 用任一分隔符拆分
        var parts = [raw]
        for (var k = 0; k < seps.length; k++) {
            var next = []
            for (var p = 0; p < parts.length; p++) {
                next = next.concat(parts[p].split(seps[k]))
            }
            parts = next
        }
        for (var j = 0; j < parts.length; j++) addTag(parts[j])
        return true
    }

    function clearTags() {
        tags = []
        tagsModified(tags)
    }

    // Calculate current/max tag count display 计算标签数显示
    readonly property string _countText: maxTags > 0 ? tags.length + "/" + maxTags : ""
    
    
    // ==================== Bind InputCore State 绑定InputCore状态 ====================
    focused: inputField.activeFocus
    property alias textInput: inputField
    
    // ==================== Size 尺寸 ====================
    implicitWidth: 300
    implicitHeight: Math.max(Enums.controlSize.inputHeight, tagsFlow.height + Enums.spacing.l)
    radius: Enums.radius.small

    // ==================== Bind Hovered State 绑定hovered状态 ====================
    hovered: hoverHandler.hovered

    // ==================== Content 内容 ====================
    Flow {
        id: tagsFlow
        anchors.left: parent.left
        anchors.right: rightArea.left
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: control.paddingLeft
        anchors.rightMargin: control.paddingRight
        anchors.topMargin: control.paddingTop
        anchors.bottomMargin: control.paddingBottom
        spacing: Enums.spacing.xs

        // Existing tags 已有标签
        Repeater {
            id: tagsRepeater
            model: control.tags

            delegate: Tag {
                tagControl: control  // Use different name to avoid shadowing 使用不同名称避免遮蔽
                tagColor: control.tagColors ? (control.tagColors[modelData] || "") : ""  // Per-tag tint 按标签着色
            }
        }

        // Input field 输入框
        TextInput {
            id: inputField
            // Reserve a slim slot (~one short tag) so adding a tag doesn't immediately push the input to next row.
            // tagsFlow already anchors to rightArea.left, so we only need to leave a small in-flow gap here.
            // 仅在 Flow 内为可能的同行 tag 预留一段窄槽位；右侧计数/搜索按钮空间已由 tagsFlow 锚定避开。
            width: Math.max(120, tagsFlow.width - Enums.spacing.xxxl)
            height: Enums.spacing.xxxl
            font.family: control.fontFamily
            font.pixelSize: control.fontSize
            color: Enums.textColor.primary
            selectionColor: control.selectionColor
            selectedTextColor: control.selectedTextColor
            enabled: control.enabled
            clip: true
            verticalAlignment: Text.AlignVCenter

            InputsInternal.InputPlaceholderLabel {
                anchors.fill: parent
                text: control.placeholderText
                visible: !parent.text && !parent.activeFocus && control.tags.length === 0
            }

            onTextEdited: {
                control._forceShowAll = false  // Reset when typing 输入时重置
                // Paste/typed separators → split into multiple tags 粘贴或输入分隔符时拆分成多个标签
                // (single-char separator keystroke also routes here; trailing empty segment is dropped)
                if (control._addSplit(text)) text = ""
            }

            Keys.onPressed: (event) => {
                // Enter/Return commits the current buffer; separators are handled in onTextEdited.
                // Enter 提交当前缓冲; 分隔符拆分已在 onTextEdited 处理 (此处兜底 Enter)
                if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                    var trimmedText = text.trim()
                    if (trimmedText) {
                        // _canAcceptTag 统一处理 maxTags/去重/allowCustomTags/validateTag
                        if (control._canAcceptTag(trimmedText)) {
                            control.addTag(trimmedText)
                            text = ""
                        }
                        // Rejected: keep text so user can fix 被拒时保留文本供修正
                    }
                    event.accepted = true
                }
                // Backspace should NOT remove tags, only X button can 退格键不应删除tag，只能通过X按钮删除
            }
        }
    }
    
    // ==================== Right Area (count + search button) 右侧区域 ====================
    Row {
        id: rightArea
        anchors.right: parent.right
        anchors.rightMargin: Enums.spacing.m
        anchors.verticalCenter: parent.verticalCenter
        spacing: Enums.spacing.s
        
        // Count display 计数显示
        Label {
            type: Enums.label.type_caption
            text: control._countText
            color: Enums.stateColor.scrollThumbHover
            visible: control._countText !== ""
            anchors.verticalCenter: parent.verticalCenter
        }
        
        // Search button 搜索按钮
        SearchButton {
            visible: control.showSearchButton
            anchors.verticalCenter: parent.verticalCenter
            onClicked: {
                // Show all completion items 显示所有补全项
                control._forceShowAll = true
                inputField.forceActiveFocus()
                control.searched(inputField.text)
            }
        }
    }

    // ==================== Autocomplete Dropdown 自动完成下拉列表 ====================
    TagSuggestionPopup {
        control: control
        filteredItems: control._filteredItems
        showSuggestions: control._showSuggestions
    }
    
    // ==================== Hover Detection 悬浮检测 ====================
    HoverHandler {
        id: hoverHandler
    }
    
    TapHandler {
        onTapped: inputField.forceActiveFocus()
    }
}
