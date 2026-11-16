// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../utils"

// BottomSheetGrabber - Top drag handle of a bottom sheet 底部弹层顶部拖拽手柄
// Only the handle drags, so scrolling content inside the sheet never competes with it.
// 只有手柄可拖，弹层内部的滚动内容不会与它争抢手势。
Item {
    id: grabber

    // ==================== Required Props 必需属性 ====================
    required property var sheetControl

    // ==================== Internal Props 内部属性 ====================
    readonly property var _skin: sheetControl._skin

    // ==================== Signals 信号 ====================
    signal dragStarted()
    signal dragMoved(real translationY)
    signal dragReleased(real translationY, real velocityY)
    signal tapped()

    objectName: "bottomSheetGrabber"
    height: _skin.sheet.grabberHeight
    enabled: sheetControl._isOpen && sheetControl._sheetAbove === null
    // Screen readers press it to cycle detents, matching a tap 读屏器按下即切换停靠，与点按一致
    Accessible.role: AccessibilityHelper.roleValue(Enums.accessibility.role_button)
    Accessible.name: { Translator._v; return Translator.tr("sheet_grabber") }
    Accessible.onPressAction: if (grabber.enabled) grabber.tapped()

    // ==================== Content 内容 ====================
    Rectangle {
        anchors.centerIn: parent
        width: grabber._skin.sheet.grabberBarWidth
        height: grabber._skin.sheet.grabberBarHeight
        radius: height / 2
        color: grabber._skin.borderStrongColor
    }

    DragHandler {
        id: dragHandler

        property real lastTranslationY: 0
        property real lastVelocityY: 0
        property real lastSampleTime: 0

        target: null
        xAxis.enabled: false
        yAxis.enabled: true

        onActiveChanged: {
            if (active) {
                lastTranslationY = 0
                lastVelocityY = 0
                lastSampleTime = Date.now()
                grabber.dragStarted()
            } else {
                // A finger that paused before lifting is not flicking 停顿后抬起不算甩动
                var stale = Date.now() - lastSampleTime > grabber._skin.sheet.velocityStaleMs
                grabber.dragReleased(lastTranslationY, stale ? 0 : lastVelocityY)
            }
        }
        // Velocity is measured here instead of read from centroid.velocity: that value
        // is derived from event timestamps, and synthetic or batched events that share
        // one timestamp report it as hundreds of thousands of px/s.
        // 速度在此自行测量，不读 centroid.velocity：后者由事件时间戳推导，合成或批量
        // 事件共用同一时间戳时会报出每秒数十万像素。
        onActiveTranslationChanged: {
            if (!active) return
            var now = Date.now()
            var elapsed = now - lastSampleTime
            if (elapsed > 0) {
                lastVelocityY = (activeTranslation.y - lastTranslationY) * 1000 / elapsed
                lastSampleTime = now
            }
            lastTranslationY = activeTranslation.y
            grabber.dragMoved(lastTranslationY)
        }
    }

    TapHandler {
        onTapped: grabber.tapped()
    }
}
