// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import PrismQML

// PrismSkinCompareStrip - Three skin screenshot strip 三皮肤截图对照条
Item {
    id: control

    // ==================== Internal Props 内部属性 ====================
    readonly property string _themeSuffix: Enums.isDark ? "dark" : "light"
    readonly property int _snapshotWidth: 250
    readonly property int _snapshotHeight: 206
    readonly property int _imageHeight: 162
    readonly property var _snapshots: [
        {
            "label": "Fluent",
            "source": "qrc:/image/prism-design/skin-compare-fluent-" + _themeSuffix + ".png"
        },
        {
            "label": "Neobrutalism",
            "source": "qrc:/image/prism-design/skin-compare-neobrutalism-" + _themeSuffix + ".png"
        },
        {
            "label": "Prism Design",
            "source": "qrc:/image/prism-design/skin-compare-prism-design-" + _themeSuffix + ".png"
        }
    ]

    // ==================== Size 尺寸 ====================
    implicitWidth: snapshotFlow.implicitWidth
    implicitHeight: snapshotFlow.implicitHeight

    // ==================== Content 内容 ====================
    Flow {
        id: snapshotFlow
        width: parent ? parent.width : implicitWidth
        spacing: Enums.spacing.l

        Repeater {
            model: control._snapshots

            Rectangle {
                width: control._snapshotWidth
                height: control._snapshotHeight
                radius: Enums.isPrismDesign ? Enums.prismDesign.radiusCard : Enums.radius.large
                color: Enums.cardColor
                border.width: Enums.border.thin
                border.color: Enums.borderColor

                Column {
                    anchors.fill: parent
                    anchors.margins: Enums.spacing.m
                    spacing: Enums.spacing.s

                    Text {
                        text: modelData.label
                        font.family: Enums.fontFamily
                        font.pixelSize: Enums.typography.body
                        font.bold: true
                        color: Enums.textColor.primary
                    }

                    Image {
                        width: parent.width
                        height: control._imageHeight
                        source: modelData.source
                        fillMode: Image.PreserveAspectFit
                        asynchronous: false
                        cache: false
                    }
                }
            }
        }
    }
}
