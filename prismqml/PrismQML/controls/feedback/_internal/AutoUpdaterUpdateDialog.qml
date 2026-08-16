// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../"
import "../../dialogs"

// AutoUpdaterUpdateDialog - AutoUpdater confirmation dialog wiring 自动更新确认弹窗编排
// Keeps the facade focused on update state while preserving its dynamic dialog contract.
// 将弹窗回调留在动态组件所有者内，同时保持门面只负责更新状态编排。
UpdateDialog {
    id: dialog

    // ==================== Required Props 必需属性 ====================
    required property var updaterControl

    // ==================== Public Props 公开属性 ====================
    confirmText: {
        Translator._v
        return Translator.tr("download_and_install")
    }
    cancelText: {
        Translator._v
        return Translator.tr("later")
    }

    // ==================== Signals 信号 ====================
    onConfirmed: {
        updaterControl._awaitingDecision = false
        updaterControl.downloadRequested(
            updaterControl._pendingVersion,
            updaterControl._pendingUrl,
            updaterControl._pendingHtmlUrl
        )
        if (updaterControl.autoDownload)
            updaterControl._beginDownload(
                updaterControl._pendingVersion,
                updaterControl._pendingUrl,
                updaterControl._pendingHtmlUrl
            )
    }
    onCancelled: {
        // 用户稍后再说,清空待处理状态
        updaterControl._awaitingDecision = false
        updaterControl._clearPending()
    }
}
