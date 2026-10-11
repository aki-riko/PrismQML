// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

// Import components 导入组件
import PrismQML
import PrismQML as Fluent

// Media components page 媒体组件页面
Item {
    id: root

    ScrollArea {
        anchors.fill: parent

        Column {
            width: parent ? parent.width : 0
            spacing: Fluent.Enums.spacing.xxl

            // Page title 页面标题
            Column {
                width: parent ? parent.width : 0
                spacing: Fluent.Enums.spacing.xs
                Text { text: Fluent.Translator.tr("gallery_fa33e10009759859", Fluent.Translator._v); font.pixelSize: Fluent.Enums.typography.displayLarge; font.bold: true; color: Fluent.Enums.textColor.primary; font.family: Fluent.Enums.fontFamily }
            }

        }
    }
}
