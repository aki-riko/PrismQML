// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import ".."

// LineEditVariants - Input mode factories 输入模式工厂
// Keeps normal, label, and tag creation separate from LineEditCore's loader wiring.
// 将普通、标签和标签列表创建从 LineEditCore 的 Loader 编排中分离。
Item {
    id: variants

    // ==================== Required Props 必需属性 ====================
    required property var lineEditControl

    // ==================== Public Props 公开属性 ====================
    property alias normalComponent: normalComponent
    property alias labelComponent: labelComponent
    property alias tagComponent: tagComponent

    // ==================== Size 尺寸 ====================
    width: 0
    height: 0
    visible: false

    // ==================== Content 内容 ====================
    // Normal/password/search component 普通/密码/搜索组件
    Component {
        id: normalComponent

        LineEditNormal {
            inputType: variants.lineEditControl.inputType
            placeholderText: variants.lineEditControl.placeholderText
            readOnly: variants.lineEditControl.readOnly
            maximumLength: variants.lineEditControl.maximumLength
            clearButtonEnabled: variants.lineEditControl.clearButtonEnabled
            validator: variants.lineEditControl.validator
            inputMethodHints: variants.lineEditControl.inputMethodHints
            showPassword: variants.lineEditControl.showPassword
            collapsible: variants.lineEditControl.collapsible
            collapsedWidth: variants.lineEditControl.collapsedWidth
            expandedWidth: variants.lineEditControl.expandedWidth
            controlEnabled: variants.lineEditControl.enabled
            paddingLeft: variants.lineEditControl.paddingLeft
            paddingRight: variants.lineEditControl.paddingRight
            fontSize: variants.lineEditControl.fontSize
            inputTextColor: variants.lineEditControl.inputTextColor
            selectionColor: variants.lineEditControl.selectionColor
            selectedTextColor: variants.lineEditControl.selectedTextColor

            onTextEdited: (text) => variants.lineEditControl.textEdited(text)
            onAccepted: variants.lineEditControl.accepted()
            onEditingFinished: variants.lineEditControl.editingFinished()
            onSearched: (text) => variants.lineEditControl.searched(text)
            onCleared: variants.lineEditControl.cleared()
            onSelectionChanged: variants.lineEditControl.selectionChanged()
        }
    }

    // Label component 标签组件
    Component {
        id: labelComponent

        LineEditLabel {
            label: variants.lineEditControl.label
            placeholderText: variants.lineEditControl.placeholderText
            controlEnabled: variants.lineEditControl.enabled
            paddingLeft: variants.lineEditControl.paddingLeft
            paddingRight: variants.lineEditControl.paddingRight
            fontSize: variants.lineEditControl.fontSize
            selectionColor: variants.lineEditControl.selectionColor
            selectedTextColor: variants.lineEditControl.selectedTextColor

            onTextModified: (text) => variants.lineEditControl.textModified(text)
            onEditingFinished: variants.lineEditControl.editingFinished()
        }
    }

    // Tag component 标签组件
    Component {
        id: tagComponent

        // Tag uses existing TagLineEdit directly Tag 使用现有 TagLineEdit
        Item {
            id: tagContent

            property string text: ""
            readonly property bool focused: tagEdit.focused
            readonly property bool hovered: tagEdit.hovered
            property var textInput: tagEdit.textInput
            readonly property var editActionTarget: tagEdit
            readonly property real contentHeight: tagEdit.implicitHeight

            TagLineEdit {
                id: tagEdit

                anchors.fill: parent
                tags: variants.lineEditControl.tags
                separator: variants.lineEditControl.separator
                placeholderText: variants.lineEditControl.placeholderText
                maxTags: variants.lineEditControl.maxTags
                suggestions: variants.lineEditControl.suggestions
                allowCustomTags: variants.lineEditControl.allowCustomTags
                extraSeparators: variants.lineEditControl.extraSeparators
                validateTag: variants.lineEditControl.validateTag
                tagColors: variants.lineEditControl.tagColors
                enabled: variants.lineEditControl.enabled
                transparentBackground: true

                onTagAdded: (tag) => variants.lineEditControl.tagAdded(tag)
                onTagRemoved: (index, tag) =>
                    variants.lineEditControl.tagRemoved(index, tag)
                onTagsModified: (newTags) => {
                    variants.lineEditControl.tags = newTags
                    variants.lineEditControl.tagsModified(newTags)
                }
                onSearched: (text) => variants.lineEditControl.searched(text)
            }
        }
    }
}
