// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../buttons"
import "../../data/Label"

// ShortcutEditorContent - Scrollable shortcut tags 滚动快捷键标签内容
// Keeps ShortcutEditor focused on recording, focus and public state.
// 将 ShortcutEditor 入口限制为录制、焦点与公开状态编排。
Flickable {
    id: content

    // ==================== Required Props 必需属性 ====================
    required property var editorControl
    required property var cancelButton

    // ==================== Public Props 公开属性 ====================
    property alias contentRow: contentRow

    anchors.left: parent.left
    anchors.right: cancelButton.visible ? cancelButton.left : parent.right
    anchors.verticalCenter: parent.verticalCenter
    anchors.leftMargin: Enums.spacing.m
    anchors.rightMargin: Enums.spacing.m
    height: Enums.controlSize.shortcutKeyHeight
    contentWidth: contentRow.width
    clip: true
    boundsBehavior: Flickable.StopAtBounds
    flickableDirection: Flickable.HorizontalFlick
    interactive: false  // Disable drag, use wheel only 禁用拖拽，仅用滚轮

    // Center content when not overflowing 内容不溢出时居中
    contentX: contentWidth <= width ? -(width - contentWidth) / 2 : 0

    // Wheel scroll handler 滚轮滚动处理
    MouseArea {
        anchors.fill: parent
        propagateComposedEvents: true
        onWheel: (wheel) => {
            if (editorControl._needsScroll) {
                editorControl._smoothScrollTo(editorControl._targetX - wheel.angleDelta.y * 0.5)
                wheel.accepted = true
            } else {
                wheel.accepted = false
            }
        }
        onClicked: (mouse) => {
            mouse.accepted = false
        }
        onPressed: (mouse) => {
            mouse.accepted = false
        }
    }

    Row {
        id: contentRow
        height: Enums.controlSize.shortcutKeyHeight
        spacing: Enums.spacing.s

        // Key tags container 按键标签容器
        Row {
            id: tagsRow
            anchors.verticalCenter: parent.verticalCenter
            spacing: Enums.spacing.xs
            visible: !editorControl.recording && editorControl.keyList.length > 0

            Repeater {
                model: editorControl.keyList

                // Single key tag using Button 单个按键标签复用Button
                Item {
                    width: Math.min(keyBtn.implicitWidth, Enums.controlSize.shortcutKeyMaxWidth)
                    height: Enums.controlSize.shortcutKeyHeight

                    Button {
                        id: keyBtn
                        anchors.fill: parent
                        style: Enums.button.style_primary
                        text: modelData
                        enabled: editorControl.enabled
                    }
                }
            }
        }

        // Placeholder text 占位符文本
        Label {
            type: Enums.label.type_body
            anchors.verticalCenter: parent.verticalCenter
            visible: !editorControl.recording && editorControl.keyList.length === 0
            text: editorControl.placeholderText
            color: Enums.textColor.tertiary
        }

        // Recording indicator 录制中指示器
        Label {
            type: Enums.label.type_body
            anchors.verticalCenter: parent.verticalCenter
            visible: editorControl.recording
            text: { Translator._v; return Translator.tr("recording") }
            color: Enums.accentColor

            SequentialAnimation on opacity {
                running: editorControl.recording
                loops: Animation.Infinite
                NumberAnimation { to: 0.4; duration: Enums.duration.dialog }
                NumberAnimation { to: 1; duration: Enums.duration.dialog }
            }
        }
    }
}
