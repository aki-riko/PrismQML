// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../../../"
import "../../../containers/Separator"
import "../../../data"
import QtQuick

// TableHeader - Header renderer for TableWidget 表格头部渲染器
Row {
    id: root

    // ==================== Required Props 必需属性 ====================
    required property var table

    anchors.fill: parent

    Repeater {
        model: root.table._safeColumns

        Item {
            id: headerItem

            readonly property var columnData: modelData || ({})

            // ==================== Readonly State 只读状态 ====================
            readonly property bool hovered: headerHoverArea.containsMouse

            width: root.table._columnPixelWidths[index] || 60
            height: parent.height

            MouseArea {
                id: headerHoverArea
                anchors.fill: parent
                hoverEnabled: true
                acceptedButtons: Qt.NoButton
            }

            Label {
                anchors.centerIn: parent
                type: Enums.label.type_caption
                text: headerItem.columnData.text || ""
                font.bold: true
                color: root.table.secondaryColor
            }

            Item {
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                width: Enums.spacing.s
                height: parent.height
                visible: index < root.table._safeColumns.length - 1

                Separator {
                    anchors.centerIn: parent
                    type: 1
                    lineWidth: Enums.border.medium
                    lineLength: parent.height * 0.5
                    opacity: headerItem.hovered || resizeHandle.pressed ? 1.0 : 0.4

                    Behavior on opacity {
                        NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic }
                    }
                }

                MouseArea {
                    id: resizeHandle

                    property real startX: 0
                    property real startWidth: 0

                    anchors.fill: parent
                    cursorShape: Qt.SplitHCursor

                    onPressed: (mouse) => {
                        startX = mouse.x
                        startWidth = headerItem.width
                    }

                    onPositionChanged: (mouse) => {
                        if (pressed) {
                            var delta = mouse.x - startX
                            var newWidth = Math.max(50, startWidth + delta)
                            var cols = (root.table._safeColumns || []).slice()
                            cols[index] = Object.assign({}, cols[index] || {}, {width: newWidth})
                            root.table.columns = cols
                        }
                    }
                }
            }
        }
    }
}
