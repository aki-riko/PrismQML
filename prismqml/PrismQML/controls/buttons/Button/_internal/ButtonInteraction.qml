// ButtonInteraction - Main button pointer interaction 主按钮指针交互
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

import QtQuick
import "../../../.."

// ButtonInteraction - Keeps pointer handling outside the button shell 将指针处理从按钮壳中拆出
MouseArea {
    id: interaction

    // ==================== Required Props 必需属性 ====================
    required property var button
    required property var featureItem

    anchors.fill: parent
    hoverEnabled: true
    enabled: button.enabled && !button.loading
              && !button._countdownActive
              && button.feature !== Enums.button.feature_split
    visible: button.feature !== Enums.button.feature_split
    cursorShape: enabled && button.style === Enums.button.style_hyperlink
                 ? Qt.PointingHandCursor : Qt.ArrowCursor

    onClicked: {
        if (button.feature === Enums.button.feature_toggle) {
            button.checked = !button.checked
            button.toggled(button.checked)
        }
        if (button.feature === Enums.button.feature_dropdown
                && (button.menu !== null && button.menu !== undefined
                    || button._safeMenuItems.length > 0)) {
            if (featureItem) featureItem.openMenu()
            return
        }
        if (button.feature === Enums.button.feature_countdown) {
            button._countdownInitialWidth = button.width
            button._countdownRemaining = button.countdown
            button._countdownActive = true
        }
        button.clicked()
    }

    onPressed: {
        // Give the button focus so other inputs lose focus. 让按钮获得焦点，使其它输入控件失焦。
        button.forceActiveFocus()
        button.buttonPressed()
    }
    onReleased: button.released()
    onContainsMouseChanged: {
        if (containsMouse) button._prewarmMenu()
    }
    onDoubleClicked: (mouse) => {
        // Replay the suppressed second activation before forwarding the double-click signal 重放被抑制的第二次激活，再转发双击信号
        clicked(mouse)
        button.doubleClicked()
    }
}
