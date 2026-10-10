// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// ActionAccelerator - Real keyboard accelerator for one menu action 单个菜单动作的真实键盘加速器
// Application scope: the row keeps its accelerator while its popup is closed.
// 应用级作用域: 弹层关闭时该行仍保留键盘加速器。
Shortcut {
    id: accelerator

    // ==================== Required Props 必需属性 ====================
    required property var actionControl

    objectName: "actionAccelerator"
    sequence: actionControl.shortcut
    context: Qt.ApplicationShortcut
    enabled: actionControl.enabled && actionControl.canExecuteNow
    autoRepeat: false
    onActivated: actionControl.activate()
    // An ambiguous sequence must still reach the row instead of going silent.
    // 冲突的快捷键序列仍须触达该行, 而不是静默失效。
    onActivatedAmbiguously: actionControl.activate()
}
