// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import PrismQML
import PrismQML as Fluent

// FeedbackNotificationMenuShowcase - Notification surface menu demo 通知承载面菜单演示
Item {
    id: root

    // ==================== Required Props 必需属性 ====================
    required property Item notificationParent

    // ==================== Internal Props 内部属性 ====================
    readonly property int _position: Enums.notification.posTopLeft
    readonly property string _title:
        Fluent.Translator.tr("gallery_f56c6c82203b33f6", Fluent.Translator._v)
    readonly property string _message:
        Fluent.Translator.tr("gallery_a59f733a80883766", Fluent.Translator._v)

    // ==================== Internal Methods 内部方法 ====================
    function _showToast(mode) {
        if (mode === "desktop") {
            NotificationManager.desktop.info(
                _title, _message, Enums.duration.notification, _position
            )
            return
        }
        NotificationManager.toast.info(
            notificationParent, _title, _message,
            Enums.duration.notification, _position,
            mode === "outside"
                ? Enums.notification.mode_window_outside
                : Enums.notification.mode_in_app
        )
    }

    function _showInfoBar(mode) {
        if (mode === "desktop") {
            NotificationManager.desktop.infoBar(
                "info", _title, _message,
                Enums.duration.notification, _position
            )
            return
        }
        NotificationManager.infoBar.info(
            notificationParent, _title, _message,
            Enums.duration.notification, _position,
            mode === "outside"
                ? Enums.notification.mode_window_outside
                : Enums.notification.mode_in_app
        )
    }

    function _showNotification(actionId) {
        var parts = actionId.split(".")
        if (parts.length !== 2) return
        if (parts[0] === "toast") _showToast(parts[1])
        else if (parts[0] === "infobar") _showInfoBar(parts[1])
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: notificationCard.implicitWidth
    implicitHeight: notificationCard.implicitHeight
    width: parent ? parent.width : implicitWidth

    // ==================== Content 内容 ====================
    MenuCore {
        id: notificationMenu

        objectName: "galleryNotificationModeMenu"
        onActionTriggered: (actionId) => root._showNotification(actionId)
        Component.onCompleted: {
            addSubmenu("Toast", "", toastMenuComponent)
            addSubmenu("InfoBar", "", infoBarMenuComponent)
        }
    }

    Component {
        id: toastMenuComponent

        MenuCore {
            Component.onCompleted: {
                addAction(
                    Fluent.Translator.tr("gallery_de907d10df98b498", Fluent.Translator._v),
                    "", "", { "actionId": "toast.in_app" }
                )
                addAction("Window outside", "", "", { "actionId": "toast.outside" })
                addAction("Desktop", "", "", { "actionId": "toast.desktop" })
            }
        }
    }

    Component {
        id: infoBarMenuComponent

        MenuCore {
            Component.onCompleted: {
                addAction(
                    Fluent.Translator.tr("gallery_de907d10df98b498", Fluent.Translator._v),
                    "", "", { "actionId": "infobar.in_app" }
                )
                addAction("Window outside", "", "", { "actionId": "infobar.outside" })
                addAction("Desktop", "", "", { "actionId": "infobar.desktop" })
            }
        }
    }

    ExampleCard {
        id: notificationCard

        title: "NotificationManager"
        description: "Toast / InfoBar: in-app / window-outside / desktop"

        Button {
            objectName: "galleryNotificationModeButton"
            style: Enums.button.style_primary
            feature: Enums.button.feature_dropdown
            text: "NotificationManager"
            menu: notificationMenu
        }
    }
}
