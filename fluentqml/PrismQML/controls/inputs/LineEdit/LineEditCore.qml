// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import ".."

// LineEdit - Unified single-line input component 统一单行输入组件
// Control via inputType 通过inputType控制类型
// Modular architecture: uses internal modules 模块化架构
InputCore {
    id: control
    focusTarget: loader.item ? loader.item.textInput : null
    
    // ==================== Type 类型 ====================
    property int inputType: Enums.input.type_normal
    
    // ==================== Common Props 通用属性 ====================
    // 注意：text 使用双向同步而非绑定，防止外部 .text = "" 赋值打破绑定
    property string text: ""
    property bool _syncing: false  // 防止同步循环
    onTextChanged: {
        if (!_syncing && loader.item && loader.item.text !== text) {
            _syncing = true
            loader.item.text = text
            _syncing = false
        }
    }
    property string placeholderText: ""
    property bool readOnly: false
    property int maximumLength: 32767
    property bool clearButtonEnabled: true
    // Optional input filtering 可选输入过滤
    // 例如: validator: IntValidator { bottom: 0; top: 99999 }
    //       validator: DoubleValidator { ... }
    //       validator: RegularExpressionValidator { regularExpression: /.../ }
    property var validator: null
    // 例如: inputMethodHints: Qt.ImhDigitsOnly (软键盘 + IME 提示)
    property int inputMethodHints: Qt.ImhNone
    
    // ==================== Password Props 密码属性 ====================
    property bool showPassword: false
    
    // ==================== Search Props 搜索属性 ====================
    property bool collapsible: false
    property int collapsedWidth: Enums.controlSize.inputHeight  // Match height for square 正方形
    property int expandedWidth: 200
    
    // ==================== Label Props 标签属性 ====================
    property string label: ""
    
    // ==================== Tag Props 标签属性 ====================
    property var tags: []
    property string separator: " "
    property int maxTags: -1
    property var suggestions: []
    property bool allowCustomTags: true   // Allow custom (non-suggested) tags 允许自定义标签
    property var extraSeparators: []      // Extra separator chars for split/paste 额外分隔符
    property var validateTag: null        // Optional function(text)->bool 校验回调
    property var tagColors: ({})          // Optional {tagText: color} tint map 按标签着色

    // ==================== Signals 信号 ====================
    signal textEdited(string text)
    signal accepted()
    signal editingFinished()
    signal searched(string text)
    signal cleared()
    signal textModified(string newText)
    signal tagAdded(string tag)
    signal tagRemoved(int index, string tag)
    signal tagsModified(var newTags)
    signal selectionChanged()  // Selection changed 选择变化
    
    // ==================== Bind State 绑定状态 ====================
    focused: loader.item ? loader.item.focused : false
    hovered: loader.item ? loader.item.hovered : false
    property var textInput: loader.item ? loader.item.textInput : null
    // 透传 TextInput 状态属性,避免调用方写 lineEdit.textInput.cursorPosition
    // 这种 2 级链 (textInput 在 Loader 异步加载时短暂为 null,2 级链会报错)
    readonly property int cursorPosition: textInput ? textInput.cursorPosition : 0
    readonly property int selectionStart: textInput ? textInput.selectionStart : 0
    readonly property int selectionEnd: textInput ? textInput.selectionEnd : 0
    readonly property string selectedText: textInput ? textInput.selectedText : ""
    // 当前 text 是否通过 validator 验证 (无 validator 时永远 true)
    readonly property bool acceptableInput: textInput ? textInput.acceptableInput : true
    
    // ==================== Size 尺寸 ====================
    // Override InputCore content size 覆盖InputCore内容尺寸
    // Content calculated size based on inputType 根据inputType计算内容尺寸
    contentWidth: {
        switch (inputType) {
            case Enums.input.type_label: return Enums.controlSize.inputDefaultWidth + 50
            case Enums.input.type_tag: return Enums.controlSize.inputDefaultWidth + 100
            default:
                if (_isSearch && collapsible) return expanded ? expandedWidth : collapsedWidth
                return Enums.controlSize.inputDefaultWidth
        }
    }
    contentHeight: {
        switch (inputType) {
            case Enums.input.type_label: return Enums.controlSize.inputHeightLabel
            case Enums.input.type_tag: return Math.max(Enums.controlSize.inputHeightCompact, loader.item ? loader.item.contentHeight : Enums.controlSize.inputHeightCompact)
            default: return Enums.controlSize.inputHeight
        }
    }
    
    // ==================== Internal State 内部状态 ====================
    readonly property bool _isSearch: inputType === Enums.input.type_search
    readonly property bool expanded: !collapsible || (loader.item ? loader.item.expanded : true)

    // ==================== Public Methods 公开方法 ====================
    function clear() { if (loader.item && loader.item.clear) loader.item.clear() }
    function selectAll() { if (loader.item && loader.item.selectAll) loader.item.selectAll() }
    function forceActiveFocus() { if (loader.item && loader.item.forceActiveFocus) loader.item.forceActiveFocus() }

    // Undo last edit 撤销
    function undo() { if (loader.item && loader.item.undo) loader.item.undo() }

    // Redo last undone edit 重做
    function redo() { if (loader.item && loader.item.redo) loader.item.redo() }

    // Copy selected text 复制
    function copy() { if (loader.item && loader.item.copy) loader.item.copy() }

    // Cut selected text 剪切
    function cut() { if (loader.item && loader.item.cut) loader.item.cut() }

    // Paste from clipboard 粘贴
    function paste() { if (loader.item && loader.item.paste) loader.item.paste() }

    // ==================== Public Methods 公共方法 ====================
    // Set text 设置文本 (现在也可直接用 .text = value)
    function setText(t) { text = t }
    function getText() { return text }

    function isEnabled() { return enabled }

    // Has focus 是否有焦点
    function hasFocus() { return loader.item ? loader.item.activeFocus : false }

    // Set alignment 设置对齐方式
    function setAlignment(align) { if (loader.item) loader.item.horizontalAlignment = align }

    // ==================== Collapsible Animation 折叠动画 ====================
    Behavior on implicitWidth {
        enabled: _isSearch && collapsible
        NumberAnimation { duration: Enums.duration.medium; easing.type: Easing.OutCubic }
    }
    
    // ==================== Dynamic Loader 动态加载器 ====================
    Loader {
        id: loader
        anchors.fill: parent
        sourceComponent: {
            switch (control.inputType) {
                case Enums.input.type_normal:
                case Enums.input.type_password:
                case Enums.input.type_search:
                    return normalComponent
                case Enums.input.type_label:
                    return labelComponent
                case Enums.input.type_tag:
                    return tagComponent
                default:
                    return normalComponent
            }
        }
        // Loader 加载完成时同步初始文本
        onLoaded: {
            if (item && control.text && item.text !== control.text) {
                item.text = control.text
            }
        }
    }

    // 内部组件 → 外部 text 属性同步 (用户输入时触发)
    Connections {
        target: loader.item
        function onTextChanged() {
            if (!control._syncing && loader.item && control.text !== loader.item.text) {
                control._syncing = true
                control.text = loader.item.text
                control._syncing = false
            }
        }
    }
    
    // ==================== Normal/Password/Search Component 普通组件 ====================
    Component {
        id: normalComponent
        LineEditNormal {
            inputType: control.inputType
            placeholderText: control.placeholderText
            readOnly: control.readOnly
            maximumLength: control.maximumLength
            clearButtonEnabled: control.clearButtonEnabled
            validator: control.validator
            inputMethodHints: control.inputMethodHints
            showPassword: control.showPassword
            collapsible: control.collapsible
            collapsedWidth: control.collapsedWidth
            expandedWidth: control.expandedWidth
            controlEnabled: control.enabled
            paddingLeft: control.paddingLeft
            paddingRight: control.paddingRight
            fontFamily: control.fontFamily
            fontSize: control.fontSize
            inputTextColor: control.inputTextColor
            selectionColor: control.selectionColor
            selectedTextColor: control.selectedTextColor

            onTextEdited: (text) => control.textEdited(text)
            onAccepted: control.accepted()
            onEditingFinished: control.editingFinished()
            onSearched: (text) => control.searched(text)
            onCleared: control.cleared()
            onSelectionChanged: control.selectionChanged()
        }
    }
    
    // ==================== Label Component 标签组件 ====================
    Component {
        id: labelComponent
        LineEditLabel {
            label: control.label
            placeholderText: control.placeholderText
            controlEnabled: control.enabled
            paddingLeft: control.paddingLeft
            paddingRight: control.paddingRight
            fontFamily: control.fontFamily
            fontSize: control.fontSize
            
            onTextModified: (text) => control.textModified(text)
            onEditingFinished: control.editingFinished()
        }
    }
    
    // ==================== Tag Component 标签组件 ====================
    Component {
        id: tagComponent
        // Tag uses existing TagLineEdit directly Tag使用现有组件
        Item {
            property string text: ""  // Tag模式不使用text
            readonly property bool focused: tagEdit.focused
            readonly property bool hovered: tagEdit.hovered
            property var textInput: tagEdit.textInput
            readonly property real contentHeight: tagEdit.implicitHeight

            TagLineEdit {
                id: tagEdit
                anchors.fill: parent
                tags: control.tags
                separator: control.separator
                placeholderText: control.placeholderText
                maxTags: control.maxTags
                suggestions: control.suggestions
                allowCustomTags: control.allowCustomTags
                extraSeparators: control.extraSeparators
                validateTag: control.validateTag
                tagColors: control.tagColors
                enabled: control.enabled
                transparentBackground: true  // 避免双重阴影叠加

                onTagAdded: (tag) => control.tagAdded(tag)
                onTagRemoved: (index, tag) => control.tagRemoved(index, tag)
                onTagsModified: (newTags) => { control.tags = newTags; control.tagsModified(newTags) }
                onSearched: (text) => control.searched(text)
            }
        }
    }
}
