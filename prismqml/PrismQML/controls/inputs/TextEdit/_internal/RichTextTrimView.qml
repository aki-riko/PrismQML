// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// RichTextTrimView - Eliding read-only presentation for a text block
// 文本块的省略式只读呈现
// Used only while a TextEditCore asks for ellipsis trimming, so the classic
// TextEdit presentation stays untouched by default.
// 仅在 TextEditCore 请求省略号裁剪时使用, 默认路径的 TextEdit 呈现完全不变。
// Tokens arrive as required properties so this module never imports the PrismQML
// module and can keep using the plain QtQuick Text.
// token 通过必需属性传入, 使本模块无需引入 PrismQML 模块并继续使用 QtQuick 的 Text。
Item {
    id: trimView

    // ==================== Required Props 必需属性 ====================
    required property var editor
    required property string textFontFamily
    required property int textFontSize
    required property color textColor
    required property int trimWrapMode

    // ==================== Readonly State 只读状态 ====================
    // Line height comes from the font metrics, so no probe text is needed.
    // 行高直接取自字体度量, 无需任何探针文本。
    readonly property real _lineHeight: metrics.height
    // Lines the fixed viewport can show 固定视口可展示的行数
    readonly property int _maxLines: _lineHeight > 0
        ? Math.max(1, Math.floor(height / _lineHeight)) : 1
    // Unclamped height of the identical layout 同一排版的未裁剪高度
    readonly property real naturalHeight: measureText.contentHeight
    readonly property bool hasOverflow: naturalHeight > height + 1
    // Qt honours maximumLineCount for plain text only; rich text still clips and
    // reports its overflow through hasOverflow. Qt 仅在纯文本下支持
    // maximumLineCount; 富文本仍然裁切并通过 hasOverflow 报告溢出。
    readonly property bool truncated: visibleText.truncated

    // ==================== Signals 信号 ====================
    signal linkTriggered(string link)

    anchors.fill: parent

    // ==================== Content 内容 ====================
    FontMetrics {
        id: metrics
        font.family: trimView.textFontFamily
        font.pixelSize: trimView.textFontSize
    }

    // Off-viewport measuring layout 视口外测量排版
    Text {
        id: measureText
        objectName: "richTextTrimMeasure"
        x: -100000
        width: trimView.width
        text: trimView.editor.text
        textFormat: trimView.editor.textFormat
        wrapMode: trimView.trimWrapMode
        font.family: trimView.textFontFamily
        font.pixelSize: trimView.textFontSize
    }

    // Clamped, eliding presentation 已裁剪并带省略号的呈现
    Text {
        id: visibleText
        objectName: "richTextTrimLabel"
        anchors.fill: parent
        text: trimView.editor.text
        textFormat: trimView.editor.textFormat
        wrapMode: trimView.trimWrapMode
        maximumLineCount: trimView._maxLines
        elide: Text.ElideRight
        font.family: trimView.textFontFamily
        font.pixelSize: trimView.textFontSize
        color: trimView.textColor
        clip: true
        onLinkActivated: (link) => trimView.linkTriggered(link)
    }
}
