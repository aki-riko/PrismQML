// ButtonDropdownMenuHost - Native popup and item content 按钮下拉原生弹层与内容
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../menus"
import "../../../utils"
import "../../../containers/ScrollBar"

Item {
    id: host

    required property var dropdownControl
    required property var skinContext
    required property int fontSize
    readonly property var menu: internalMenuLoader.item

    Loader {
        id: internalMenuLoader
        active: host.dropdownControl._internalMenuRequested

        sourceComponent: PopupWindowCore {
            id: dropDownMenu

            readonly property int _itemsHeight: {
                var height = 0
                for (var i = 0; i < host.dropdownControl._safeMenuItems.length; i++) {
                    var item = host.dropdownControl._safeMenuItems[i]
                    var text = item && typeof item === "object" ? (item.text || item) : (item || "")
                    height += text === "-"
                        ? host.skinContext.controlSize.menuSeparatorHeight
                        : host.skinContext.comboBoxMetrics.itemHeight
                }
                return height
            }
            readonly property int _maxContentHeight: Math.max(
                0, host.skinContext.comboBoxMetrics.popupMaxHeight - 2 * contentPadding)
            readonly property bool _needsScroll: _itemsHeight > _maxContentHeight
            readonly property var _textMeasure: menuContentLoader.item
                ? menuContentLoader.item.textMeasure : null

            skinContext: host.skinContext
            implicitContentHeight: Math.min(_itemsHeight, _maxContentHeight)
            closeOnClickOutside: true
            useQtPopupWindow: true

            Loader {
                id: menuContentLoader
                anchors.fill: parent
                active: host.dropdownControl._menuContentRequested

                sourceComponent: Item {
                    readonly property alias textMeasure: textMeasure

                    TextMetrics {
                        id: textMeasure
                        font.family: host.skinContext.fontFamily
                        font.pixelSize: host.fontSize > 0
                            ? host.fontSize : host.skinContext.typography.body
                    }

                    Flickable {
                        id: menuFlickable
                        anchors.fill: parent
                        anchors.rightMargin: dropDownMenu._needsScroll
                            ? host.skinContext.comboBoxMetrics.scrollBarRightMargin : 0
                        contentWidth: width
                        contentHeight: menuColumn.height
                        clip: true
                        boundsBehavior: Flickable.StopAtBounds
                        interactive: false

                        PopupSmoothScroll {
                            flickable: menuFlickable
                            enabled: dropDownMenu._needsScroll
                        }

                        Column {
                            id: menuColumn
                            width: parent.width

                            Repeater {
                                model: host.dropdownControl._safeMenuItems

                                MenuDelegate {
                                    width: menuColumn.width
                                    text: modelData && typeof modelData === "object"
                                        ? (modelData.text || modelData) : (modelData || "")
                                    icon: modelData && typeof modelData === "object"
                                        ? (modelData.icon || "") : ""
                                    isSeparator: text === "-"
                                    onClicked: {
                                        dropDownMenu.close()
                                        host.dropdownControl.menuItemClicked(index, text)
                                    }
                                }
                            }
                        }
                    }

                    Loader {
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        anchors.margins: host.skinContext.spacing.xxs
                        width: host.skinContext.comboBoxMetrics.scrollBarWidth
                        active: dropDownMenu._needsScroll
                        sourceComponent: ScrollBarEntry {
                            flickable: menuFlickable
                            width: host.skinContext.comboBoxMetrics.scrollBarWidth
                        }
                    }
                }
            }
        }
    }
}
