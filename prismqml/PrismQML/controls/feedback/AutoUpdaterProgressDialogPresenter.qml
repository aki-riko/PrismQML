// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import PrismQML

// AutoUpdaterProgressDialogPresenter - Modal AutoUpdater feedback presenter 模态自动更新反馈展示器
// Maps the shared feedback model to ProgressDialog. 将共享反馈模型映射到 ProgressDialog。
Item {
    id: root

    // ==================== Public Props 公开属性 ====================
    property var feedbackModel: null
    property Item presenterHost: null
    property real progressMaximum: 100

    // ==================== Internal Methods 内部方法 ====================
    function _dialogProgress() {
        var model = root.feedbackModel;
        if (!model || model.indeterminate)
            return -1;
        if (model.determinate)
            return Math.max(0, Math.min(root.progressMaximum,
                model.progress * root.progressMaximum));
        return model.severity === "success" ? root.progressMaximum : 0;
    }

    function _syncActive() {
        if (root.feedbackModel && root.feedbackModel.active)
            progressDialog.open();
        else
            progressDialog.close();
    }

    objectName: "autoUpdaterProgressDialogPresenter"
    visible: false

    onFeedbackModelChanged: root._syncActive()

    Component.onCompleted: root._syncActive()
    Component.onDestruction: progressDialog.close()

    // ==================== Content 内容 ====================
    property alias progressDialog: progressDialog
    ProgressDialog {
        id: progressDialog
        objectName: "autoUpdaterProgressDialog"
        title: root.feedbackModel ? root.feedbackModel.title : ""
        content: root.feedbackModel ? root.feedbackModel.message : ""
        progressIcon: root.feedbackModel ? root.feedbackModel.icon : ""
        progress: root._dialogProgress()
    }

    Connections {
        function onActiveChanged() { root._syncActive(); }

        target: root.feedbackModel
        ignoreUnknownSignals: true
    }
}
