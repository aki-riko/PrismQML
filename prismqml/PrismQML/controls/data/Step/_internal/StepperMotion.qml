// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// StepperMotion - Shared showcase motion tokens 步骤进度条共享炫技动效令牌
// Single source for every duration the showcase layers consume. Reduced motion
// collapses all of them to Enums.duration.none, so a caller keeps one binding and
// only gates the looping animations on `animated`.
// 炫技各层的唯一时长来源。开启减少动态效果时全部收敛为 Enums.duration.none，
// 调用方只需用 `animated` 控制循环动画是否运行。
QtObject {
    id: root

    // ==================== Readonly State 只读状态 ====================
    readonly property bool animated: !Enums.reduceMotion
    // One highlight pass over the progress rail 进度轨单次流光扫过
    readonly property int sweep: animated ? Enums.duration.xslow : Enums.duration.none
    // One dot-trail cycle ahead of the current step 当前步骤前方流动点的一个周期
    readonly property int flow: animated ? Enums.duration.pulse : Enums.duration.none
    // One halo breath stroke 光晕单程呼吸
    readonly property int breathe: animated ? Enums.duration.pulse : Enums.duration.none
    // Activation ripple expansion 激活涟漪扩散
    readonly property int ripple: animated ? Enums.duration.elevation : Enums.duration.none
    // Progress rail growth on step change 步骤切换时进度轨生长
    readonly property int grow: animated ? Enums.duration.spring : Enums.duration.none
    // Completion burst lifetime 完成迸发存活时长
    readonly property int burst: animated ? Enums.duration.elevation : Enums.duration.none
    // Elastic advance and 3D tilt on step change 步骤切换的弹性推进与 3D 倾斜
    readonly property int advance: animated ? Enums.duration.medium : Enums.duration.none
}
