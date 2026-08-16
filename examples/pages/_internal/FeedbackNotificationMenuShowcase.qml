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
    readonly property string _title:
        Fluent.Translator.tr("gallery_f56c6c82203b33f6", Fluent.Translator._v)
    readonly property string _message:
        Fluent.Translator.tr("gallery_a59f733a80883766", Fluent.Translator._v)
    readonly property var _positionOptions: [
        {
            "text": Fluent.Translator.tr("gallery_a59f733a80883766", Fluent.Translator._v),
            "position": Enums.notification.posTopLeft
        },
        {
            "text": Fluent.Translator.tr("gallery_58b9ea35c2e8aeb8", Fluent.Translator._v),
            "position": Enums.notification.posTop
        },
        {
            "text": Fluent.Translator.tr("gallery_37a1933200b062da", Fluent.Translator._v),
            "position": Enums.notification.posTopRight
        },
        {
            "text": Fluent.Translator.tr("gallery_14eeea875dc5c658", Fluent.Translator._v),
            "position": Enums.notification.posLeft
        },
        {
            "text": Fluent.Translator.tr("gallery_c4162f1fe3ee4751", Fluent.Translator._v),
            "position": Enums.notification.posCenter
        },
        {
            "text": Fluent.Translator.tr("gallery_ca75b858e7559fa3", Fluent.Translator._v),
            "position": Enums.notification.posRight
        },
        {
            "text": Fluent.Translator.tr("gallery_84eb9f344f50a101", Fluent.Translator._v),
            "position": Enums.notification.posBottomLeft
        },
        {
            "text": Fluent.Translator.tr("gallery_b90cd29061ebe116", Fluent.Translator._v),
            "position": Enums.notification.posBottom
        },
        {
            "text": Fluent.Translator.tr("gallery_3ff4eacca4b44501", Fluent.Translator._v),
            "position": Enums.notification.posBottomRight
        }
    ]

    // ==================== Internal Methods 内部方法 ====================
    function _positionActions(kind, surface) {
        var actions = []
        for (var index = 0; index < _positionOptions.length; index++) {
            var option = _positionOptions[index]
            if (surface === "outside"
                    && !Enums.notification.isWindowOutsidePosition(
                        option.position
                    )) {
                continue
            }
            actions.push({
                "text": option.text,
                "actionId": kind + "." + surface + "." + option.position
            })
        }
        return actions
    }

    function _isSurfaceValid(surface) {
        return surface === "in_app"
            || surface === "outside"
            || surface === "desktop"
    }

    function _isPositionValid(surface, position) {
        if (position < Enums.notification.posTopLeft
                || position > Enums.notification.posBottomRight
                || position !== Math.floor(position)) {
            return false
        }
        return surface !== "outside"
            || Enums.notification.isWindowOutsidePosition(position)
    }

    function _showToast(surface, position) {
        if (surface === "desktop") {
            NotificationManager.desktop.info(
                _title, _message, Enums.duration.notification, position
            )
            return
        }
        NotificationManager.toast.info(
            notificationParent, _title, _message,
            Enums.duration.notification, position,
            surface === "outside"
                ? Enums.notification.mode_window_outside
                : Enums.notification.mode_in_app
        )
    }

    function _showInfoBar(surface, position) {
        if (surface === "desktop") {
            NotificationManager.desktop.infoBar(
                "info", _title, _message,
                Enums.duration.notification, position
            )
            return
        }
        NotificationManager.infoBar.info(
            notificationParent, _title, _message,
            Enums.duration.notification, position,
            surface === "outside"
                ? Enums.notification.mode_window_outside
                : Enums.notification.mode_in_app
        )
    }

    function _showNotification(actionId) {
        var parts = actionId.split(".")
        if (parts.length !== 3) return
        if (parts[0] !== "toast" && parts[0] !== "infobar") return
        if (!_isSurfaceValid(parts[1])) return
        var position = Number(parts[2])
        if (!_isPositionValid(parts[1], position)) return
        if (parts[0] === "toast") _showToast(parts[1], position)
        else if (parts[0] === "infobar") _showInfoBar(parts[1], position)
    }

    // ==================== Size 尺寸 ====================
    objectName: "galleryNotificationMenuShowcase"
    implicitWidth: notificationCard.implicitWidth
    implicitHeight: notificationCard.implicitHeight
    width: parent ? parent.width : implicitWidth

    // ==================== Content 内容 ====================
    MenuCore {
        id: notificationMenu

        objectName: "galleryNotificationModeMenu"
        onActionTriggered: (actionId) => root._showNotification(actionId)
        Component.onCompleted: {
            addSubmenu(
                Fluent.Translator.tr("gallery_921acd914acd6c57", Fluent.Translator._v),
                "", toastMenuComponent
            )
            addSubmenu(
                Fluent.Translator.tr("gallery_8c2a398b8ff2e713", Fluent.Translator._v),
                "", infoBarMenuComponent
            )
        }
    }

    Component {
        id: toastMenuComponent

        MenuCore {
            Component.onCompleted: {
                addSubmenuActions(
                    Fluent.Translator.tr("gallery_e70b45ef67e88235", Fluent.Translator._v),
                    "", root._positionActions("toast", "in_app")
                )
                addSubmenuActions(
                    Fluent.Translator.tr("gallery_a84df74251f7f8da", Fluent.Translator._v),
                    "", root._positionActions("toast", "outside")
                )
                addSubmenuActions(
                    Fluent.Translator.tr("gallery_f48d334495f6e4f4", Fluent.Translator._v),
                    "", root._positionActions("toast", "desktop")
                )
            }
        }
    }

    Component {
        id: infoBarMenuComponent

        MenuCore {
            Component.onCompleted: {
                addSubmenuActions(
                    Fluent.Translator.tr("gallery_e70b45ef67e88235", Fluent.Translator._v),
                    "", root._positionActions("infobar", "in_app")
                )
                addSubmenuActions(
                    Fluent.Translator.tr("gallery_a84df74251f7f8da", Fluent.Translator._v),
                    "", root._positionActions("infobar", "outside")
                )
                addSubmenuActions(
                    Fluent.Translator.tr("gallery_f48d334495f6e4f4", Fluent.Translator._v),
                    "", root._positionActions("infobar", "desktop")
                )
            }
        }
    }

    ExampleCard {
        id: notificationCard

        title: Fluent.Translator.tr("gallery_7d40e038e4694fcc", Fluent.Translator._v)
        description: Fluent.Translator.tr("gallery_a598c8a19da5da6a", Fluent.Translator._v)

        Button {
            objectName: "galleryNotificationModeButton"
            style: Enums.button.style_primary
            feature: Enums.button.feature_dropdown
            text: Fluent.Translator.tr("gallery_7d40e038e4694fcc", Fluent.Translator._v)
            menu: notificationMenu
        }
    }
}
