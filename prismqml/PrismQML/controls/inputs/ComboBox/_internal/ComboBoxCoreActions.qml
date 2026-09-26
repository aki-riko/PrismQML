// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../../.."
import QtQuick  // After library import: unprefixed native types stay unshadowed 置于库import后:去前缀后保原生类型不被库覆盖

// ComboBoxCoreActions - Popup factory and edit command owner 弹层工厂与编辑命令所有者
// Keeps non-visual ComboBoxCore wiring out of the public entry
// 将非视觉的 ComboBoxCore 装配逻辑移出公开入口。
QtObject {
    id: actions

    // ==================== Required Props 必需属性 ====================
    required property var comboControl

    // ==================== Public Props 公开属性 ====================
    // Default popup content (uses popupDelegate) 默认弹出内容(使用popupDelegate)
    property Component defaultPopupContent: Component {
        ComboBoxPopupContent {
            control: actions.comboControl
        }
    }

    // ==================== Internal Methods 内部方法 ====================
    function _dispatchEditAction(actionName, mutatesText) {
        var control = actions.comboControl
        if (!control.editable || !control.useDefaultContent || !control.enabled
                || typeof control.editableInput[actionName] !== "function") return false
        var previousText = control.editableInput.text
        control.editableInput[actionName]()
        if (mutatesText && control.editableInput.text !== previousText) {
            if (control.currentIndex !== -1) control.currentIndex = -1
            if (control.currentText !== control.editableInput.text) {
                control.currentText = control.editableInput.text
                control.textEdited(control.currentText)
            }
        }
        return true
    }
}
