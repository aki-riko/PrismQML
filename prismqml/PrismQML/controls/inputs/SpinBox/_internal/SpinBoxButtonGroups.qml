// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import ".."

// SpinBoxButtonGroups - Spin button component factories 微调按钮组件工厂
// Keeps dynamic button definitions separate while SpinBoxCore owns the Loader.
// 将动态按钮定义分离，同时由 SpinBoxCore 保留 Loader 所有权。
Item {
    id: buttonGroups

    // ==================== Required Props 必需属性 ====================
    required property var spinControl

    // ==================== Public Props 公开属性 ====================
    property alias inlineButtonsComponent: inlineButtonsComponent
    property alias compactButtonsComponent: compactButtonsComponent

    // ==================== Size 尺寸 ====================
    width: 0
    height: 0
    visible: false

    // ==================== Content 内容 ====================
    Component {
        id: inlineButtonsComponent

        Item {
            readonly property alias increaseButton: increaseBtn
            readonly property alias decreaseButton: decreaseBtn
            readonly property real textLeftInset: Enums.spacing.xs + decreaseBtn.width + Enums.spacing.xs
            readonly property real textRightInset: Enums.spacing.xs + increaseBtn.width + Enums.spacing.xs

            // Decrease button for inline mode 内联模式减号按钮
            SpinBoxButton {
                id: decreaseBtn
                anchors.left: parent.left
                anchors.leftMargin: Enums.spacing.xs
                anchors.verticalCenter: parent.verticalCenter
                icon: Enums.icon.subtract
                enabled: buttonGroups.spinControl.enabled
                z: Enums.zIndex.inputControls
                onClicked: buttonGroups.spinControl.decrease()
                onButtonPressed: buttonGroups.spinControl._startAutoRepeat(false)
                onReleased: buttonGroups.spinControl._stopAutoRepeat()
            }

            // Increase button for inline mode 内联模式加号按钮
            SpinBoxButton {
                id: increaseBtn
                anchors.right: parent.right
                anchors.rightMargin: Enums.spacing.xs
                anchors.verticalCenter: parent.verticalCenter
                icon: Enums.icon.add
                enabled: buttonGroups.spinControl.enabled
                z: Enums.zIndex.inputControls
                onClicked: buttonGroups.spinControl.increase()
                onButtonPressed: buttonGroups.spinControl._startAutoRepeat(true)
                onReleased: buttonGroups.spinControl._stopAutoRepeat()
            }
        }
    }

    Component {
        id: compactButtonsComponent

        Item {
            readonly property alias increaseButton: compactUpBtn
            readonly property alias decreaseButton: compactDownBtn
            readonly property real textLeftInset: Enums.spacing.xs
            readonly property real textRightInset: Enums.spacing.xxs + compactBtnContainer.width + Enums.spacing.xs

            // Compact buttons on the right 右侧紧凑按钮
            // Inline mode: two separate clickable buttons 内联模式：两个独立可点击按钮
            Item {
                id: compactBtnContainer
                anchors.right: parent.right
                anchors.rightMargin: Enums.spacing.xxs
                anchors.verticalCenter: parent.verticalCenter
                width: Enums.spacing.xl + Enums.spacing.xs
                height: buttonGroups.spinControl.height - Enums.spacing.xs
                z: Enums.zIndex.inputControls

                // Up button (extends ButtonCore) 增加按钮(继承ButtonCore)
                MiniSpinButton {
                    id: compactUpBtn
                    anchors.top: parent.top
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: parent.width
                    height: parent.height / 2
                    icon: Enums.icon.chevron_up
                    enabled: buttonGroups.spinControl.enabled
                    onClicked: buttonGroups.spinControl.increase()
                    onButtonPressed: buttonGroups.spinControl._startAutoRepeat(true)
                    onReleased: buttonGroups.spinControl._stopAutoRepeat()
                }

                // Down button (extends ButtonCore) 减少按钮(继承ButtonCore)
                MiniSpinButton {
                    id: compactDownBtn
                    anchors.bottom: parent.bottom
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: parent.width
                    height: parent.height / 2
                    icon: Enums.icon.chevron_down
                    enabled: buttonGroups.spinControl.enabled
                    onClicked: buttonGroups.spinControl.decrease()
                    onButtonPressed: buttonGroups.spinControl._startAutoRepeat(false)
                    onReleased: buttonGroups.spinControl._stopAutoRepeat()
                }
            }
        }
    }
}
