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
        title: Fluent.Translator.tr("gallery_7a466042afd5186a", Fluent.Translator._v)
        description: Fluent.Translator.tr("gallery_900db63e40422949", Fluent.Translator._v)

        Column {
            spacing: Enums.spacing.l

            // Static showcase 静态展示
            Row {
                spacing: Enums.spacing.m

                ComponentCard {
                    label: Fluent.Translator.tr("gallery_27ce4e7bae1a94fa", Fluent.Translator._v)

                    InfoBar {
                        objectName: "galleryProgressInfoBarProgressBar"
                        title: Fluent.Translator.tr("gallery_e2fc571a4cf00ceb", Fluent.Translator._v)
                        message: "60%"
                        feature: Enums.notification.feature_progress_bar
                        progress: 0.6
                        width: Enums.demoMetrics.feedbackNotificationWidth
                        duration: Enums.duration.persistent
                    }
                }

                ComponentCard {
                    label: Fluent.Translator.tr("gallery_494a635922be0b85", Fluent.Translator._v)

                    InfoBar {
                        objectName: "galleryProgressInfoBarIndeterminateBar"
                        title: Fluent.Translator.tr("gallery_d04fcbda737fc0c6", Fluent.Translator._v)
                        message: Fluent.Translator.tr("gallery_6a651b85a4259148", Fluent.Translator._v)
                        feature: Enums.notification.feature_indeterminate_bar
                        width: Enums.demoMetrics.feedbackNotificationWidth
                        duration: Enums.duration.persistent
                    }
                }
            }

            Row {
                spacing: Enums.spacing.m

                ComponentCard {
                    label: Fluent.Translator.tr("gallery_407b3ced57ef87c2", Fluent.Translator._v)

                    InfoBar {
                        objectName: "galleryProgressInfoBarProgressRing"
                        title: Fluent.Translator.tr("gallery_403b055e56f59395", Fluent.Translator._v)
                        message: "40%"
                        feature: Enums.notification.feature_progress_ring
                        progress: 0.4
                        width: Enums.demoMetrics.feedbackNotificationWidth
                        duration: Enums.duration.persistent
                    }
                }

                ComponentCard {
                    label: Fluent.Translator.tr("gallery_c26a5889102dc0c3", Fluent.Translator._v)

                    InfoBar {
                        objectName: "galleryProgressInfoBarIndeterminateRing"
                        title: Fluent.Translator.tr("gallery_694b71bc8013ff43", Fluent.Translator._v)
                        message: Fluent.Translator.tr("gallery_6a651b85a4259148", Fluent.Translator._v)
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
                    text: Fluent.Translator.tr("gallery_cd2e8707a7db3b3f", Fluent.Translator._v)
                    style: Enums.button.style_primary
                    onClicked: {
                        var bar = NotificationManager.infoBar.progressBar(
                            root.notificationParent,
                            Fluent.Translator.tr("gallery_e2fc571a4cf00ceb", Fluent.Translator._v),
                            Fluent.Translator.tr("gallery_e3742345058701ab", Fluent.Translator._v)
                        )
                        root._animateProgress(
                            bar,
                            Enums.demoMetrics.feedbackProgressBarStep,
                            Enums.duration.fast
                        )
                    }
                }

                Button {
                    text: Fluent.Translator.tr("gallery_494a635922be0b85", Fluent.Translator._v)
                    onClicked: NotificationManager.infoBar.indeterminateBar(
                        root.notificationParent,
                        Fluent.Translator.tr("gallery_d04fcbda737fc0c6", Fluent.Translator._v),
                        Fluent.Translator.tr("gallery_2ca049d69ce16975", Fluent.Translator._v)
                    )
                }

                Button {
                    text: Fluent.Translator.tr("gallery_029926f219a66e79", Fluent.Translator._v)
                    onClicked: {
                        var ring = NotificationManager.infoBar.progressRing(
                            root.notificationParent,
                            Fluent.Translator.tr("gallery_403b055e56f59395", Fluent.Translator._v),
                            Fluent.Translator.tr("gallery_4342d63e83c75f86", Fluent.Translator._v)
                        )
                        root._animateProgress(
                            ring,
                            Enums.demoMetrics.feedbackProgressRingStep,
                            Enums.demoMetrics.feedbackProgressRingInterval
                        )
                    }
                }

                Button {
                    text: Fluent.Translator.tr("gallery_c26a5889102dc0c3", Fluent.Translator._v)
                    onClicked: NotificationManager.infoBar.indeterminateRing(
                        root.notificationParent,
                        Fluent.Translator.tr("gallery_bb429d0227b7d9d6", Fluent.Translator._v),
                        Fluent.Translator.tr("gallery_49c69133a643bad3", Fluent.Translator._v)
                    )
                }
            }
        }
    }

    // Toast progress modes Toast 进度模式
    ExampleCard {
        title: Fluent.Translator.tr("gallery_d79cd9adc7a9260b", Fluent.Translator._v)
        description: Fluent.Translator.tr("gallery_2d64e8ce312f974f", Fluent.Translator._v)

        Column {
            spacing: Enums.spacing.l

            // Static showcase 静态展示
            Row {
                spacing: Enums.spacing.m

                ComponentCard {
                    label: Fluent.Translator.tr("gallery_27ce4e7bae1a94fa", Fluent.Translator._v)

                    Toast {
                        objectName: "galleryProgressToastProgressBar"
                        title: Fluent.Translator.tr("gallery_e2fc571a4cf00ceb", Fluent.Translator._v)
                        message: "60%"
                        feature: Enums.notification.feature_progress_bar
                        progress: 0.6
                        width: Enums.demoMetrics.feedbackNotificationWidth
                        duration: Enums.duration.persistent
                        visible: true
                    }
                }

                ComponentCard {
                    label: Fluent.Translator.tr("gallery_494a635922be0b85", Fluent.Translator._v)

                    Toast {
                        objectName: "galleryProgressToastIndeterminateBar"
                        title: Fluent.Translator.tr("gallery_d04fcbda737fc0c6", Fluent.Translator._v)
                        message: Fluent.Translator.tr("gallery_6a651b85a4259148", Fluent.Translator._v)
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
                    label: Fluent.Translator.tr("gallery_407b3ced57ef87c2", Fluent.Translator._v)

                    Toast {
                        objectName: "galleryProgressToastProgressRing"
                        title: Fluent.Translator.tr("gallery_403b055e56f59395", Fluent.Translator._v)
                        message: "40%"
                        feature: Enums.notification.feature_progress_ring
                        progress: 0.4
                        width: Enums.demoMetrics.feedbackNotificationWidth
                        duration: Enums.duration.persistent
                        visible: true
                    }
                }

                ComponentCard {
                    label: Fluent.Translator.tr("gallery_c26a5889102dc0c3", Fluent.Translator._v)

                    Toast {
                        objectName: "galleryProgressToastIndeterminateRing"
                        title: Fluent.Translator.tr("gallery_694b71bc8013ff43", Fluent.Translator._v)
                        message: Fluent.Translator.tr("gallery_6a651b85a4259148", Fluent.Translator._v)
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
                    text: Fluent.Translator.tr("gallery_cd2e8707a7db3b3f", Fluent.Translator._v)
                    style: Enums.button.style_primary
                    onClicked: {
                        var bar = NotificationManager.toast.progressBar(
                            root.notificationParent,
                            Fluent.Translator.tr("gallery_e2fc571a4cf00ceb", Fluent.Translator._v),
                            Fluent.Translator.tr("gallery_355f28c799501267", Fluent.Translator._v)
                        )
                        root._animateProgress(
                            bar,
                            Enums.demoMetrics.feedbackProgressBarStep,
                            Enums.duration.fast
                        )
                    }
                }

                Button {
                    text: Fluent.Translator.tr("gallery_494a635922be0b85", Fluent.Translator._v)
                    onClicked: NotificationManager.toast.indeterminateBar(
                        root.notificationParent,
                        Fluent.Translator.tr("gallery_694b71bc8013ff43", Fluent.Translator._v),
                        Fluent.Translator.tr("gallery_6a651b85a4259148", Fluent.Translator._v)
                    )
                }

                Button {
                    text: Fluent.Translator.tr("gallery_029926f219a66e79", Fluent.Translator._v)
                    onClicked: {
                        var ring = NotificationManager.toast.progressRing(
                            root.notificationParent,
                            Fluent.Translator.tr("gallery_403b055e56f59395", Fluent.Translator._v),
                            Fluent.Translator.tr("gallery_4342d63e83c75f86", Fluent.Translator._v)
                        )
                        root._animateProgress(
                            ring,
                            Enums.demoMetrics.feedbackProgressRingStep,
                            Enums.demoMetrics.feedbackProgressRingInterval
                        )
                    }
                }

                Button {
                    text: Fluent.Translator.tr("gallery_c26a5889102dc0c3", Fluent.Translator._v)
                    onClicked: NotificationManager.toast.indeterminateRing(
                        root.notificationParent,
                        Fluent.Translator.tr("gallery_bb429d0227b7d9d6", Fluent.Translator._v),
                        Fluent.Translator.tr("gallery_3c3df3f45f33435f", Fluent.Translator._v)
                    )
                }
            }
        }
    }
}
