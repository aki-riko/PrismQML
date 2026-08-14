// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "../icons"
import "../buttons"
import "../data"

// Paginator - Fluent Design style pagination 分页器
// Features sliding page changes, hover effects, and accent highlights 支持滑动翻页、悬停效果和强调色高亮
Item {
    id: root
    
    // ==================== Public Props 公开属性 ====================
    property int currentPage: 1
    property int totalPages: 10
    property int visiblePages: 5
    property color accentColor: Enums.accentColor
    property bool showPrevNext: true

    // ==================== Internal Props 内部属性 ====================
    readonly property real _buttonSize: Enums.controlSize.buttonHeight
    readonly property real _spacing: Enums.spacing.xxs
    readonly property real _itemWidth: _buttonSize + _spacing
    readonly property int _pageRadius: Enums.radius.small
    readonly property color _pageIndicatorColor: root.accentColor
    readonly property color _pageHoverColor: Enums.stateColor.hover
    readonly property color _pageIdleColor: Enums.transparent
    readonly property color _pageTextColor: Enums.foregroundColor
    readonly property color _pageSelectedTextColor: Enums.accentForeground
    readonly property int _pageOffset: {
        var centerIndex = Math.floor(root.visiblePages / 2)
        var pageIndex = root.currentPage - 1
        var maxOffset = root.totalPages - root.visiblePages
        return Math.max(0, Math.min(maxOffset, pageIndex - centerIndex))
    }
    readonly property int _windowStartPage: _pageOffset + 1
    readonly property int _windowEndPage: Math.min(
        root.totalPages, _windowStartPage + root.visiblePages - 1
    )
    property int _loadedPageStart: _windowStartPage
    property int _loadedPageEnd: _windowEndPage
    readonly property int _loadedPageCount: Math.max(
        0, _loadedPageEnd - _loadedPageStart + 1
    )

    // ==================== Signals 信号 ====================
    signal pageChanged(int page)

    // ==================== Internal Methods 内部方法 ====================
    function _expandLoadedPages() {
        var total = Math.max(0, root.totalPages)
        if (total === 0) {
            _loadedPageStart = 1
            _loadedPageEnd = 0
            return
        }
        var nextStart = Math.max(1, Math.min(_windowStartPage, total))
        var nextEnd = Math.max(nextStart, Math.min(_windowEndPage, total))
        if (_loadedPageEnd < _loadedPageStart) {
            _loadedPageStart = nextStart
            _loadedPageEnd = nextEnd
            return
        }
        _loadedPageStart = Math.min(Math.max(1, _loadedPageStart), nextStart)
        _loadedPageEnd = Math.min(total, Math.max(_loadedPageEnd, nextEnd))
    }

    function _settleLoadedPages() {
        var total = Math.max(0, root.totalPages)
        if (total === 0) {
            _loadedPageStart = 1
            _loadedPageEnd = 0
            return
        }
        _loadedPageStart = Math.max(1, Math.min(_windowStartPage, total))
        _loadedPageEnd = Math.max(
            _loadedPageStart, Math.min(_windowEndPage, total)
        )
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: pagerRow.implicitWidth
    implicitHeight: _buttonSize
    on_WindowStartPageChanged: _expandLoadedPages()
    on_WindowEndPageChanged: _expandLoadedPages()

    // ==================== Content 内容 ====================
    Timer {
        id: pageSettleTimer

        interval: 0
        repeat: false
        onTriggered: {
            if (!pageSlideAnimation.running) root._settleLoadedPages()
        }
    }

    Row {
        id: pagerRow
        anchors.centerIn: parent
        spacing: _spacing
        
        // Previous button 上一页按钮
        Button {
            visible: root.showPrevNext
            style: Enums.button.style_transparent
            icon: Enums.icon.chevron_left
            iconSize: Enums.iconSize.xs
            implicitWidth: root._buttonSize
            implicitHeight: root._buttonSize
            flat: true
            enabled: root.currentPage > 1
            onClicked: {
                root.currentPage--
                root.pageChanged(root.currentPage)
            }
        }
        
        // Page-number viewport 页码视口
        Item {
            id: viewport
            width: root.visiblePages * root._buttonSize + (root.visiblePages - 1) * root._spacing
            height: root._buttonSize
            clip: true
            
            // Inner container with all pages 包含所有页码的内部容器
            Item {
                id: innerContainer

                width: root.totalPages * root._itemWidth
                height: root._buttonSize

                // Slide to show current page centered 滑动使当前页居中
                x: -root._pageOffset * root._itemWidth

                Behavior on x {
                    NumberAnimation {
                        id: pageSlideAnimation

                        duration: Enums.duration.medium
                        easing.type: Easing.OutCubic
                        onRunningChanged: {
                            if (!running) pageSettleTimer.restart()
                        }
                    }
                }

                // Sliding indicator 滑动指示器
                Rectangle {
                    id: indicator
                    width: root._buttonSize
                    height: root._buttonSize
                    radius: root._pageRadius
                    color: root._pageIndicatorColor
                    
                    x: (root.currentPage - 1) * root._itemWidth
                    
                    Behavior on x {
                        NumberAnimation {
                            duration: Enums.duration.medium
                            easing.type: Easing.OutCubic
                        }
                    }
                }
                
                // Keep the visible page window and any pages crossed by an active slide 保留可见页窗口以及当前滑动会经过的页码
                Repeater {
                    id: pageRepeater
                    model: root._loadedPageCount

                    delegate: Item {
                        id: pageDelegate
                        required property int index

                        property int pageNum: root._loadedPageStart + index
                        property bool isCurrentPage: pageNum === root.currentPage

                        x: (pageNum - 1) * root._itemWidth
                        width: root._buttonSize
                        height: root._buttonSize

                        // Hover background 悬停背景
                        Rectangle {
                            anchors.fill: parent
                            radius: root._pageRadius
                            color: pageMouseArea.containsMouse && !pageDelegate.isCurrentPage
                                   ? root._pageHoverColor : root._pageIdleColor
                            HoverBehavior on color {
                                active: pageMouseArea.containsMouse &&
                                        !pageDelegate.isCurrentPage
                                enterDuration: Enums.duration.fast
                            }
                        }

                        // Page number text 页码文字
                        Label {
                            anchors.centerIn: parent
                            type: Enums.label.type_body
                            text: pageDelegate.pageNum.toString()
                            color: pageDelegate.isCurrentPage
                                   ? root._pageSelectedTextColor
                                   : root._pageTextColor
                            Behavior on color {
                                ColorAnimation { duration: Enums.duration.fast }
                            }
                        }

                        MouseArea {
                            id: pageMouseArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                root.currentPage = pageDelegate.pageNum
                                root.pageChanged(pageDelegate.pageNum)
                            }
                        }
                    }
                }
            }
        }

        // Next button 下一页按钮
        Button {
            visible: root.showPrevNext
            style: Enums.button.style_transparent
            icon: Enums.icon.chevron_right
            iconSize: Enums.iconSize.xs
            implicitWidth: root._buttonSize
            implicitHeight: root._buttonSize
            flat: true
            enabled: root.currentPage < root.totalPages
            onClicked: {
                root.currentPage++
                root.pageChanged(root.currentPage)
            }
        }
    }
}
