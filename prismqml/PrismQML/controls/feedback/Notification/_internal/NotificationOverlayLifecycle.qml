// NotificationOverlayLifecycle - overlay creation and cleanup lifecycle 通知覆盖层创建与清理生命周期
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

import QtQuick

QtObject {
    id: lifecycle

    // ==================== Required Props 必需属性 ====================
    required property var stackManager

    // ==================== Public Methods 公开方法 ====================
    function create(overlayComponent, notificationComponent, overlayProperties,
                    notificationProperties, position, stackKind) {
        if (overlayComponent.status !== Component.Ready) {
            console.error("NotificationManager: overlay component not ready:",
                overlayComponent.errorString())
            return null
        }

        var overlay = overlayComponent.createObject(null, overlayProperties)
        if (!overlay) return null

        if (notificationComponent.status !== Component.Ready) {
            overlay.destroy()
            return null
        }

        var notification = notificationComponent.createObject(
            overlay.content, notificationProperties
        )
        if (!notification) {
            overlay.destroy()
            return null
        }

        overlay.notificationItem = notification
        notification.anchors.centerIn = overlay.content
        if (stackKind === "desktop") {
            stackManager.addToDesktopStack(overlay, position)
        } else {
            stackManager.addToOutsideStack(overlay, position)
        }

        notification.closed.connect(function() { overlay.hide() })
        overlay.closed.connect(function() {
            if (stackKind === "desktop") {
                stackManager.removeFromDesktopStack(overlay, position)
            } else {
                stackManager.removeFromOutsideStack(overlay, position)
            }
            notification.destroy()
            overlay.destroy()
        })

        notification.visible = true
        overlay.show()
        return notification
    }
}
