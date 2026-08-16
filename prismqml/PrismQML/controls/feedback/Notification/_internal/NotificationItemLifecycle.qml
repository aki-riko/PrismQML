// NotificationItemLifecycle - in-window notification lifecycle 窗口内通知生命周期
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

import QtQuick
import "../../../.."

QtObject {
    id: lifecycle

    // ==================== Required Props 必需属性 ====================
    required property var stackManager

    // ==================== Public Methods 公开方法 ====================
    function create(component, parentItem, properties, position, stackGap) {
        if (component.status !== Component.Ready) {
            console.error("NotificationManager: notification component not ready:",
                component.errorString())
            return null
        }

        var item = component.createObject(parentItem, properties)
        if (!item) return null

        item.z = Enums.zIndex.overlay
        stackManager.addToStack(item, position)
        if (stackGap === undefined) {
            stackManager.setPosition(item, parentItem, position)
        } else {
            stackManager.setPosition(item, parentItem, position, stackGap)
        }
        item.closed.connect(function() {
            stackManager.removeFromStack(item, position)
            item.destroy()
        })
        item.show()
        return item
    }
}
