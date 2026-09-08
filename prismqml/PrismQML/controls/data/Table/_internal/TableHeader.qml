// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../../../"
import "../../../containers/Separator"
import "../../../data"
import "../../../icons"
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
            readonly property bool sortable: root.table.sortingEnabled && !!columnData.role
            readonly property bool sorted: root.table.sortColumn === index

            width: root.table._columnPixelWidths[index] || 60
            height: parent.height

            MouseArea {
                id: headerHoverArea
                anchors.fill: parent
                hoverEnabled: true
                acceptedButtons: Qt.NoButton
            }

            Row {
                anchors.centerIn: parent
                spacing: Enums.spacing.xs

                Label {
                    type: Enums.label.type_caption
                    text: headerItem.columnData.text || ""
                    font.bold: true
                    color: root.table.secondaryColor
                }

                Icon {
                    visible: headerItem.sortable
                    icon: headerItem.sorted
                        ? (root.table.sortOrder === 0 ? "ArrowSortUp" : "ArrowSortDown")
                        : "ArrowSort"
                    iconSize: Enums.typography.caption
                    color: root.table.secondaryColor
                }
            }

            MouseArea {
                id: sortArea

                anchors.fill: parent
                enabled: headerItem.sortable
                hoverEnabled: true
                cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                onClicked: root.table.toggleSort(index)
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

                    HoverBehavior on opacity {
                        active: headerItem.hovered && !resizeHandle.pressed
                        enterDuration: Enums.duration.fast
                        easingType: Easing.OutCubic
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
