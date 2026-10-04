// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "../../effects"

// ChatBubbleSurface - Shared chat bubble chrome 共用聊天气泡外壳
//
// Draws only the bubble shell: surface color, radius, tail, border and elevation.
// Callers put their own content inside.
// 只画「气泡壳」：表面色 / 圆角 / 尖角 / 描边 / 阴影层级，内容由调用方塞进来。
//
// `ChatBubble`（Copilot 卡片流）与下游聊天界面（例如 Kaleidos IM 的文本 / 图文 / 文件气泡）
// 共用同一份规则，避免每个界面各写一套配色与圆角——那样用户换主题色、切深色模式或换皮肤时
// 总会有一部分不跟随。
//
// Props 公开属性:
//   role: "user" | "assistant" | "system"   Message role 消息角色（自己 / 对方 / 系统）
//   tail: bool        Asymmetric tail corner 是否使用非对称尖角
//   chromeless: bool  No shell at all (inline text inside a mixed bubble) 无壳用法
//
// Shadow policy 阴影策略: enabled for user and assistant, hidden for system and chromeless.
// A caller that wants a different policy simply overrides `shadowVisible` (Copilot card flow
// keeps the shadow on assistant messages only). 默认两侧都有、系统消息与无壳用法没有；
// 需要别的策略的调用方直接覆盖 `shadowVisible`（Copilot 卡片流就只给助手消息留阴影）。
//
// 🔴 Tails cost nothing to draw: `ShadowedRectangle` only exposes one uniform `radius`, but
//    its `contentItem` is a Qt 6.7+ `Rectangle` which supports per-corner radii, so the
//    edge-side corner is simply tightened. Gluing an extra square/triangle onto the corner
//    would add a draw call and disagree with the SDF shadow.
//    尖角不额外加绘制对象：ShadowedRectangle 只暴露统一 radius，但它的 contentItem 是
//    Qt 6.7+ 的 Rectangle，支持分角圆角，把贴边那一角收紧即可。用额外的方块/三角形去「贴」
//    尖角会多一个绘制对象，还会和 SDF 阴影对不上。
//
// 🔴 The corner radii must be computed right here, not read from a readonly intermediate
//    property: QML runs change handlers **before** re-evaluating dependent bindings, so a
//    handler that reads such a property still sees the old value, writes it back unchanged,
//    and the tail silently never applies. Measured downstream on 2026-10-04.
//    半径必须现算，不能先做成 readonly 中间属性再读：QML 的变更处理函数会先于依赖绑定重算
//    执行，读到旧值就写回原值、尖角永远不生效（2026-10-04 下游实测）。
ShadowedRectangle {
    id: root

    // ==================== Public Props 公开属性 ====================
    property string role: "assistant"
    property bool tail: true
    property bool chromeless: false
    // Whether the user side gets a blurred / hard shadow. The Copilot card flow sets it to
    // false so elevation stays on assistant messages only.
    // 用户侧是否要模糊 / 硬阴影。Copilot 卡片流置 false，把浮起感只留给助手消息。
    property bool elevationOnUser: true

    // ==================== Readonly State 只读状态 ====================
    readonly property bool _isUser: role === "user"
    readonly property bool _isSystem: role === "system"
    readonly property bool _hasTail: tail && !_isSystem && !chromeless
    readonly property real _largeRadius: Enums.surfaceRadius(Enums.radius.large)
    readonly property real _tailRadius: Enums.surfaceRadius(Enums.radius.small)
    readonly property bool _shellElevated: !chromeless && !_isSystem
    readonly property bool _elevated: _shellElevated && (!_isUser || elevationOnUser)
    // Blurred (Fluent) and hard (Neobrutalism) shadows honour `elevationOnUser`; the neumorphic
    // skin expresses elevation as a surface treatment and keeps both sides. Outlined skins ship
    // no elevation by design, so `shadowVisible` stays false there and the hard one below takes over.
    // 模糊（Fluent）与硬阴影（新粗野主义）听 elevationOnUser；新拟态把浮起当表面处理，两侧都留。
    // 描边皮肤按设计不加浮起，故 shadowVisible 在其下为 false，由下方硬阴影接管。
    readonly property bool _softElevated: _elevated && Enums.usesSoftElevation
    readonly property bool _neumorphicElevated: _shellElevated && Enums.isNeumorphism

    // ==================== Public Methods 公开方法 ====================
    // Re-apply the per-corner radii. Exposed so callers that change radius tokens at runtime
    // (skin switch) can refresh the shell. 重新套用分角圆角，供运行期换肤后刷新。
    function applyTail() {
        var content = root.contentItem
        if (!content || content.topLeftRadius === undefined) return
        // Chromeless means "no shell at all", so every corner goes square rather than keeping
        // the shell radius. 无壳用法意味着完全没有壳，四角一律切平，不保留壳的圆角。
        var large = root.chromeless ? 0 : root._largeRadius
        var small = root._tailRadius
        var hasTail = root._hasTail
        content.topLeftRadius = (!hasTail || root._isUser) ? large : small
        content.topRightRadius = large
        content.bottomLeftRadius = large
        content.bottomRightRadius = (hasTail && root._isUser) ? small : large
    }

    // ==================== Shell 外壳 ====================
    color: chromeless ? Enums.transparent
        : (_isSystem ? Enums.hoverColor : (_isUser ? Enums.accentColor : Enums.cardColor))
    radius: chromeless ? 0 : _largeRadius
    shadowLevel: Enums.shadow.level2
    shadowVisible: _softElevated || _neumorphicElevated
    // Outlined skins border every bubble; Fluent borders only the peer side.
    // 描边皮肤给所有气泡加细描边；Fluent 只描对方那一侧。
    border.width: chromeless ? 0
        : (Enums.hasOutlinedSurfaces ? Enums.surfaceBorderWidth(Enums.border.thin)
                                     : (_isUser ? 0 : Enums.border.thin))
    border.color: chromeless ? Enums.transparent
        : (Enums.hasOutlinedSurfaces ? Enums.borderColor
                                     : (_isUser ? Enums.transparent : Enums.borderColor))

    Component.onCompleted: applyTail()
    onRoleChanged: applyTail()
    onTailChanged: applyTail()
    onChromelessChanged: applyTail()
    onRadiusChanged: applyTail()

    // A skin switch changes what `surfaceRadius(...)` returns while `radius` itself may stay the
    // same — then `onRadiusChanged` never fires and the tail corner keeps the previous skin's
    // radius (measured: a 33px residue on the shadow-lifecycle roundtrip). Watch the skin itself.
    // 换皮肤会改 `surfaceRadius(...)` 的取值，而 `radius` 未必随之变化——那样 onRadiusChanged
    // 不触发，尖角那一角会留在旧皮肤半径上（实测在阴影生命周期往返里留下 33px 残差）。故直接盯皮肤。
    Connections {
        target: Enums
        function onSkinChanged() { root.applyTail() }
    }

    // Neobrutalism uses a hard-edged offset shadow instead of a blur. `ShadowedRectangle`
    // ships only the Fluent (SDF blur) and Neumorphic variants, so the hard one belongs
    // here — otherwise the shell loses its elevation the moment the skin changes.
    // 新粗野主义用硬边偏移阴影而不是模糊；ShadowedRectangle 只带 Fluent（SDF 模糊）与新拟态
    // 两种，硬阴影得在这里补——否则一换皮肤气泡就没有浮起感了。
    NeoShadow {
        target: root.contentItem
        visible: root._elevated && Enums.isNeobrutalism
        radius: root.radius
        z: root.contentItem.z - 1
    }
}
