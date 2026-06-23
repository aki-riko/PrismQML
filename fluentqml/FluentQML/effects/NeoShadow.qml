// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../"

// NeoShadow - Neobrutalism 硬阴影组件 (偏移纯黑矩形, 零模糊)
// 收敛 neo 皮肤的硬阴影范式: 控件不再各自手写偏移矩形, 统一 Loader/实例化本组件。
// 用法:
//   NeoShadow { target: _bg }                      // 跟随 _bg 几何, 纯黑
//   NeoShadow { target: _bg; accent: control.focused } // 聚焦时转橙强调
//   NeoShadow { target: _bg; offset: 6 }           // 自定义偏移(默认 neo.shadowOffset)
Rectangle {
    id: shadow

    // ==================== Props 属性 ====================
    // 阴影跟随的目标矩形(取其 width/height/radius)。必填。
    required property Item target
    // accent=true 时阴影转 neo 主色(橙), 用于聚焦/展开等激活态强调。
    property bool accent: false
    // 偏移量(X=Y), 默认取 neo.shadowOffset。
    property real offset: Enums.neo.shadowOffset

    // ==================== Geometry 几何 ====================
    // 放在 target 之下一层 (z = target.z - 1), 由父级负责把本组件声明在 target 之前
    // 或显式设置 z。这里默认 z 比常规背景低。
    x: offset
    y: offset
    width: target ? target.width : 0
    height: target ? target.height : 0
    radius: target ? target.radius : 0
    color: accent ? Enums.neo.primary : Enums.neo.shadowColor

    Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
}
