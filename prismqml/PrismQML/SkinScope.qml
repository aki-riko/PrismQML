// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "SkinResolver.js" as SkinResolver

// SkinScope - Apply one design language to a subtree 让一棵子树使用指定设计语言
//
// Business code only needs this type. It creates a local SkinContext and
// publishes it so every widget in the subtree resolves to it instead of the
// global theme. It never touches ThemeManager, user settings, or persistence.
// 业务侧只需要这个类型。它创建一份局部 SkinContext 并发布出去，让子树内的控件
// 解析到它而不是全局主题。它不触碰 ThemeManager、用户设置或持久化。
//
//   Fluent.SkinScope {
//       skin: "vintage_ticket"
//       Fluent.Card { ... }        // 自动使用票据圆角、边框、颜色与阴影
//       Fluent.ButtonCore { ... }  // 自动使用票据按钮样式
//   }
//
// Nesting works in both directions: a Fluent scope inside a ticket scope
// restores Fluent tokens for its own subtree, and vice versa.
// 嵌套双向可用：票据范围里的 Fluent 范围会让自己这棵子树恢复 Fluent token，反之亦然。
//
// Light/dark stays global; a scope only overrides the design language.
// 明暗保持全局；局部范围只覆盖设计语言。
Item {
    id: root

    // ==================== Public Props 公开属性 ====================
    // Empty string follows the nearest parent scope, or the global skin at the
    // root. 空字符串表示跟随最近父范围；位于根层时跟随全局皮肤。
    property string skin: ""
    // Read-only context for popups, reparented content, and tests.
    // 供弹出层、跨父级重挂载内容与测试使用的只读上下文。
    readonly property var context: _context
    // The design language actually applied after validation and inheritance.
    // 经过校验与继承后实际生效的设计语言。
    readonly property string resolvedSkin: _context.skin

    // ==================== Readonly State 只读状态 ====================
    readonly property var _parentScopeContext: SkinResolver.nearestContext(root.parent)
    readonly property string _inheritedSkin: _parentScopeContext
                                             ? _parentScopeContext.skin
                                             : Enums.skin
    readonly property string _requestedSkin: root.skin !== "" ? root.skin
                                                              : root._inheritedSkin
    // An unknown name falls back to the parent scope, never to a partial skin.
    // 未知名称回退到父范围，绝不产生半套皮肤。
    readonly property string _effectiveSkin: SkinResolver.isValidSkin(root._requestedSkin)
                                             ? root._requestedSkin
                                             : root._inheritedSkin

    // ==================== Internal Props 内部属性 ====================
    // Marker consumed by SkinResolver; not a business contract.
    // 供 SkinResolver 使用的标记，不是业务契约。
    readonly property var _prismSkinScopeContext: _context
    property string _lastWarnedSkin: ""

    // ==================== Internal Methods 内部方法 ====================
    // Warn once per distinct invalid value instead of once per binding pass.
    // 每个不同的无效值只告警一次，而不是每次绑定求值都告警。
    function _warnInvalidSkin(value) {
        if (_lastWarnedSkin === value) return
        _lastWarnedSkin = value
        var scopeName = root.objectName !== "" ? root.objectName : "SkinScope"
        console.warn("SkinScope(" + scopeName + "): 未知皮肤名 '" + value
                     + "'，已回退到父范围或全局皮肤")
    }

    implicitWidth: contentItem.childrenRect.width
    implicitHeight: contentItem.childrenRect.height

    on_RequestedSkinChanged: {
        if (SkinResolver.isValidSkin(root._requestedSkin)) {
            root._lastWarnedSkin = ""
            return
        }
        root._warnInvalidSkin(root._requestedSkin)
    }

    Component.onCompleted: {
        if (!SkinResolver.isValidSkin(root._requestedSkin)) {
            root._warnInvalidSkin(root._requestedSkin)
        }
    }

    // ==================== Content 内容 ====================
    // Children live in an inner item so the scope itself stays a pure marker
    // for the resolver. 子项放在内层 Item 中，让范围本身只作为解析器的标记。
    Item {
        id: contentItem
        objectName: "_skinScopeContent"
        anchors.fill: parent
    }

    default property alias content: contentItem.data

    // Skin context: inputs come from the global appearance so a scope only
    // replaces the design language, never the user's dark mode or base accent.
    // 皮肤上下文：输入取自全局外观，使局部范围只替换设计语言，
    // 不替换用户的明暗或基础主色。
    SkinContext {
        id: _context

        isDark: Enums.isDark
        skin: root._effectiveSkin
        uiFontFamily: Enums.uiFontFamily
        fontMonospace: Enums.fontMonospace
        rawAccentColor: Enums.rawAccentColor
        rawAccentColorLight: Enums.rawAccentColorLight
        rawAccentColorDark: Enums.rawAccentColorDark
        devicePixelRatio: DpiManager.devicePixelRatio
    }
}
