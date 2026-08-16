// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

pragma Singleton
import QtQuick
import "../../.."
import "_internal"

// NotificationManager - Unified notification manager 统一通知管理器
// Manages InfoBar and Toast in window scope 管理窗口内的InfoBar和Toast
// Usage 用法:
//   NotificationManager.infoBar.info(parent, "title", "content")
//   NotificationManager.toast.success(parent, "title", "message")
QtObject {
    id: manager
    
    // ==================== Internal Props 内部属性 ====================
    property NotificationStackManager _stackManager: NotificationStackManager {}
    property NotificationItemLifecycle _itemLifecycle: NotificationItemLifecycle {
        stackManager: manager._stackManager
    }
    property NotificationOverlayLifecycle _overlayLifecycle: NotificationOverlayLifecycle {
        stackManager: manager._stackManager
    }
    
    // ==================== Readonly State 只读状态 ====================
    readonly property int posTopLeft: _stackManager.posTopLeft
    readonly property int posTop: _stackManager.posTop
    readonly property int posTopRight: _stackManager.posTopRight
    readonly property int posLeft: _stackManager.posLeft
    readonly property int posCenter: _stackManager.posCenter
    readonly property int posRight: _stackManager.posRight
    readonly property int posBottomLeft: _stackManager.posBottomLeft
    readonly property int posBottom: _stackManager.posBottom
    readonly property int posBottomRight: _stackManager.posBottomRight
    
    // Lazy components 延迟组件
    property var _infoBarComponent: null
    property var _toastComponent: null
    property var _desktopComponent: null
    property var _windowOutsideComponent: null
    
    // ==================== Public Props 公开属性 ====================
    // InfoBar namespace InfoBar 命名空间
    readonly property QtObject infoBar: QtObject {
        function info(parent, title, content, duration, position, mode) {
            return manager._createInfoBar(parent, "info", title, content, 
                duration !== undefined ? duration : Enums.duration.notification, 
                position !== undefined ? position : manager.posTopRight,
                mode !== undefined ? mode : Enums.notification.mode_in_app)
        }
        function attention(parent, title, content, duration, position, mode) {
            return manager._createInfoBar(parent, "attention", title, content, 
                duration !== undefined ? duration : Enums.duration.notification, 
                position !== undefined ? position : manager.posTopRight,
                mode !== undefined ? mode : Enums.notification.mode_in_app)
        }
        function success(parent, title, content, duration, position, mode) {
            return manager._createInfoBar(parent, "success", title, content, 
                duration !== undefined ? duration : Enums.duration.notification, 
                position !== undefined ? position : manager.posTopRight,
                mode !== undefined ? mode : Enums.notification.mode_in_app)
        }
        function warning(parent, title, content, duration, position, mode) {
            return manager._createInfoBar(parent, "warning", title, content, 
                duration !== undefined ? duration : Enums.duration.notification, 
                position !== undefined ? position : manager.posTopRight,
                mode !== undefined ? mode : Enums.notification.mode_in_app)
        }
        function error(parent, title, content, duration, position, mode) {
            return manager._createInfoBar(parent, "error", title, content, 
                duration !== undefined ? duration : Enums.duration.notification, 
                position !== undefined ? position : manager.posTopRight,
                mode !== undefined ? mode : Enums.notification.mode_in_app)
        }
        function processing(parent, title, content, duration, position, mode) {
            return manager._createInfoBar(parent, "processing", title, content, 
                duration !== undefined ? duration : Enums.duration.notification,
                position !== undefined ? position : manager.posTopRight,
                mode !== undefined ? mode : Enums.notification.mode_in_app)
        }
        function progressBar(parent, title, content, position, mode) {
            return manager._createInfoBarWithFeature(parent, "info", title, content, Enums.duration.notification,
                position !== undefined ? position : manager.posTopRight,
                Enums.notification.feature_progress_bar,
                mode !== undefined ? mode : Enums.notification.mode_in_app)
        }
        function indeterminateBar(parent, title, content, position, mode) {
            return manager._createInfoBarWithFeature(parent, "info", title, content, Enums.duration.notification,
                position !== undefined ? position : manager.posTopRight,
                Enums.notification.feature_indeterminate_bar,
                mode !== undefined ? mode : Enums.notification.mode_in_app)
        }
        function progressRing(parent, title, content, position, mode) {
            return manager._createInfoBarWithFeature(parent, "info", title, content, Enums.duration.notification,
                position !== undefined ? position : manager.posTopRight,
                Enums.notification.feature_progress_ring,
                mode !== undefined ? mode : Enums.notification.mode_in_app)
        }
        function indeterminateRing(parent, title, content, position, mode) {
            return manager._createInfoBarWithFeature(parent, "info", title, content, Enums.duration.notification,
                position !== undefined ? position : manager.posTopRight,
                Enums.notification.feature_indeterminate_ring,
                mode !== undefined ? mode : Enums.notification.mode_in_app)
        }
        function randomPosition() { return manager._stackManager.randomPosition() }
    }
    
    // Toast namespace Toast 命名空间
    readonly property QtObject toast: QtObject {
        function info(parent, title, message, duration, position, mode) {
            return manager._createToast(parent, "info", title, message, 
                duration !== undefined ? duration : Enums.duration.notification, 
                position !== undefined ? position : manager.posBottomRight,
                mode !== undefined ? mode : Enums.notification.mode_in_app)
        }
        function attention(parent, title, message, duration, position, mode) {
            return manager._createToast(parent, "attention", title, message, 
                duration !== undefined ? duration : Enums.duration.notification, 
                position !== undefined ? position : manager.posBottomRight,
                mode !== undefined ? mode : Enums.notification.mode_in_app)
        }
        function success(parent, title, message, duration, position, mode) {
            return manager._createToast(parent, "success", title, message, 
                duration !== undefined ? duration : Enums.duration.notification, 
                position !== undefined ? position : manager.posBottomRight,
                mode !== undefined ? mode : Enums.notification.mode_in_app)
        }
        function warning(parent, title, message, duration, position, mode) {
            return manager._createToast(parent, "warning", title, message, 
                duration !== undefined ? duration : Enums.duration.notification, 
                position !== undefined ? position : manager.posBottomRight,
                mode !== undefined ? mode : Enums.notification.mode_in_app)
        }
        function error(parent, title, message, duration, position, mode) {
            return manager._createToast(parent, "error", title, message, 
                duration !== undefined ? duration : Enums.duration.notification, 
                position !== undefined ? position : manager.posBottomRight,
                mode !== undefined ? mode : Enums.notification.mode_in_app)
        }
        function processing(parent, title, message, duration, position, mode) {
            return manager._createToast(parent, "processing", title, message, 
                duration !== undefined ? duration : Enums.duration.notification,
                position !== undefined ? position : manager.posBottomRight,
                mode !== undefined ? mode : Enums.notification.mode_in_app)
        }
        function progressBar(parent, title, message, position, mode) {
            return manager._createToastWithFeature(parent, "info", title, message, Enums.duration.notification,
                position !== undefined ? position : manager.posBottomRight,
                Enums.notification.feature_progress_bar,
                mode !== undefined ? mode : Enums.notification.mode_in_app)
        }
        function indeterminateBar(parent, title, message, position, mode) {
            return manager._createToastWithFeature(parent, "info", title, message, Enums.duration.notification,
                position !== undefined ? position : manager.posBottomRight,
                Enums.notification.feature_indeterminate_bar,
                mode !== undefined ? mode : Enums.notification.mode_in_app)
        }
        function progressRing(parent, title, message, position, mode) {
            return manager._createToastWithFeature(parent, "info", title, message, Enums.duration.notification,
                position !== undefined ? position : manager.posBottomRight,
                Enums.notification.feature_progress_ring,
                mode !== undefined ? mode : Enums.notification.mode_in_app)
        }
        function indeterminateRing(parent, title, message, position, mode) {
            return manager._createToastWithFeature(parent, "info", title, message, Enums.duration.notification,
                position !== undefined ? position : manager.posBottomRight,
                Enums.notification.feature_indeterminate_ring,
                mode !== undefined ? mode : Enums.notification.mode_in_app)
        }
        function randomPosition() { return manager._stackManager.randomPosition() }
    }
    
    // Desktop namespace 桌面通知命名空间
    readonly property QtObject desktop: QtObject {
        function info(title, message, duration, position, options) {
            return manager._createDesktop("info", title, message, 
                duration !== undefined ? duration : Enums.duration.notification, 
                position !== undefined ? position : manager.posBottomRight, 0, options)
        }
        function success(title, message, duration, position, options) {
            return manager._createDesktop("success", title, message, 
                duration !== undefined ? duration : Enums.duration.notification, 
                position !== undefined ? position : manager.posBottomRight, 0, options)
        }
        function warning(title, message, duration, position, options) {
            return manager._createDesktop("warning", title, message, 
                duration !== undefined ? duration : Enums.duration.notification, 
                position !== undefined ? position : manager.posBottomRight, 0, options)
        }
        function error(title, message, duration, position, options) {
            return manager._createDesktop("error", title, message, 
                duration !== undefined ? duration : Enums.duration.notification, 
                position !== undefined ? position : manager.posBottomRight, 0, options)
        }
        function infoBar(severity, title, message, duration, position, options) {
            return manager._createDesktop(severity, title, message, 
                duration !== undefined ? duration : Enums.duration.notification, 
                position !== undefined ? position : manager.posTopRight, 1, options)
        }
        function randomPosition() { return manager._stackManager.randomPosition() }
    }
    
    // ==================== Public Methods 公开方法 ====================
    function closeAllDesktopNotifications() {
        _stackManager.closeAllDesktopNotifications()
    }

    function closeAllWindowOutsideNotifications(hostWindow) {
        _stackManager.closeAllOutsideNotifications(hostWindow)
    }

    function orientationForMessage(message) {
        return message && (message.indexOf("\n") >= 0
            || message.length > Enums.notification.layout.longMessageThreshold)
            ? Qt.Vertical : Qt.Horizontal
    }
    
    // ==================== Internal Methods 内部方法 ====================
    function _getInfoBarComponent() {
        if (!_infoBarComponent) {
            _infoBarComponent = Qt.createComponent("../InfoBar/InfoBarEntry.qml")
        }
        return _infoBarComponent
    }

    function _getToastComponent() {
        if (!_toastComponent) {
            _toastComponent = Qt.createComponent("Toast.qml")
        }
        return _toastComponent
    }

    function _getDesktopComponent() {
        if (!_desktopComponent) {
            _desktopComponent = Qt.createComponent("DesktopOverlay.qml")
        }
        return _desktopComponent
    }

    function _getWindowOutsideComponent() {
        if (!_windowOutsideComponent) {
            _windowOutsideComponent = Qt.createComponent(
                "_internal/WindowOutsideOverlay.qml"
            )
        }
        return _windowOutsideComponent
    }

    function _getWindowParent(item) {
        if (item && item.Window && item.Window.window) {
            return item.Window.window.contentItem
        }
        return item
    }

    function _getHostWindow(item) {
        if (item && item.Window && item.Window.window) return item.Window.window
        if (item && item.contentItem) return item
        return null
    }

    function _usesWindowOutside(mode) {
        return mode === Enums.notification.mode_window_outside
    }

    function _desktopOverlayProperties(position, options) {
        var properties = { "position": position, "stackOffset": 0 }
        if (options && options.screen !== undefined && options.screen !== null) {
            properties.screen = options.screen
        }
        return properties
    }

    function _desktopNotificationProperties(severity, title, message, duration, position, mode, options) {
        var properties = {
            "severity": severity,
            "title": title,
            "message": message,
            "duration": duration,
            "position": position,
            "desktopMode": true
        }
        var names = [
            "orient", "customContent", "closable", "feature", "progress",
            "completeDuration", "backgroundColorLight", "backgroundColorDark"
        ]
        if (mode === 1) names.push("icon", "radius")
        for (var i = 0; options && i < names.length; i++) {
            var name = names[i]
            if (options[name] !== undefined) properties[name] = options[name]
        }
        if (!options || options.orient === undefined) {
            properties.orient = orientationForMessage(message)
        }
        return properties
    }
    
    function _createInfoBar(parent, severity, title, content, duration, position, mode) {
        return _createInfoBarWithFeature(
            parent, severity, title, content, duration, position,
            Enums.notification.feature_normal, mode
        )
    }
    
    function _createInfoBarWithFeature(parent, severity, title, content, duration, position, feature, mode) {
        if (_usesWindowOutside(mode)) {
            return _createWindowOutside(
                parent, severity, title, content, duration, position, feature, true
            )
        }
        var windowParent = _getWindowParent(parent)
        var component = _getInfoBarComponent()
        return _itemLifecycle.create(component, windowParent, {
            "severity": severity, "title": title, "message": content,
            "duration": duration, "position": position, "feature": feature
        }, position, Enums.spacing.m)
    }
    
    function _createToast(parent, severity, title, message, duration, position, mode) {
        return _createToastWithFeature(
            parent, severity, title, message, duration, position,
            Enums.notification.feature_normal, mode
        )
    }
    
    function _createToastWithFeature(parent, severity, title, message, duration, position, feature, mode) {
        if (_usesWindowOutside(mode)) {
            return _createWindowOutside(
                parent, severity, title, message, duration, position, feature, false
            )
        }
        var windowParent = _getWindowParent(parent)
        var component = _getToastComponent()
        return _itemLifecycle.create(component, windowParent, {
            "severity": severity, "title": title, "message": message,
            "duration": duration, "position": position, "feature": feature,
            // 长文本/多行自动用垂直布局(水平布局高度受限,长内容易裁切)
            "orient": orientationForMessage(message)
        }, position)
    }

    function _createWindowOutside(parent, severity, title, message, duration, position, feature, infoBarMode) {
        if (!Enums.notification.isWindowOutsidePosition(position)) {
            console.warn("NotificationManager: Window-outside mode requires an edge position:", position)
            return null
        }
        var hostWindow = _getHostWindow(parent)
        if (!hostWindow) {
            console.warn("NotificationManager: Window-outside mode requires a window parent")
            return null
        }
        var overlayComponent = _getWindowOutsideComponent()
        var component = infoBarMode ? _getInfoBarComponent() : _getToastComponent()
        var properties = {
            "severity": severity,
            "title": title,
            "message": message,
            "duration": duration,
            "position": position,
            "feature": feature,
            "desktopMode": true
        }
        if (!infoBarMode) properties.orient = orientationForMessage(message)
        return _overlayLifecycle.create(
            overlayComponent, component, {
                "hostWindow": hostWindow,
                "position": position,
                "stackOffset": 0
            }, properties, position, "outside"
        )
    }
    
    function _createDesktop(severity, title, message, duration, position, mode, options) {
        var overlayComponent = _getDesktopComponent()
        var properties = _desktopNotificationProperties(
            severity, title, message, duration, position, mode, options
        )
        var notification
        if (mode === 1) {
            var infoBarComp = _getInfoBarComponent()
            notification = _overlayLifecycle.create(
                overlayComponent, infoBarComp,
                _desktopOverlayProperties(position, options), properties,
                position, "desktop"
            )
        } else {
            var toastComp = _getToastComponent()
            notification = _overlayLifecycle.create(
                overlayComponent, toastComp,
                _desktopOverlayProperties(position, options), properties,
                position, "desktop"
            )
        }
        return notification
    }
}
