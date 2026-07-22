// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "../data/Badge"

// TimelineGraphLabels - Graph row labels 图模式行标签
Flow {
    id: control

    required property var labels

    spacing: Enums.spacing.s

    Repeater {
        model: control.labels || []
        delegate: Tag {
            required property var modelData
            text: modelData.text || ""
            status: modelData.status === undefined
                ? Enums.statusLevel.info : modelData.status
            showDot: false
        }
    }
}
