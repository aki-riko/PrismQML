// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."

// A11ySurface - Accessible metadata for the item that hosts it 宿主项的无障碍元数据
// Applies role, name, description and checked state to the item it is declared in,
// so a component adopts accessibility with one non-visual line instead of an
// attached-property block that competes with size gates.
// 把角色/名称/描述/勾选状态施加到声明它的项目上，使组件用一行非可视声明即可接入
// 无障碍，而不是与体积门禁争夺空间的属性块。
//
// The attached objects still exist (Qt materialises them per assignment); this
// component only removes the declaration-order and line-budget cost. Components
// with fixed object-count contracts must therefore keep opting out.
// 附加对象依然存在（Qt 为每次赋值实体化）；本组件只消除声明顺序与行数预算的代价。
// 因此有固定对象计数合同的组件仍需按件豁免。
//
// Usage 使用方式:
//   A11ySurface { target: control; role: Enums.accessibility.role_button; name: control.text }
Item {
    id: surface

    // ==================== Required Props 必需属性 ====================
    // The item that receives the metadata; usually the declaring component.
    // 接收元数据的项目；通常是声明它的组件。
    required property Item target
    // One Enums.accessibility.role_* token, mapped through the shared helper.
    // 一个 Enums.accessibility.role_* 令牌，经共享辅助函数映射。
    required property int role

    // ==================== Public Props 公开属性 ====================
    property string name: ""
    property string description: ""
    // Only meaningful for checkable and radio roles; other roles leave it unset so
    // assistive technology never announces a stale state.
    // 仅对可勾选与单选角色有意义；其余角色不设置，避免辅助技术播报过期状态。
    property int checkable: 0
    property bool checked: false
    // Decorations (anchors, dividers, glows) carry no text and no interaction, so
    // they should be hidden from the accessibility tree instead of given a role.
    // 装饰元素（锚点、分隔线、光晕）既无文本也无交互，应被无障碍树隐藏而不是赋予角色。
    property bool ignored: false

    // ==================== Readonly State 只读状态 ====================
    // Compose the effective metadata once, then apply it to the target.
    // 先合成有效元数据，再施加到目标项目上。
    readonly property bool _hasCheckedState: checkable !== 0
    readonly property string _effectiveName:
        AccessibilityHelper.resolveName(name, "", "")
    readonly property string _effectiveDescription:
        AccessibilityHelper.describe([description])

    // ==================== Internal Methods 内部方法 ====================
    function _apply() {
        var item = surface.target
        if (item === null || item === undefined) return
        // A decoration is removed from the tree outright; assigning a role on top of
        // that would be contradictory, so the ignored branch returns early.
        // 装饰元素直接从无障碍树移除；再赋予角色会自相矛盾，因此该分支提前返回。
        if (surface.ignored) {
            item.Accessible.ignored = true
            return
        }
        item.Accessible.ignored = false
        item.Accessible.role = AccessibilityHelper.roleValue(surface.role)
        // An explicit name wins; otherwise the target's own Accessible.name is kept
        // so a subclass can declare it on itself in one line.
        // 显式名称优先；否则保留目标自身的 Accessible.name，使子类可用一行自行声明。
        var declared = surface._effectiveName
        if (declared === "") declared = item.Accessible.name || ""
        item.Accessible.name = declared
        var described = surface._effectiveDescription
        if (described !== "") item.Accessible.description = described
        if (surface._hasCheckedState) item.Accessible.checked = surface.checked
    }

    // ==================== Size 尺寸 ====================
    // Non-visual: never occupies space and never intercepts input.
    // 非可视：不占空间、不拦截输入。
    width: 0
    height: 0
    enabled: false
    visible: false

    onTargetChanged: _apply()
    onRoleChanged: _apply()
    onNameChanged: _apply()
    onDescriptionChanged: _apply()
    onCheckedChanged: _apply()
    onCheckableChanged: _apply()
    Component.onCompleted: _apply()
}
