// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."
import "../containers/Separator"

// MenuSeparator - Menu separator (wraps Separator) 菜单分隔线
Item {
    width: parent ? parent.width : 100
    height: Enums.controlSize.menuSeparatorHeight
    
    Separator {
        anchors.centerIn: parent
        lineLength: parent.width - Enums.spacing.m
    }
}
