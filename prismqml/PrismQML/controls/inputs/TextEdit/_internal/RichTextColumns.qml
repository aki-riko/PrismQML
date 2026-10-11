// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// RichTextColumns - Newspaper-style multi-column rich text viewport 报纸式多列富文本视口
// Created only while a TextEditCore asks for more than one column, so the
// single-column presentation keeps its original object tree untouched.
// 仅在 TextEditCore 请求多列时创建, 单列呈现保持原有对象树不变。
// Tokens arrive as required properties so this module never imports the PrismQML
// module and can keep using the plain QtQuick TextEdit.
// token 通过必需属性传入, 使本模块无需引入 PrismQML 模块并继续使用 QtQuick 的 TextEdit。
Item {
    id: columns

    // ==================== Required Props 必需属性 ====================
    required property var editor
    required property real columnGap
    required property string textFontFamily
    required property int textFontSize
    required property color textColor

    // ==================== Readonly State 只读状态 ====================
    readonly property int _columnCount: Math.max(1, editor.columnCount)
    readonly property real _columnWidth:
        Math.max(1, (width - columnGap * (_columnCount - 1)) / _columnCount)
    // Height of the whole text laid out at one column's width
    // 整段文本按单列宽度排布后的总高度
    readonly property real _textHeight: measureEdit.contentHeight
    // Height the visible column area can show 可见列区域能展示的高度
    readonly property real _visibleHeight: Math.max(0, height) * _columnCount
    readonly property bool hasOverflow: _textHeight > _visibleHeight + 1

    // ==================== Content 内容 ====================
    // Offscreen measuring editor 离屏测量编辑器
    TextEdit {
        id: measureEdit
        visible: false
        width: columns._columnWidth
        text: columns.editor.text
        textFormat: columns.editor.textFormat
        wrapMode: TextEdit.Wrap
        font.family: columns.textFontFamily
        font.pixelSize: columns.textFontSize
        readOnly: true
    }

    // One clipped viewport per column 每列一个裁剪视口
    Row {
        anchors.fill: parent
        spacing: columns.columnGap

        Repeater {
            model: columns._columnCount

            delegate: Item {
                width: columns._columnWidth
                height: columns.height
                clip: true

                TextEdit {
                    width: columns._columnWidth
                    // Slice the shared layout by one column height per viewport
                    // 每个视口按一列高度切分同一份排版
                    y: -index * columns.height
                    text: columns.editor.text
                    textFormat: columns.editor.textFormat
                    wrapMode: TextEdit.Wrap
                    font.family: columns.textFontFamily
                    font.pixelSize: columns.textFontSize
                    color: columns.textColor
                    readOnly: true
                    selectByMouse: false
                    activeFocusOnPress: false
                    cursorVisible: false
                }
            }
        }
    }
}
