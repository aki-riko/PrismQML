// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."
import "../controls/utils"

// WindowsCoreFrame - Window frame and title chrome 窗口框架与标题栏外观
Item {
    id: frameLayer

    // ==================== Required Props 必需属性 ====================
    required property var targetWindow

    // ==================== Public Props 公开属性 ====================
    property alias frame: windowFrame
    property alias contentData: contentContainer.data
    property alias leftPanelData: leftPanelContainer.data

    // ==================== Readonly State 只读状态 ====================
    readonly property var control: targetWindow

    // ==================== Content 内容 ====================
    // Main window frame. 主窗口框架。
    Rectangle {
        id: windowFrame

        anchors.fill: parent
        anchors.margins: control.margin
        radius: control.isMaximized ? 0 : control.windowRadius
        color: control.windowColor
        opacity: control._animOpacity
        scale: control._animScale
        clip: true

        // Window-level ticket paper keeps the title bar on the same grid.
        // 窗口级票据纸纹让标题栏与下方区域保持同一网格。
        TicketPaper {
            objectName: "windowTicketPaper"
            anchors.fill: parent
        }

        // Top layout title bar. 顶部布局标题栏。
        Rectangle {
            id: titleBar

            width: parent.width
            height: control._isLeftLayout ? 0 : control.titleBarHeight
            color: Enums.transparent
            z: Enums.zIndex.controls
            visible: !control._isLeftLayout

            Loader {
                anchors.fill: parent
                active: !control._isLeftLayout && control._titleChromeReady
                // Async instantiation keeps title-bar chrome off the first-frame critical path (~350ms faster cold start).
                // 异步实例化让标题栏 chrome 移出首帧关键路径（冷启动约快 350ms）；chrome 无外部 item 引用，异步安全。
                asynchronous: true
                sourceComponent: Component {
                    Item {
                        anchors.fill: parent

                        WindowIcon {
                            id: titleIcon

                            x: control.titleBarLeftMargin
                            anchors.verticalCenter: parent.verticalCenter
                            source: control.windowIcon
                            colored: control.windowIconColored
                            deferLoad: true
                            visible: control.windowIcon !== "" && !control._isLeftLayout
                        }

                        Text {
                            id: titleText

                            x: control.titleBarLeftMargin + (titleIcon.visible
                                ? Enums.window.titleIconSize + Enums.window.titleIconGap : 0)
                            text: control.windowTitle
                            font.family: Enums.fontFamily
                            font.pixelSize: Enums.typography.body
                            color: Enums.textColor.primary
                            anchors.verticalCenter: parent.verticalCenter
                            visible: !control._isLeftLayout
                        }

                        Row {
                            id: captionButtonsTop

                            objectName: "captionButtonsTop"
                            anchors.right: parent.right
                            anchors.top: parent.top
                            spacing: Enums.spacing.none
                            visible: !control._isLeftLayout
                            z: Enums.zIndex.controlsAbove  // Keep buttons above drag area 将按钮保持在拖动区域之上

                            TitleBarActionButton {
                                objectName: "captionActionButton"
                                targetWindow: control
                                icon: control.captionActionIcon
                                toolTipText: control.captionActionToolTip
                                actionEnabled: control.captionActionEnabled
                                buttonWidth: control.captionButtonWidth
                                buttonHeight: control.captionButtonHeight
                                visible: control._captionActionActive
                                onClicked: control.captionActionTriggered()
                            }

                            CaptionButton {
                                targetWindow: control
                                iconType: "minimize"
                                buttonWidth: control.captionButtonWidth
                                buttonHeight: control.captionButtonHeight
                                onClicked: control.animatedMinimize()
                            }

                            CaptionButton {
                                targetWindow: control
                                iconType: control.isMaximized ? "restore" : "maximize"
                                buttonWidth: control.captionButtonWidth
                                buttonHeight: control.captionButtonHeight
                                onClicked: control.isMaximized
                                    ? control.animatedRestore() : control.animatedMaximize()
                            }

                            CaptionButton {
                                targetWindow: control
                                iconType: "close"
                                buttonWidth: control.captionButtonWidth
                                buttonHeight: control.captionButtonHeight
                                buttonRadius: control.isMaximized ? 0 : control.windowRadius
                                onClicked: control.requestClose()
                            }
                        }

                        WindowDragHandle {
                            objectName: "topTitleBarDragArea"
                            anchors.fill: parent
                            anchors.rightMargin: control._captionControlsWidth
                            enableDrag: !control.isMaximized
                            enableDoubleClickMaximize: true
                            visible: !control._isLeftLayout
                            z: Enums.zIndex.background  // Keep below buttons 将其保持在按钮下方
                        }
                    }
                }
            }
        }

        // Left layout panel. 左侧布局面板。
        Rectangle {
            id: leftPanel

            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: control._isLeftLayout
                ? Math.max(control.leftPanelWidth, Enums.window.navPanelMinWidth) : 0
            color: Enums.transparent
            visible: control._isLeftLayout
            z: Enums.zIndex.controls

            // Left title bar area 左侧标题栏区域
            Rectangle {
                id: leftTitleBar

                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                height: control.titleBarHeight
                color: Enums.transparent

                Loader {
                    anchors.fill: parent
                    active: control._isLeftLayout && control._titleChromeReady
                    sourceComponent: Component {
                        Item {
                            anchors.fill: parent

                            // Window drag area 窗口拖拽区域
                            WindowDragHandle {
                                objectName: "leftTitleBarDragArea"
                                anchors.fill: parent
                                enableDrag: !control.isMaximized
                                enableDoubleClickMaximize: true
                            }

                            // Window icon 窗口图标
                            WindowIcon {
                                id: leftTitleIcon

                                anchors.left: parent.left
                                anchors.leftMargin: control.titleBarLeftMargin
                                anchors.verticalCenter: parent.verticalCenter
                                source: control.windowIcon
                                colored: control.windowIconColored
                                deferLoad: true
                            }

                            // Window title 窗口标题
                            Text {
                                id: leftTitleText

                                anchors.left: leftTitleIcon.visible
                                    ? leftTitleIcon.right : parent.left
                                anchors.leftMargin: leftTitleIcon.visible
                                    ? Enums.window.titleIconGap : control.titleBarLeftMargin
                                anchors.verticalCenter: parent.verticalCenter
                                text: control.windowTitle
                                font.family: Enums.fontFamily
                                font.pixelSize: Enums.typography.body
                                color: Enums.textColor.primary
                            }
                        }
                    }
                }
            }

            // Left panel content container 左侧面板内容容器
            Item {
                id: leftPanelContainer

                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: leftTitleBar.bottom
                anchors.bottom: parent.bottom
            }
        }

        // Vertical divider. 垂直分割线。
        Rectangle {
            id: verticalDivider

            anchors.left: leftPanel.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: Enums.border.thin
            color: Enums.stateColor.divider
            visible: control._isLeftLayout && control._titleChromeReady
            z: Enums.zIndex.controls
        }

        // Left-layout right title chrome. 左侧布局右侧标题栏 chrome。
        Loader {
            id: rightTitleChromeLoader

            objectName: "rightTitleChromeLoader"
            anchors.fill: parent
            active: control._isLeftLayout && control._titleChromeReady
            z: Enums.zIndex.controlsAbove
            sourceComponent: Component {
                Item {
                    objectName: "rightTitleChrome"
                    anchors.fill: parent

                    // Window drag area 窗口拖拽区域
                    WindowDragHandle {
                        objectName: "rightTitleBarDragArea"
                        anchors.left: parent.left
                        anchors.leftMargin: Math.max(
                            control.leftPanelWidth, Enums.window.navPanelMinWidth
                        ) + Enums.border.thin
                        anchors.right: parent.right
                        anchors.rightMargin: control._captionControlsWidth
                        anchors.top: parent.top
                        height: control.titleBarHeight
                        enableDrag: !control.isMaximized
                        enableDoubleClickMaximize: true
                        z: Enums.zIndex.background
                    }

                    // Window caption buttons 窗口标题栏按钮
                    Row {
                        id: captionButtonsRight

                        objectName: "captionButtonsRight"
                        anchors.right: parent.right
                        anchors.top: parent.top
                        width: control._captionControlsWidth
                        height: control.captionButtonHeight
                        spacing: Enums.spacing.none
                        z: Enums.zIndex.controlsAbove

                        TitleBarActionButton {
                            objectName: "captionActionButton"
                            targetWindow: control
                            icon: control.captionActionIcon
                            toolTipText: control.captionActionToolTip
                            actionEnabled: control.captionActionEnabled
                            buttonWidth: control.captionButtonWidth
                            buttonHeight: control.captionButtonHeight
                            visible: control._captionActionActive
                            onClicked: control.captionActionTriggered()
                        }

                        CaptionButton {
                            targetWindow: control
                            iconType: "minimize"
                            buttonWidth: control.captionButtonWidth
                            buttonHeight: control.captionButtonHeight
                            onClicked: control.animatedMinimize()
                        }

                        CaptionButton {
                            targetWindow: control
                            iconType: control.isMaximized ? "restore" : "maximize"
                            buttonWidth: control.captionButtonWidth
                            buttonHeight: control.captionButtonHeight
                            onClicked: control.isMaximized
                                ? control.animatedRestore() : control.animatedMaximize()
                        }

                        CaptionButton {
                            targetWindow: control
                            iconType: "close"
                            buttonWidth: control.captionButtonWidth
                            buttonHeight: control.captionButtonHeight
                            buttonRadius: control.isMaximized ? 0 : control.windowRadius
                            onClicked: control.requestClose()
                        }
                    }
                }
            }
        }

        // Content area. 内容区域。
        Item {
            id: contentContainer

            objectName: "contentContainer"
            anchors.top: control._isLeftLayout ? parent.top : titleBar.bottom
            anchors.left: control._isLeftLayout ? verticalDivider.right : parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom

            // Click background to clear input focus 点击背景清除输入焦点
            MouseArea {
                anchors.fill: parent
                z: Enums.zIndex.background  // Below all content 在所有内容下方
                onClicked: contentContainer.forceActiveFocus()
            }
        }

        // Border. 边框。
        Rectangle {
            anchors.fill: parent
            radius: parent.radius
            color: Enums.transparent
            border.width: Enums.border.thin
            border.color: Enums.borderColor
            z: Enums.zIndex.controls
        }
    }

    // Deferred resize handles. 延迟加载的调整大小手柄。
    Loader {
        id: resizeHandlesLoader

        anchors.fill: parent
        active: control._resizeHandlesReady
        asynchronous: true
        sourceComponent: Component {
            Item {
                anchors.fill: parent
                ResizeArea { targetWindow: control; edge: Qt.LeftEdge }
                ResizeArea { targetWindow: control; edge: Qt.RightEdge }
                ResizeArea { targetWindow: control; edge: Qt.TopEdge }
                ResizeArea { targetWindow: control; edge: Qt.BottomEdge }
            }
        }
    }
}
