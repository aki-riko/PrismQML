// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import ".."

// PlainTextEdit - Extends TextEditCore 纯文本编辑器
// Multiline text, rounded border 多行文本圆角边框
TextEditCore {
    id: control
    
    // Historical signal alias 历史信号别名
    signal textContentChanged()
    onTextEdited: textContentChanged()
    
    // Enable scroll indicator 启用滚动条指示器
    showScrollIndicator: true
    
    // Default size 默认尺寸
    implicitWidth: 300
    implicitHeight: 150
    radius: Enums.radius.large
}
