// ActionLogic - Stateless menu action rules 无状态菜单动作规则
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

.pragma library

// Dynamic CanExecute: null always allows, a bool is fixed, a function is re-evaluated.
// 动态 CanExecute: null 始终允许, bool 为固定值, function 每次求值。
function canExecute(action) {
    if (!action) return false
    var rule = action.canExecute
    if (rule === undefined || rule === null) return true
    if (typeof rule === "function") return !!rule()
    return !!rule
}

// Clear every other checked row of the same single-choice group.
// 清除同一单选组内其它已选中的行。
function clearGroup(action) {
    var parent = action.parent
    if (!parent || !parent.children) return
    var siblings = parent.children
    for (var i = 0; i < siblings.length; i++) {
        var sibling = siblings[i]
        if (sibling === action) continue
        if (sibling.radioGroup === action.radioGroup && sibling.checked) {
            sibling.checked = false
        }
    }
}

// Activate a row exactly like a pointer click: submenu, selection, then triggered.
// 与指针点击完全一致地激活一行: 先子菜单, 再选中状态, 最后触发。
function activate(action) {
    if (!action || !action.enabled || !canExecute(action)) return false
    if (action.hasSubmenu) {
        action.submenuRequested()
        return true
    }
    if (action.radioMode) {
        if (action.exclusive) clearGroup(action)
        action.checked = true
    } else if (action.checkable) {
        action.checked = !action.checked
    }
    action.triggered()
    return true
}
