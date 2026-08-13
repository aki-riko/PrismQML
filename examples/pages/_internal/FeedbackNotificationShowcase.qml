// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import PrismQML
import PrismQML as Fluent

// FeedbackNotificationShowcase - Static notification severity gallery 静态通知级别画廊
Column {
    id: root

    width: parent ? parent.width : implicitWidth
    spacing: Enums.spacing.xxl

    // InfoBar severity showcase InfoBar 级别展示
    ExampleCard {
        title: Fluent.Translator.tr("gallery_d1aaeb94e509fcb0", Fluent.Translator._v)
        description: "InfoBar"

        Column {
            spacing: Enums.spacing.m

            ComponentCard { label: "severity: info"; InfoBar { objectName: "galleryInfoBarInfo"; title: "Info"; content: Fluent.Translator.tr("gallery_7c8eb931dcf272aa", Fluent.Translator._v); severity: "info"; width: Enums.demoMetrics.feedbackNotificationWidth; duration: Enums.duration.persistent } }
            ComponentCard { label: "severity: success"; InfoBar { objectName: "galleryInfoBarSuccess"; title: "Success"; content: Fluent.Translator.tr("gallery_38de25e522956722", Fluent.Translator._v); severity: "success"; width: Enums.demoMetrics.feedbackNotificationWidth; duration: Enums.duration.persistent } }
            ComponentCard { label: "severity: warning"; InfoBar { objectName: "galleryInfoBarWarning"; title: "Warning"; content: Fluent.Translator.tr("gallery_6e06872053c92014", Fluent.Translator._v); severity: "warning"; width: Enums.demoMetrics.feedbackNotificationWidth; duration: Enums.duration.persistent } }
            ComponentCard { label: "severity: error"; InfoBar { objectName: "galleryInfoBarError"; title: "Error"; content: Fluent.Translator.tr("gallery_0cb3fb5b86d7dec6", Fluent.Translator._v); severity: "error"; width: Enums.demoMetrics.feedbackNotificationWidth; duration: Enums.duration.persistent } }
            ComponentCard { label: "severity: processing"; InfoBar { objectName: "galleryInfoBarProcessing"; title: "Processing"; content: Fluent.Translator.tr("gallery_c1fd812f81cab441", Fluent.Translator._v); severity: "processing"; width: Enums.demoMetrics.feedbackNotificationWidth; duration: Enums.duration.persistent } }
        }
    }

    // Toast severity showcase Toast 级别展示
    ExampleCard {
        title: "Toast"
        description: "Toast"

        Column {
            spacing: Enums.spacing.m

            ComponentCard { label: "severity: info"; Toast { objectName: "galleryToastInfo"; title: "Info"; message: Fluent.Translator.tr("gallery_7c8eb931dcf272aa", Fluent.Translator._v); severity: "info"; width: Enums.demoMetrics.feedbackNotificationWidth; duration: Enums.duration.persistent; visible: true } }
            ComponentCard { label: "severity: success"; Toast { objectName: "galleryToastSuccess"; title: "Success"; message: Fluent.Translator.tr("gallery_38de25e522956722", Fluent.Translator._v); severity: "success"; width: Enums.demoMetrics.feedbackNotificationWidth; duration: Enums.duration.persistent; visible: true } }
            ComponentCard { label: "severity: warning"; Toast { objectName: "galleryToastWarning"; title: "Warning"; message: Fluent.Translator.tr("gallery_6e06872053c92014", Fluent.Translator._v); severity: "warning"; width: Enums.demoMetrics.feedbackNotificationWidth; duration: Enums.duration.persistent; visible: true } }
            ComponentCard { label: "severity: error"; Toast { objectName: "galleryToastError"; title: "Error"; message: Fluent.Translator.tr("gallery_0cb3fb5b86d7dec6", Fluent.Translator._v); severity: "error"; width: Enums.demoMetrics.feedbackNotificationWidth; duration: Enums.duration.persistent; visible: true } }
            ComponentCard { label: "severity: processing"; Toast { objectName: "galleryToastProcessing"; title: "Processing"; message: Fluent.Translator.tr("gallery_c1fd812f81cab441", Fluent.Translator._v); severity: "processing"; width: Enums.demoMetrics.feedbackNotificationWidth; duration: Enums.duration.persistent; visible: true } }
        }
    }
}
