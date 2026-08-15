// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../utils"
import "../../containers/ScrollBar"

// MenuContent - Menu visual content host 菜单视觉内容承载层
// Owns scrolling and child action wiring while MenuCore keeps public APIs 负责滚动与子项连接，MenuCore 保留公开 API
Item {
    id: content

    // ==================== Required Props 必需属性 ====================
    required property var menu

    // ==================== Public Props 公开属性 ====================
    default property alias actions: itemsColumn.data
    readonly property alias itemContainer: itemsColumn

    // ==================== Content 内容 ====================
    Flickable {
        id: menuFlickable

        anchors.fill: parent
        anchors.rightMargin: content.menu._needsScroll
            ? Enums.comboBoxMetrics.scrollBarRightMargin : 0
        contentWidth: width
        contentHeight: itemsColumn.height
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        interactive: false

        PopupSmoothScroll {
            flickable: menuFlickable
            enabled: content.menu._needsScroll
        }

        Column {
            id: itemsColumn

            property var _autoBoundActions: []

            width: parent.width

            onChildrenChanged: {
                content.menu._syncMenuItems()
                var items = content.menu._menuItems()
                for (var i = 0; i < items.length; i++) {
                    var c = items[i]
                    if (c && c.triggered
                            && _autoBoundActions.indexOf(c) === -1) {
                        _autoBoundActions.push(c)
                        if (c.pressed) {
                            c.pressed.connect(function() {
                                content.menu.stabilizeInteraction()
                            })
                        }
                        if (c.hoveredChanged) {
                            c.hoveredChanged.connect((function(child) {
                                return function() {
                                    if (child.hovered && !child.hasSubmenu) {
                                        content.menu._closeOpenSubmenu()
                                    }
                                }
                            })(c))
                        }
                        c.triggered.connect((function(child) {
                            return function() {
                                content.menu.actionTriggered(
                                    child.actionId || child.text || ""
                                )
                                content.menu.close()
                            }
                        })(c))
                    }
                }
                Qt.callLater(content.menu._updateSize)
            }
        }
    }

    Loader {
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.margins: Enums.spacing.xxs
        width: Enums.comboBoxMetrics.scrollBarWidth
        active: content.menu._needsScroll
        sourceComponent: ScrollBarEntry {
            flickable: menuFlickable
            width: Enums.comboBoxMetrics.scrollBarWidth
        }
    }
}
