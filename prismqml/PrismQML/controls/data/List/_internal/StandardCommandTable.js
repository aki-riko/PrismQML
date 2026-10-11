// StandardCommandTable - Predefined standard command text presets 预定义标准命令文本预设
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

.pragma library

// Textual presets only: icons and StandardKey values are resolved in QML because
// Enums and StandardKey are not reachable from a library JS file.
// 仅保存文本预设: 图标与 StandardKey 在 QML 侧解析, 因为库 JS 文件访问不到 Enums 与 StandardKey。
var COMMANDS = {
    "cut": { "label": "Cut", "shortcut": "Ctrl+X" },
    "copy": { "label": "Copy", "shortcut": "Ctrl+C" },
    "paste": { "label": "Paste", "shortcut": "Ctrl+V" },
    "undo": { "label": "Undo", "shortcut": "Ctrl+Z" },
    "redo": { "label": "Redo", "shortcut": "Ctrl+Y" },
    "select_all": { "label": "Select All", "shortcut": "Ctrl+A" }
}

function preset(kind) {
    return COMMANDS[kind] || null
}

// Sorted list of the predefined kinds 预定义种类的有序列表
function kinds() {
    var names = []
    for (var kind in COMMANDS) {
        if (COMMANDS.hasOwnProperty(kind)) names.push(kind)
    }
    names.sort()
    return names
}
