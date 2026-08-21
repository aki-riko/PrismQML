// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import PrismQML
import "_internal" as FeedbackInternal

// AutoUpdaterToastPresenter - Default AutoUpdater feedback presenter 默认自动更新反馈展示器
// Maps the shared feedback model to an in-window Toast. 将共享反馈模型映射到窗口内 Toast。
Item {
    id: root

    // ==================== Public Props 公开属性 ====================
    property var feedbackModel: null
    property Item presenterHost: null
    property int position: Enums.notification.posBottomRight

    // ==================== Internal Props 内部属性 ====================
    property var _toast: null

    // ==================== Internal Methods 内部方法 ====================
    function _scheduleSync() {
        syncTimer.restart();
    }

    function _onToastClosed() {
        var item = root._toast;
        if (!item)
            return;
        item.closed.disconnect(root._onToastClosed);
        root._toast = null;
        if (root.feedbackModel && root.feedbackModel.active)
            root.feedbackModel.dismiss();
    }

    function _sync() {
        var model = root.feedbackModel;
        if (!model || !model.active) {
            _hideToast();
            return;
        }

        var item = root._toast;
        if (!item) {
            item = NotificationManager.toast.info(
                root.presenterHost || root,
                model.title,
                model.message,
                model.duration,
                root.position
            );
            if (!item) {
                console.warn("AutoUpdaterToastPresenter: Toast 创建失败");
                return;
            }
            item.objectName = "autoUpdaterToast";
            root._toast = item;
            item.closed.connect(root._onToastClosed);
        }

        item.orient = NotificationManager.orientationForMessage(model.message);
        item.title = model.title;
        item.message = model.message;
        item.severity = model.severity;
        item.feature = model.feature;
        item.duration = model.duration;
        item.progress = model.progress;
        item.progressIcon = model.icon;
    }

    function _hideToast() {
        var item = root._toast;
        root._toast = null;
        if (item) {
            item.closed.disconnect(root._onToastClosed);
            item.hide();
        }
    }

    objectName: "autoUpdaterToastPresenter"
    visible: false

    onFeedbackModelChanged: {
        syncTimer.stop();
        root._sync();
    }

    Component.onCompleted: root._scheduleSync()
    Component.onDestruction: root._hideToast()

    // ==================== Content 内容 ====================
    FeedbackInternal.AutoUpdaterToastSyncTimer {
        id: syncTimer

        host: root
    }

    Connections {
        function onActiveChanged() {
            syncTimer.stop();
            root._sync();
        }
        function onTitleChanged() { root._scheduleSync(); }
        function onMessageChanged() { root._scheduleSync(); }
        function onIconChanged() { root._scheduleSync(); }
        function onSeverityChanged() { root._scheduleSync(); }
        function onFeatureChanged() { root._scheduleSync(); }
        function onDurationChanged() { root._scheduleSync(); }
        function onProgressChanged() { root._scheduleSync(); }

        target: root.feedbackModel
        ignoreUnknownSignals: true
    }
}
