// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import PrismQML

// FeedbackProgressShowcase - Unified progress notification gallery 统一进度通知画廊
Column {
    id: root

    required property Item notificationParent

    function _animateProgress(notification, step, interval) {
        var progress = 0
        var timer = Qt.createQmlObject(
            "import QtQuick; Timer { repeat: true }",
            notification
        )
        timer.interval = interval
        timer.triggered.connect(function() {
            progress += step
            notification.progress = progress
            if (progress >= 1) timer.destroy()
        })
        timer.start()
    }

    width: parent ? parent.width : implicitWidth
    spacing: Enums.spacing.xxl

    // InfoBar progress modes InfoBar 进度模式
    ExampleCard {
        title: "InfoBar 进度模式"
        description: "InfoBar 的四种进度 feature"

        Column {
            spacing: Enums.spacing.l

            // Static showcase 静态展示
            Row {
                spacing: Enums.spacing.m

                ComponentCard {
                    label: "进度条 60%"

                    InfoBar {
                        objectName: "galleryProgressInfoBarProgressBar"
                        title: "下载中"
                        message: "60%"
                        feature: Enums.notification.feature_progress_bar
                        progress: 0.6
                        width: Enums.demoMetrics.feedbackNotificationWidth
                        duration: Enums.duration.persistent
                    }
                }

                ComponentCard {
                    label: "不确定进度条"

                    InfoBar {
                        objectName: "galleryProgressInfoBarIndeterminateBar"
                        title: "加载中"
                        message: "请稍候..."
                        feature: Enums.notification.feature_indeterminate_bar
                        width: Enums.demoMetrics.feedbackNotificationWidth
                        duration: Enums.duration.persistent
                    }
                }
            }

            Row {
                spacing: Enums.spacing.m

                ComponentCard {
                    label: "进度环 40%"

                    InfoBar {
                        objectName: "galleryProgressInfoBarProgressRing"
                        title: "上传中"
                        message: "40%"
                        feature: Enums.notification.feature_progress_ring
                        progress: 0.4
                        width: Enums.demoMetrics.feedbackNotificationWidth
                        duration: Enums.duration.persistent
                    }
                }

                ComponentCard {
                    label: "不确定进度环"

                    InfoBar {
                        objectName: "galleryProgressInfoBarIndeterminateRing"
                        title: "处理中"
                        message: "请稍候..."
                        feature: Enums.notification.feature_indeterminate_ring
                        width: Enums.demoMetrics.feedbackNotificationWidth
                        duration: Enums.duration.persistent
                    }
                }
            }

            // Popup showcase 弹出演示
            Row {
                spacing: Enums.spacing.l

                Button {
                    text: "进度条"
                    style: Enums.button.style_primary
                    onClicked: {
                        var bar = NotificationManager.infoBar.progressBar(
                            root.notificationParent,
                            "下载中",
                            "正在下载文件..."
                        )
                        root._animateProgress(
                            bar,
                            Enums.demoMetrics.feedbackProgressBarStep,
                            Enums.duration.fast
                        )
                    }
                }

                Button {
                    text: "不确定进度条"
                    onClicked: NotificationManager.infoBar.indeterminateBar(
                        root.notificationParent,
                        "加载中",
                        "正在处理..."
                    )
                }

                Button {
                    text: "进度环"
                    onClicked: {
                        var ring = NotificationManager.infoBar.progressRing(
                            root.notificationParent,
                            "上传中",
                            "正在上传..."
                        )
                        root._animateProgress(
                            ring,
                            Enums.demoMetrics.feedbackProgressRingStep,
                            Enums.demoMetrics.feedbackProgressRingInterval
                        )
                    }
                }

                Button {
                    text: "不确定进度环"
                    onClicked: NotificationManager.infoBar.indeterminateRing(
                        root.notificationParent,
                        "同步中",
                        "正在同步数据..."
                    )
                }
            }
        }
    }

    // Toast progress modes Toast 进度模式
    ExampleCard {
        title: "Toast 进度模式"
        description: "Toast 的四种进度 feature"

        Column {
            spacing: Enums.spacing.l

            // Static showcase 静态展示
            Row {
                spacing: Enums.spacing.m

                ComponentCard {
                    label: "进度条 60%"

                    Toast {
                        objectName: "galleryProgressToastProgressBar"
                        title: "下载中"
                        message: "60%"
                        feature: Enums.notification.feature_progress_bar
                        progress: 0.6
                        width: Enums.demoMetrics.feedbackNotificationWidth
                        duration: Enums.duration.persistent
                        visible: true
                    }
                }

                ComponentCard {
                    label: "不确定进度条"

                    Toast {
                        objectName: "galleryProgressToastIndeterminateBar"
                        title: "加载中"
                        message: "请稍候..."
                        feature: Enums.notification.feature_indeterminate_bar
                        width: Enums.demoMetrics.feedbackNotificationWidth
                        duration: Enums.duration.persistent
                        visible: true
                    }
                }
            }

            Row {
                spacing: Enums.spacing.m

                ComponentCard {
                    label: "进度环 40%"

                    Toast {
                        objectName: "galleryProgressToastProgressRing"
                        title: "上传中"
                        message: "40%"
                        feature: Enums.notification.feature_progress_ring
                        progress: 0.4
                        width: Enums.demoMetrics.feedbackNotificationWidth
                        duration: Enums.duration.persistent
                        visible: true
                    }
                }

                ComponentCard {
                    label: "不确定进度环"

                    Toast {
                        objectName: "galleryProgressToastIndeterminateRing"
                        title: "处理中"
                        message: "请稍候..."
                        feature: Enums.notification.feature_indeterminate_ring
                        width: Enums.demoMetrics.feedbackNotificationWidth
                        duration: Enums.duration.persistent
                        visible: true
                    }
                }
            }

            // Popup showcase 弹出演示
            Row {
                spacing: Enums.spacing.l

                Button {
                    text: "进度条"
                    style: Enums.button.style_primary
                    onClicked: {
                        var bar = NotificationManager.toast.progressBar(
                            root.notificationParent,
                            "下载中",
                            "正在下载..."
                        )
                        root._animateProgress(
                            bar,
                            Enums.demoMetrics.feedbackProgressBarStep,
                            Enums.duration.fast
                        )
                    }
                }

                Button {
                    text: "不确定进度条"
                    onClicked: NotificationManager.toast.indeterminateBar(
                        root.notificationParent,
                        "处理中",
                        "请稍候..."
                    )
                }

                Button {
                    text: "进度环"
                    onClicked: {
                        var ring = NotificationManager.toast.progressRing(
                            root.notificationParent,
                            "上传中",
                            "正在上传..."
                        )
                        root._animateProgress(
                            ring,
                            Enums.demoMetrics.feedbackProgressRingStep,
                            Enums.demoMetrics.feedbackProgressRingInterval
                        )
                    }
                }

                Button {
                    text: "不确定进度环"
                    onClicked: NotificationManager.toast.indeterminateRing(
                        root.notificationParent,
                        "同步中",
                        "正在同步..."
                    )
                }
            }
        }
    }
}
