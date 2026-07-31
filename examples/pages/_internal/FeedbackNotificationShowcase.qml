// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import PrismQML

// FeedbackNotificationShowcase - Static notification severity gallery 静态通知级别画廊
Column {
    id: root

    width: parent ? parent.width : implicitWidth
    spacing: Enums.spacing.xxl

    // InfoBar severity showcase InfoBar 级别展示
    ExampleCard {
        title: "信息条"
        description: "InfoBar"

        Column {
            spacing: Enums.spacing.m

            ComponentCard { label: "severity: info"; InfoBar { objectName: "galleryInfoBarInfo"; title: "Info"; content: "信息提示"; severity: "info"; width: Enums.demoMetrics.feedbackNotificationWidth; duration: Enums.duration.persistent } }
            ComponentCard { label: "severity: success"; InfoBar { objectName: "galleryInfoBarSuccess"; title: "Success"; content: "操作成功"; severity: "success"; width: Enums.demoMetrics.feedbackNotificationWidth; duration: Enums.duration.persistent } }
            ComponentCard { label: "severity: warning"; InfoBar { objectName: "galleryInfoBarWarning"; title: "Warning"; content: "请注意"; severity: "warning"; width: Enums.demoMetrics.feedbackNotificationWidth; duration: Enums.duration.persistent } }
            ComponentCard { label: "severity: error"; InfoBar { objectName: "galleryInfoBarError"; title: "Error"; content: "发生错误"; severity: "error"; width: Enums.demoMetrics.feedbackNotificationWidth; duration: Enums.duration.persistent } }
            ComponentCard { label: "severity: processing"; InfoBar { objectName: "galleryInfoBarProcessing"; title: "Processing"; content: "处理中..."; severity: "processing"; width: Enums.demoMetrics.feedbackNotificationWidth; duration: Enums.duration.persistent } }
        }
    }

    // Toast severity showcase Toast 级别展示
    ExampleCard {
        title: "Toast"
        description: "Toast"

        Column {
            spacing: Enums.spacing.m

            ComponentCard { label: "severity: info"; Toast { objectName: "galleryToastInfo"; title: "Info"; message: "信息提示"; severity: "info"; width: Enums.demoMetrics.feedbackNotificationWidth; duration: Enums.duration.persistent; visible: true } }
            ComponentCard { label: "severity: success"; Toast { objectName: "galleryToastSuccess"; title: "Success"; message: "操作成功"; severity: "success"; width: Enums.demoMetrics.feedbackNotificationWidth; duration: Enums.duration.persistent; visible: true } }
            ComponentCard { label: "severity: warning"; Toast { objectName: "galleryToastWarning"; title: "Warning"; message: "请注意"; severity: "warning"; width: Enums.demoMetrics.feedbackNotificationWidth; duration: Enums.duration.persistent; visible: true } }
            ComponentCard { label: "severity: error"; Toast { objectName: "galleryToastError"; title: "Error"; message: "发生错误"; severity: "error"; width: Enums.demoMetrics.feedbackNotificationWidth; duration: Enums.duration.persistent; visible: true } }
            ComponentCard { label: "severity: processing"; Toast { objectName: "galleryToastProcessing"; title: "Processing"; message: "处理中..."; severity: "processing"; width: Enums.demoMetrics.feedbackNotificationWidth; duration: Enums.duration.persistent; visible: true } }
        }
    }
}
