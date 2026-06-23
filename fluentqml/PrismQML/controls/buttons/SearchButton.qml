// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."
import "Button"

// SearchButton - Simple search icon button 简单的搜索图标按钮
ButtonCore {
    style: Enums.button.style_transparent
    icon: Enums.icon.search
    implicitWidth: Enums.controlSize.closeButtonSize
    implicitHeight: Enums.controlSize.closeButtonSize
}
