// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

// ColorPickerHsv - Pure HSV state conversion 纯 HSV 状态转换
//
// Owns only the conversion math shared by ColorPickerDialog and
// ColorPickerDropdown. 只持有对话框与下拉共用的转换算式。
// Deliberately NOT owned here, because the two consumers differ:
// 以下有意不归本文件，因为两个消费者的契约不同：
//   - change notification: Dialog emits colorUpdated, Dropdown emits colorChanged
//     变更通知：Dialog 发 colorUpdated，Dropdown 发 colorChanged
//   - alpha read-back: Dialog writes _alpha from the colour, Dropdown does not
//     alpha 回读：Dialog 会从颜色写回 _alpha，Dropdown 不回读
//   - dialog/dropdown lifecycle and initialisation 对话框/下拉的生命周期与初始化

.pragma library

// Split a colour into HSV components plus alpha.
// 把颜色拆成 HSV 分量与 alpha。
//
// Qt reports hsvHue as -1 for achromatic colours (grey/black/white), so callers
// pass the floor they want that sentinel collapsed to.
// Qt 对无彩色（灰/黑/白）返回 hsvHue 为 -1，故由调用方传入要收敛到的下限值。
// The floor stays with the consumer on purpose: this file must not invent a hue
// policy, and both consumers keep using their Enums token for it.
// 下限有意留在消费者侧：本文件不应自行发明色相策略，两处消费者仍各自使用 Enums token。
//
// alpha is returned as the raw 0..1 channel; scaling to the dialog's integer
// range stays with the caller. alpha 按原始 0..1 返回，缩放到对话框整数区间由调用方负责。
function decompose(color, achromaticHue) {
    return {
        hue: color.hsvHue >= achromaticHue ? color.hsvHue : achromaticHue,
        saturation: color.hsvSaturation,
        brightness: color.hsvValue,
        alpha: color.a
    }
}

// Build a colour from HSV components and a 0..1 alpha.
// 用 HSV 分量与 0..1 的 alpha 组装颜色。
function compose(hue, saturation, brightness, alpha) {
    return Qt.hsva(hue, saturation, brightness, alpha)
}
