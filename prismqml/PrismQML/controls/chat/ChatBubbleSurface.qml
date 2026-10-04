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
//   elevationOnUser: bool  Whether the user side gets elevation 用户侧是否浮起
//
// Shadow policy 阴影策略: user and assistant are elevated by default, system and chromeless are
// not. The Copilot card flow sets `elevationOnUser` to false so blurred and hard elevation stays
// on assistant messages; the neumorphic skin keeps both sides because it expresses elevation as a
// surface treatment. 默认两侧消息都有浮起、系统与无壳没有；Copilot 卡片流用 `elevationOnUser`
// 把模糊与硬阴影收成仅助手，新拟态两侧都留（该皮肤把浮起当表面处理）。
//
// 🔴 Tails cost nothing to draw: `ShadowedRectangle` only exposes one uniform `radius`, but its
//    `contentItem` is a Qt 6.7+ `Rectangle` which supports per-corner radii, so the edge-side
//    corner is simply tightened. Gluing an extra square/triangle onto the corner would add a draw
//    call and disagree with the SDF shadow.
//    尖角不额外加绘制对象：ShadowedRectangle 只暴露统一 radius，但它的 contentItem 是 Qt 6.7+
//    的 Rectangle，支持分角圆角，把贴边那一角收紧即可。用额外的方块/三角形去「贴」尖角会多
//    一个绘制对象，还会和 SDF 阴影对不上。
ShadowedRectangle {
    id: root

    // ==================== Public Props 公开属性 ====================
    property string role: "assistant"
    property bool tail: true
    property bool chromeless: false
    // Whether the user side gets a blurred / hard shadow. The Copilot card flow sets it to false
    // so elevation stays on assistant messages only.
    // 用户侧是否要模糊 / 硬阴影。Copilot 卡片流置 false，把浮起感只留给助手消息。
    property bool elevationOnUser: true

    // ==================== Readonly State 只读状态 ====================
    readonly property bool _isUser: role === "user"
    readonly property bool _isSystem: role === "system"
    readonly property real _largeRadius: Enums.surfaceRadius(Enums.radius.large)
    // Blurred (Fluent) and hard (Neobrutalism) shadows honour `elevationOnUser`; the neumorphic
    // skin expresses elevation as a surface treatment and keeps both sides. Outlined skins ship no
    // elevation by design, so `shadowVisible` stays false there and the hard shadow below takes over.
    // 模糊（Fluent）与硬阴影（新粗野主义）听 elevationOnUser；新拟态把浮起当表面处理，两侧都留。
    // 描边皮肤按设计不加浮起，故 shadowVisible 在其下为 false，由下方硬阴影接管。
    readonly property bool _shellElevated: !chromeless && !_isSystem
    readonly property bool _elevated: _shellElevated && (!_isUser || elevationOnUser)
    readonly property bool _softElevated: _elevated && Enums.usesSoftElevation
    readonly property bool _neumorphicElevated: _shellElevated && Enums.isNeumorphism

    // ==================== Public Methods 公开方法 ====================
    // Re-apply the per-corner radii after `role` / `tail` / `chromeless` changed.
    // 重新套用分角圆角（role / tail / chromeless 变化后调用）。
    //
    // 🔴 Read `role` and the switches **directly** here, and compute the radii from the tokens
    //    right here too: a change handler runs before QML re-evaluates dependent bindings, so
    //    reading an intermediate such as `_isUser` still yields the previous value, the corner gets
    //    rewritten to what it already was, and the tail never moves (measured downstream: after
    //    setting `role` to "user" at runtime the tail stayed on the assistant corner).
    //    半径与开关必须在这里直接读：变更处理函数先于依赖绑定重算执行，读 `_isUser` 这类中间属性
    //    拿到的是旧值，尖角会被写回原样、永远不动（下游实测：运行期把 role 改成 "user" 后尖角
    //    仍留在助手那一角）。
    function applyTail() {
        var content = root.contentItem
        if (!content || content.topLeftRadius === undefined) return
        var isUser = root.role === "user"
        var hasTail = root.tail && root.role !== "system" && !root.chromeless
        // Chromeless means "no shell at all", so every corner goes square rather than keeping the
        // shell radius. 无壳用法意味着完全没有壳，四角一律切平，不保留壳的圆角。
        var large = root.chromeless ? 0 : Enums.surfaceRadius(Enums.radius.large)
        var small = Enums.surfaceRadius(Enums.radius.small)
        content.topLeftRadius = (!hasTail || isUser) ? large : small
        content.topRightRadius = large
        content.bottomLeftRadius = large
        content.bottomRightRadius = (hasTail && isUser) ? small : large
    }

    // Defer the corner writes by one event-loop turn. 把分角圆角的写入延后一轮事件循环。
    function requestTail() {
        tailTimer.restart()
    }

    // Shell 外壳: surface color / radius / border / elevation token policy.
    // 表面色 / 圆角 / 描边 / 阴影层级全部走 Enums 令牌。
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

    Component.onCompleted: requestTail()
    onRoleChanged: requestTail()
    onTailChanged: requestTail()
    onChromelessChanged: requestTail()
    onRadiusChanged: requestTail()

    // The corner writes must land **after** the change notification has fully settled: writing
    // `contentItem.topLeftRadius` synchronously from a change handler gets swallowed by the
    // binding re-evaluation that follows it (measured: changing `role` at runtime left the tail on
    // the old corner, while calling the very same `applyTail()` from outside worked). The timer only
    // runs when restarted, so a resting surface costs nothing.
    // 分角圆角必须在变更通知完全落定之后再写：从变更处理函数里同步写 contentItem.topLeftRadius
    // 会被紧随其后的绑定重算吞掉（实测：运行期改 role 时尖角留在旧的一角，而从外部调用同一个
    // applyTail() 却生效）。该计时器只在 restart 时运行，静止的气泡零开销。
    Timer {
        id: tailTimer
        interval: 0
        onTriggered: root.applyTail()
    }

    // A skin switch changes what `surfaceRadius(...)` returns while `radius` itself may stay the
    // same — then `onRadiusChanged` never fires and the tail corner keeps the previous skin's
    // radius (measured: a 33px residue on the shadow-lifecycle roundtrip). Watch the skin itself.
    // 换皮肤会改 `surfaceRadius(...)` 的取值，而 `radius` 未必随之变化——那样 onRadiusChanged
    // 不触发，尖角那一角会留在旧皮肤半径上（实测在阴影生命周期往返里留下 33px 残差）。故盯皮肤。
    Connections {
        function onSkinChanged() { root.applyTail() }
        target: Enums
    }

    // Neobrutalism uses a hard-edged offset shadow instead of a blur. `ShadowedRectangle` ships
    // only the Fluent (SDF blur) and Neumorphic variants, so the hard one belongs here — otherwise
    // the shell loses its elevation the moment the skin changes.
    // 新粗野主义用硬边偏移阴影而不是模糊；ShadowedRectangle 只带 Fluent（SDF 模糊）与新拟态两种，
    // 硬阴影得在这里补——否则一换皮肤气泡就没有浮起感了。
    NeoShadow {
        target: root.contentItem
        visible: root._elevated && Enums.isNeobrutalism
        radius: root.radius
        z: root.contentItem.z - 1
    }
}
