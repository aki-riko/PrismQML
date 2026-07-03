// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../controls/feedback/Notification"

// DesktopNotificationCloser - Deferred close-path bridge for NotificationManager
QtObject {
    function closeAll() {
        NotificationManager.closeAllDesktopNotifications()
    }
}
