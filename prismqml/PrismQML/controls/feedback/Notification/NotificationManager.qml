// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

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
    
    // ==================== Stack Manager 堆叠管理器 ====================
    property NotificationStackManager _stackManager: NotificationStackManager {}
    
    // ==================== Position Enum (delegate) 位置枚举 ====================
    readonly property int posTopLeft: _stackManager.posTopLeft
    readonly property int posTop: _stackManager.posTop
    readonly property int posTopRight: _stackManager.posTopRight
    readonly property int posBottomLeft: _stackManager.posBottomLeft
    readonly property int posBottom: _stackManager.posBottom
    readonly property int posBottomRight: _stackManager.posBottomRight
    
    // ==================== Components (lazy load) 组件（懒加载） ====================
    property var _infoBarComponent: null
    property var _toastComponent: null
    property var _desktopComponent: null
    
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
    
    // ==================== InfoBar Namespace InfoBar命名空间 ====================
    readonly property QtObject infoBar: QtObject {
        function info(parent, title, content, duration, position) {
            return manager._createInfoBar(parent, "info", title, content, 
                duration !== undefined ? duration : Enums.duration.notification, 
                position !== undefined ? position : manager.posTopRight)
        }
        function attention(parent, title, content, duration, position) {
            return manager._createInfoBar(parent, "attention", title, content, 
                duration !== undefined ? duration : Enums.duration.notification, 
                position !== undefined ? position : manager.posTopRight)
        }
        function success(parent, title, content, duration, position) {
            return manager._createInfoBar(parent, "success", title, content, 
                duration !== undefined ? duration : Enums.duration.notification, 
                position !== undefined ? position : manager.posTopRight)
        }
        function warning(parent, title, content, duration, position) {
            return manager._createInfoBar(parent, "warning", title, content, 
                duration !== undefined ? duration : Enums.duration.notification, 
                position !== undefined ? position : manager.posTopRight)
        }
        function error(parent, title, content, duration, position) {
            return manager._createInfoBar(parent, "error", title, content, 
                duration !== undefined ? duration : Enums.duration.notification, 
                position !== undefined ? position : manager.posTopRight)
        }
        function processing(parent, title, content, duration, position) {
            return manager._createInfoBar(parent, "processing", title, content, 
                duration !== undefined ? duration : Enums.duration.notification,
                position !== undefined ? position : manager.posTopRight)
        }
        function progressBar(parent, title, content, position) {
            return manager._createInfoBarWithFeature(parent, "info", title, content, Enums.duration.notification,
                position !== undefined ? position : manager.posTopRight,
                Enums.notification.feature_progress_bar)
        }
        function indeterminateBar(parent, title, content, position) {
            return manager._createInfoBarWithFeature(parent, "info", title, content, Enums.duration.notification,
                position !== undefined ? position : manager.posTopRight,
                Enums.notification.feature_indeterminate_bar)
        }
        function progressRing(parent, title, content, position) {
            return manager._createInfoBarWithFeature(parent, "info", title, content, Enums.duration.notification,
                position !== undefined ? position : manager.posTopRight,
                Enums.notification.feature_progress_ring)
        }
        function indeterminateRing(parent, title, content, position) {
            return manager._createInfoBarWithFeature(parent, "info", title, content, Enums.duration.notification,
                position !== undefined ? position : manager.posTopRight,
                Enums.notification.feature_indeterminate_ring)
        }
        function randomPosition() { return manager._stackManager.randomPosition() }
    }
    
    // ==================== Toast Namespace Toast命名空间 ====================
    readonly property QtObject toast: QtObject {
        function info(parent, title, message, duration, position) {
            return manager._createToast(parent, "info", title, message, 
                duration !== undefined ? duration : Enums.duration.notification, 
                position !== undefined ? position : manager.posBottomRight)
        }
        function attention(parent, title, message, duration, position) {
            return manager._createToast(parent, "attention", title, message, 
                duration !== undefined ? duration : Enums.duration.notification, 
                position !== undefined ? position : manager.posBottomRight)
        }
        function success(parent, title, message, duration, position) {
            return manager._createToast(parent, "success", title, message, 
                duration !== undefined ? duration : Enums.duration.notification, 
                position !== undefined ? position : manager.posBottomRight)
        }
        function warning(parent, title, message, duration, position) {
            return manager._createToast(parent, "warning", title, message, 
                duration !== undefined ? duration : Enums.duration.notification, 
                position !== undefined ? position : manager.posBottomRight)
        }
        function error(parent, title, message, duration, position) {
            return manager._createToast(parent, "error", title, message, 
                duration !== undefined ? duration : Enums.duration.notification, 
                position !== undefined ? position : manager.posBottomRight)
        }
        function processing(parent, title, message, duration, position) {
            return manager._createToast(parent, "processing", title, message, 
                duration !== undefined ? duration : Enums.duration.notification,
                position !== undefined ? position : manager.posBottomRight)
        }
        function progressBar(parent, title, message, position) {
            return manager._createToastWithFeature(parent, "info", title, message, Enums.duration.notification,
                position !== undefined ? position : manager.posBottomRight,
                Enums.notification.feature_progress_bar)
        }
        function indeterminateBar(parent, title, message, position) {
            return manager._createToastWithFeature(parent, "info", title, message, Enums.duration.notification,
                position !== undefined ? position : manager.posBottomRight,
                Enums.notification.feature_indeterminate_bar)
        }
        function progressRing(parent, title, message, position) {
            return manager._createToastWithFeature(parent, "info", title, message, Enums.duration.notification,
                position !== undefined ? position : manager.posBottomRight,
                Enums.notification.feature_progress_ring)
        }
        function indeterminateRing(parent, title, message, position) {
            return manager._createToastWithFeature(parent, "info", title, message, Enums.duration.notification,
                position !== undefined ? position : manager.posBottomRight,
                Enums.notification.feature_indeterminate_ring)
        }
        function randomPosition() { return manager._stackManager.randomPosition() }
    }
    
    // ==================== Desktop Namespace 桌面通知命名空间 ====================
    readonly property QtObject desktop: QtObject {
        function info(title, message, duration, position) {
            return manager._createDesktop("info", title, message, 
                duration !== undefined ? duration : Enums.duration.notification, 
                position !== undefined ? position : manager.posBottomRight, 0)
        }
        function success(title, message, duration, position) {
            return manager._createDesktop("success", title, message, 
                duration !== undefined ? duration : Enums.duration.notification, 
                position !== undefined ? position : manager.posBottomRight, 0)
        }
        function warning(title, message, duration, position) {
            return manager._createDesktop("warning", title, message, 
                duration !== undefined ? duration : Enums.duration.notification, 
                position !== undefined ? position : manager.posBottomRight, 0)
        }
        function error(title, message, duration, position) {
            return manager._createDesktop("error", title, message, 
                duration !== undefined ? duration : Enums.duration.notification, 
                position !== undefined ? position : manager.posBottomRight, 0)
        }
        function infoBar(severity, title, message, duration, position) {
            return manager._createDesktop(severity, title, message, 
                duration !== undefined ? duration : Enums.duration.notification, 
                position !== undefined ? position : manager.posTopRight, 1)
        }
        function randomPosition() { return manager._stackManager.randomPosition() }
    }
    
    // ==================== Public Methods 公开方法 ====================
    function closeAllDesktopNotifications() {
        _stackManager.closeAllDesktopNotifications()
    }
    
    // ==================== Internal Methods 内部方法 ====================
    function _getWindowParent(item) {
        if (item && item.Window && item.Window.window) {
            return item.Window.window.contentItem
        }
        return item
    }
    
    function _createInfoBar(parent, severity, title, content, duration, position) {
        return _createInfoBarWithFeature(parent, severity, title, content, duration, position, Enums.notification.feature_normal)
    }
    
    function _createInfoBarWithFeature(parent, severity, title, content, duration, position, feature) {
        var windowParent = _getWindowParent(parent)
        var component = _getInfoBarComponent()
        if (component.status !== Component.Ready) {
            console.error("NotificationManager: InfoBar component not ready:", component.errorString())
            return null
        }
        var item = component.createObject(windowParent, {
            "severity": severity, "title": title, "message": content,
            "duration": duration, "position": position, "feature": feature
        })
        if (item) {
            item.z = Enums.zIndex.overlay
            _stackManager.addToStack(item, position)
            _stackManager.setPosition(item, windowParent, position, Enums.spacing.m)
            item.closed.connect(function() {
                _stackManager.removeFromStack(item, position)
                item.destroy()
            })
            item.show()
        }
        return item
    }
    
    function _createToast(parent, severity, title, message, duration, position) {
        return _createToastWithFeature(parent, severity, title, message, duration, position, Enums.notification.feature_normal)
    }
    
    function _createToastWithFeature(parent, severity, title, message, duration, position, feature) {
        var windowParent = _getWindowParent(parent)
        var component = _getToastComponent()
        if (component.status !== Component.Ready) {
            console.error("NotificationManager: Toast component not ready:", component.errorString())
            return null
        }
        var item = component.createObject(windowParent, {
            "severity": severity, "title": title, "message": message,
            "duration": duration, "position": position, "feature": feature,
            // 长文本/多行自动用垂直布局(水平布局高度受限,长内容易裁切)
            "orient": (message && (message.indexOf("\n") >= 0 || message.length > 60)) ? Qt.Vertical : Qt.Horizontal
        })
        if (item) {
            item.z = Enums.zIndex.overlay
            _stackManager.addToStack(item, position)
            _stackManager.setPosition(item, windowParent, position)
            item.closed.connect(function() {
                _stackManager.removeFromStack(item, position)
                item.destroy()
            })
            item.show()
        }
        return item
    }
    
    function _createDesktop(severity, title, message, duration, position, mode) {
        var overlayComponent = _getDesktopComponent()
        if (overlayComponent.status !== Component.Ready) {
            console.error("NotificationManager: DesktopOverlay component not ready:", overlayComponent.errorString())
            return null
        }
        var stackOffset = _stackManager.getDesktopStackOffset(position)
        var overlay = overlayComponent.createObject(null, { 
            "position": position, "stackOffset": stackOffset
        })
        if (!overlay) return null
        
        _stackManager.addToDesktopStack(overlay, position)
        
        var notification
        if (mode === 1) {
            var infoBarComp = _getInfoBarComponent()
            if (infoBarComp.status !== Component.Ready) { overlay.destroy(); return null }
            notification = infoBarComp.createObject(overlay.content, {
                "severity": severity, "title": title, "message": message,
                "duration": duration, "position": position, "desktopMode": true
            })
        } else {
            var toastComp = _getToastComponent()
            if (toastComp.status !== Component.Ready) { overlay.destroy(); return null }
            notification = toastComp.createObject(overlay.content, {
                "severity": severity, "title": title, "message": message,
                "duration": duration, "position": position, "desktopMode": true
            })
        }
        
        if (!notification) { overlay.destroy(); return null }
        
        overlay.notificationItem = notification
        notification.anchors.centerIn = overlay.content
        
        notification.closed.connect(function() { overlay.hide() })
        overlay.closed.connect(function() {
            manager._stackManager.removeFromDesktopStack(overlay, position)
            notification.destroy()
            overlay.destroy()
        })
        
        notification.visible = true
        overlay.show()
        
        return notification
    }
}
