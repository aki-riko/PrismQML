// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../data/Label"

// InputPlaceholderLabel - Unified placeholder text for input controls
// 所有 InputCore 派生控件（LineEditNormal / TagLineEdit / TextEditCore /
// ComboBoxCore editable popup 等）的占位文本统一组件。
//
// 抽出基类的目的：
//   - 修复 type_body 默认 WordWrap 在 anchors.fill 窄宽下换行的 bug
//     （placeholder 应单行省略，而不是撑成两 / 三行）
//   - 避免每处 placeholder Label 重复粘贴 wrapMode / elide / clip /
//     color / verticalAlignment 等相同样板代码
//
// 使用：
//   InputPlaceholderLabel {
//       anchors.fill: parent
//       text: control.placeholderText
//       visible: !parent.text && !parent.activeFocus
//   }
Label {
    id: control
    type: Enums.label.type_body
    color: Enums.textColor.disabled
    wrapMode: Text.NoWrap
    elide: Text.ElideRight
    clip: true
    verticalAlignment: Text.AlignVCenter
}
