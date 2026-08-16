// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

// 导入组件
import PrismQML
import PrismQML as Fluent
import "_internal"

// 反馈组件页面
Item {
    id: root
    
    function iconPath(name) {
        return Fluent.Enums.iconPath + name + ".svg"
    }

    Component {
        id: desktopToastAction
        Button {
            text: Fluent.Translator.tr("gallery_7d0d5850515d9421", Fluent.Translator._v)
            width: parent ? parent.width : implicitWidth
        }
    }
    
    ScrollArea {
        anchors.fill: parent
        
        Column {
            width: parent ? parent.width : 0
            spacing: Fluent.Enums.spacing.xxl
            
            // 页面标题
            Column {
                width: parent ? parent.width : 0
                spacing: Fluent.Enums.spacing.xs
                Text { text: Fluent.Translator.tr("gallery_bf367252d1ee1b72", Fluent.Translator._v); font.pixelSize: Fluent.Enums.typography.displayLarge; font.bold: true; color: Fluent.Enums.textColor.primary; font.family: Fluent.Enums.fontFamily }
                Text { text: "prismqml.controls.feedback"; font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.secondary; font.family: Fluent.Enums.fontFamily }
            }
            
            // 进度指示
            ExampleCard {
                title: Fluent.Translator.tr("gallery_b16f0cf94c81feaa", Fluent.Translator._v)
                description: "Progress (type_bar / type_bar_filled / type_ring)"
                Column {
                    spacing: Fluent.Enums.spacing.l
                    Row {
                        spacing: Fluent.Enums.spacing.xxl
                        ComponentCard { label: "type_bar"; Progress { type: Fluent.Enums.progress.type_bar; width: 140; value: 60 } }
                        ComponentCard { label: "indeterminate"; Progress { type: Fluent.Enums.progress.type_bar; width: 140; indeterminate: true } }
                        ComponentCard { label: "type_bar_filled"; Progress { type: Fluent.Enums.progress.type_bar_filled; width: 140; value: 70 } }
                    }
                    Row {
                        spacing: Fluent.Enums.spacing.xl
                        ComponentCard { label: "paused"; Progress { type: Fluent.Enums.progress.type_bar; width: 100; value: 40; paused: true } }
                        ComponentCard { label: "error"; Progress { type: Fluent.Enums.progress.type_bar; width: 100; value: 70; error: true } }
                        ComponentCard { label: "type_ring"; Progress { type: Fluent.Enums.progress.type_ring; value: 75; width: 60; height: 60 } }
                        ComponentCard { label: "ring indeterminate"; Progress { type: Fluent.Enums.progress.type_ring; indeterminate: true; width: 60; height: 60 } }
                    }
                }
            }
            
            // 骨架屏
            ExampleCard {
                title: Fluent.Translator.tr("gallery_76f59696529a636c", Fluent.Translator._v)
                description: "Skeleton (shape_rounded / shape_rect / shape_circle)"
                Column {
                    spacing: Fluent.Enums.spacing.xl
                    Row {
                        spacing: Fluent.Enums.spacing.xl
                        ComponentCard { label: "shape_rounded"; Skeleton { shape: Fluent.Enums.skeleton.shape_rounded; width: 200; height: 14 } }
                        ComponentCard { label: "shape_rect"; Skeleton { shape: Fluent.Enums.skeleton.shape_rect; width: 80; height: 80 } }
                        ComponentCard { label: "shape_circle"; Skeleton { shape: Fluent.Enums.skeleton.shape_circle; width: 60; height: 60 } }
                    }
                    Row {
                        spacing: Fluent.Enums.spacing.l
                        // 方形个人信息骨架
                        Column {
                            spacing: Fluent.Enums.spacing.none
                            Text { text: Fluent.Translator.tr("gallery_b2a08a05f90e151b", Fluent.Translator._v); font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.secondaryForeground; bottomPadding: Fluent.Enums.spacing.m }
                            Row {
                                spacing: Fluent.Enums.spacing.l
                                Skeleton { shape: Fluent.Enums.skeleton.shape_rect; width: 64; height: 64 }
                                Column {
                                    spacing: Fluent.Enums.spacing.m
                                    Skeleton { width: 200; height: 16 }
                                    Skeleton { width: 120; height: 14 }
                                }
                            }
                        }
                        // 圆形个人信息骨架
                        Column {
                            spacing: Fluent.Enums.spacing.none
                            Text { text: Fluent.Translator.tr("gallery_1840f748c438cea2", Fluent.Translator._v); font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.secondaryForeground; bottomPadding: Fluent.Enums.spacing.m }
                            Row {
                                spacing: Fluent.Enums.spacing.l
                                Skeleton { shape: Fluent.Enums.skeleton.shape_circle; width: 64; height: 64 }
                                Column {
                                    spacing: Fluent.Enums.spacing.m
                                    Skeleton { width: 200; height: 16 }
                                    Skeleton { width: 160; height: 14 }
                                }
                            }
                        }
                    }
                }
            }
            
            // Static InfoBar and Toast showcases 静态 InfoBar 与 Toast 展示
            FeedbackNotificationShowcase {}
            
            // NotificationManager surface menu NotificationManager 承载面菜单
            FeedbackNotificationMenuShowcase {
                notificationParent: root
            }

            // Desktop Toast options demo 桌面 Toast 选项演示
            ExampleCard {
                title: "NotificationManager.desktop (Toast options)"
                description: Fluent.Translator.tr("gallery_11eb088399ff4760", Fluent.Translator._v)
                Row {
                    spacing: Fluent.Enums.spacing.l
                    Button {
                        style: Fluent.Enums.button.style_filled
                        level: 1
                        text: "Success + options"
                        onClicked: NotificationManager.desktop.success(
                            Fluent.Translator.tr("gallery_053461ce86d26572", Fluent.Translator._v),
                            "00:14\nC:/recordings/clip.mp4",
                            Fluent.Enums.duration.notification,
                            Fluent.Enums.notification.posBottomRight,
                            {
                                "orient": Qt.Vertical,
                                "customContent": desktopToastAction,
                                "screen": root.Window.window.screen
                            }
                        )
                    }
                }
            }
            
            // Unified InfoBar and Toast progress showcases 统一 InfoBar 与 Toast 进度展示
            FeedbackProgressShowcase {
                notificationParent: root
            }
            
            // 状态组件 - StateWidget（统一组件）
            ExampleCard {
                title: Fluent.Translator.tr("gallery_7cffe28ddcedd1d0", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_9b6c6de92f21ee98", Fluent.Translator._v)
                Row {
                    spacing: Fluent.Enums.demoMetrics.gapLarge
                    ComponentCard { label: "type_no_data"; StateWidget { width: 160; height: 180; stateType: Fluent.Enums.state.type_no_data } }
                    ComponentCard { label: "type_result (success)"; StateWidget { width: 160; height: 180; stateType: Fluent.Enums.state.type_result; severity: "success"; title: Fluent.Translator.tr("gallery_205dfc7ce8cd7288", Fluent.Translator._v) } }
                    ComponentCard { label: "type_result (error)"; StateWidget { width: 160; height: 180; stateType: Fluent.Enums.state.type_result; severity: "error"; title: Fluent.Translator.tr("gallery_0c3b4cf7aa259edb", Fluent.Translator._v) } }
                    ComponentCard { label: "type_no_internet"; StateWidget { width: 160; height: 200; stateType: Fluent.Enums.state.type_no_internet } }
                }
            }
            
            
            // 对话框
            ExampleCard {
                title: Fluent.Translator.tr("gallery_dffaa1bf796588bc", Fluent.Translator._v)
                description: "MessageBox / DialogBoxCore / ProgressDialog"
                Column {
                    spacing: Fluent.Enums.spacing.l
                    Row {
                        spacing: Fluent.Enums.spacing.l
                        ComponentCard { label: "MessageBox"; Button { text: Fluent.Translator.tr("gallery_877850d2f430ee78", Fluent.Translator._v); onClicked: demoMessageBox.open() } }
                        ComponentCard { label: Fluent.Translator.tr("gallery_a0e0c0bae980ef35", Fluent.Translator._v); Button { text: Fluent.Translator.tr("gallery_a0e0c0bae980ef35", Fluent.Translator._v); onClicked: confirmBox.open() } }
                        ComponentCard { label: Fluent.Translator.tr("gallery_eb400e6c1e6b2899", Fluent.Translator._v); Button { text: Fluent.Translator.tr("gallery_eb400e6c1e6b2899", Fluent.Translator._v); onClicked: draggableBox.open() } }
                        ComponentCard { label: Fluent.Translator.tr("gallery_0bb79bdc93beabe5", Fluent.Translator._v); Button { text: Fluent.Translator.tr("gallery_0bb79bdc93beabe5", Fluent.Translator._v); onClicked: maskCloseBox.open() } }
                        Text { id: dialogResult; text: Fluent.Translator.tr("gallery_d1f5b5d4bdea4b12", Fluent.Translator._v); font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.secondary; topPadding: Fluent.Enums.spacing.m }
                    }
                    Row {
                        spacing: Fluent.Enums.spacing.l
                        ComponentCard { label: Fluent.Translator.tr("gallery_a500fb63eeacf9ac", Fluent.Translator._v); Button { text: Fluent.Translator.tr("gallery_a500fb63eeacf9ac", Fluent.Translator._v); onClicked: dialogDemo.open() } }
                        ComponentCard { label: "ProgressDialog"; Button { text: "ProgressDialog"; onClicked: { progressDlg.open(); progressTimer.start() } } }
                        ComponentCard { label: Fluent.Translator.tr("gallery_f10123490a7f9380", Fluent.Translator._v); Button { text: Fluent.Translator.tr("gallery_1d0be325f2993f8a", Fluent.Translator._v); onClicked: noCancelBox.open() } }
                        ComponentCard { label: Fluent.Translator.tr("gallery_fd6e988db6d48cca", Fluent.Translator._v); Button { text: Fluent.Translator.tr("gallery_a1ac66a4569080c3", Fluent.Translator._v); onClicked: copyableBox.open() } }
                    }
                }
            }
            
            // 弹出层 - Flyout (6种动画)
            ExampleCard {
                title: Fluent.Translator.tr("gallery_470739e4f4ac1431", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_087b36f7897ea738", Fluent.Translator._v)
                Row {
                    spacing: Fluent.Enums.spacing.l
                    ComponentCard {
                        label: "PullUp"
                        Button { id: flyoutBtn1; text: Fluent.Translator.tr("gallery_4c944bc1575e5d3c", Fluent.Translator._v); onClicked: flyout1.show() }
                        Flyout { id: flyout1; target: flyoutBtn1; title: Fluent.Translator.tr("gallery_f56c6c82203b33f6", Fluent.Translator._v); content: Fluent.Translator.tr("gallery_2bb39825adcd3750", Fluent.Translator._v); animationType: Fluent.Enums.flyout.pullUp }
                    }
                    ComponentCard {
                        label: "DropDown"
                        Button { id: flyoutBtn2; text: Fluent.Translator.tr("gallery_2d57905608fe316e", Fluent.Translator._v); onClicked: flyout2.show() }
                        Flyout { id: flyout2; target: flyoutBtn2; title: Fluent.Translator.tr("gallery_f56c6c82203b33f6", Fluent.Translator._v); content: Fluent.Translator.tr("gallery_02ae362b3e5af9a5", Fluent.Translator._v); animationType: Fluent.Enums.flyout.dropDown; deleteOnClose: false }
                    }
                    ComponentCard {
                        label: "SlideLeft"
                        Button { id: flyoutBtn3; text: Fluent.Translator.tr("gallery_3f481edbbfdb168b", Fluent.Translator._v); onClicked: flyout3.show() }
                        Flyout { id: flyout3; target: flyoutBtn3; title: Fluent.Translator.tr("gallery_f56c6c82203b33f6", Fluent.Translator._v); content: Fluent.Translator.tr("gallery_edebb5eedd236bfa", Fluent.Translator._v); animationType: Fluent.Enums.flyout.slideLeft; deleteOnClose: false }
                    }
                    ComponentCard {
                        label: "SlideRight"
                        Button { id: flyoutBtn5; text: Fluent.Translator.tr("gallery_7058a7d72aed6230", Fluent.Translator._v); onClicked: flyout5.show() }
                        Flyout { id: flyout5; target: flyoutBtn5; title: Fluent.Translator.tr("gallery_f56c6c82203b33f6", Fluent.Translator._v); content: Fluent.Translator.tr("gallery_186d8705e08e55e4", Fluent.Translator._v); animationType: Fluent.Enums.flyout.slideRight; deleteOnClose: false }
                    }
                    ComponentCard {
                        label: "FadeIn"
                        Button { id: flyoutBtn4; text: Fluent.Translator.tr("gallery_f72b83eaba1cc7f0", Fluent.Translator._v); onClicked: flyout4.show() }
                        Flyout { id: flyout4; target: flyoutBtn4; title: Fluent.Translator.tr("gallery_f56c6c82203b33f6", Fluent.Translator._v); content: Fluent.Translator.tr("gallery_476e94748b0959ce", Fluent.Translator._v); animationType: Fluent.Enums.flyout.fadeIn; deleteOnClose: false }
                    }
                    ComponentCard {
                        label: Fluent.Translator.tr("gallery_d31df5e84bc61e71", Fluent.Translator._v)
                        Button { id: flyoutBtn6; text: Fluent.Translator.tr("gallery_d31df5e84bc61e71", Fluent.Translator._v); onClicked: flyout6.show() }
                        Flyout { id: flyout6; target: flyoutBtn6; title: Fluent.Translator.tr("gallery_5124e57901af8928", Fluent.Translator._v); content: Fluent.Translator.tr("gallery_f86a3402e9505e66", Fluent.Translator._v); modal: false; deleteOnClose: false }
                    }
                }
            }
            
            // TeachingTip (带箭头)
            ExampleCard {
                title: Fluent.Translator.tr("gallery_4ea266b55b66cdff", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_f40558e0064fd14c", Fluent.Translator._v)
                Row {
                    spacing: Fluent.Enums.spacing.l
                    ComponentCard {
                        label: "Bottom"
                        Button { id: tipBtn1; text: Fluent.Translator.tr("gallery_3f049887991b880c", Fluent.Translator._v); onClicked: tip1.show() }
                        TeachingTip { id: tip1; target: tipBtn1; title: Fluent.Translator.tr("gallery_8828e0fec4b05a40", Fluent.Translator._v); content: Fluent.Translator.tr("gallery_96a13a16b9f46d25", Fluent.Translator._v); anchorPosition: Fluent.Enums.teachingTip.anchor_bottom; deleteOnClose: false }
                    }
                    ComponentCard {
                        label: "Top"
                        Button { id: tipBtn2; text: Fluent.Translator.tr("gallery_6f2a4a02e60e067c", Fluent.Translator._v); onClicked: tip2.show() }
                        TeachingTip { id: tip2; target: tipBtn2; title: Fluent.Translator.tr("gallery_8828e0fec4b05a40", Fluent.Translator._v); content: Fluent.Translator.tr("gallery_c6505f122d94191b", Fluent.Translator._v); anchorPosition: Fluent.Enums.teachingTip.anchor_top; deleteOnClose: false }
                    }
                    ComponentCard {
                        label: "Left"
                        Button { id: tipBtn3; text: Fluent.Translator.tr("gallery_6a24b14f33c72be4", Fluent.Translator._v); onClicked: tip3.show() }
                        TeachingTip { id: tip3; target: tipBtn3; title: Fluent.Translator.tr("gallery_8828e0fec4b05a40", Fluent.Translator._v); content: Fluent.Translator.tr("gallery_c115c0dde27a7b9a", Fluent.Translator._v); anchorPosition: Fluent.Enums.teachingTip.anchor_left; deleteOnClose: false }
                    }
                    ComponentCard {
                        label: "Right"
                        Button { id: tipBtn4; text: Fluent.Translator.tr("gallery_1cf1d4d0b24b0b16", Fluent.Translator._v); onClicked: tip4.show() }
                        TeachingTip { id: tip4; target: tipBtn4; title: Fluent.Translator.tr("gallery_8828e0fec4b05a40", Fluent.Translator._v); content: Fluent.Translator.tr("gallery_e8f5dd6d4b0a27b7", Fluent.Translator._v); anchorPosition: Fluent.Enums.teachingTip.anchor_right; deleteOnClose: false }
                    }
                    ComponentCard {
                        label: Fluent.Translator.tr("gallery_d31df5e84bc61e71", Fluent.Translator._v)
                        Button { id: tipBtnModal; text: Fluent.Translator.tr("gallery_d31df5e84bc61e71", Fluent.Translator._v); onClicked: tipModal.show() }
                        TeachingTip { id: tipModal; target: tipBtnModal; title: Fluent.Translator.tr("gallery_5124e57901af8928", Fluent.Translator._v); content: Fluent.Translator.tr("gallery_f86a3402e9505e66", Fluent.Translator._v); anchorPosition: Fluent.Enums.teachingTip.anchor_bottom; modal: false; deleteOnClose: false }
                    }
                }
            }
            FeedbackTeachingTourExample {}
            // 其他弹出组件
            ExampleCard {
                title: Fluent.Translator.tr("gallery_08f2cb12e2942057", Fluent.Translator._v)
                description: "ToolTip"
                Row {
                    spacing: Fluent.Enums.spacing.l
                    ComponentCard {
                        label: "ToolTip"
                        Rectangle {
                            width: 90; height: 30; color: Fluent.Enums.hoverColor; radius: Fluent.Enums.radius.small
                            Text { anchors.centerIn: parent; text: Fluent.Translator.tr("gallery_b70c4e8a2e1d27ad", Fluent.Translator._v); font.pixelSize: Fluent.Enums.demoMetrics.toolTipFontSize; color: Fluent.Enums.textColor.primary }
                            ToolTip { id: demoTooltip; x: (parent.width - width) / 2; y: parent.height + 5; text: Fluent.Translator.tr("gallery_497f14a4db87906b", Fluent.Translator._v) }
                            MouseArea { anchors.fill: parent; hoverEnabled: true; onEntered: demoTooltip.show(); onExited: demoTooltip.hide() }
                        }
                    }
                }
            }
            
            
            // 彩纸动画
            ExampleCard {
                title: Fluent.Translator.tr("gallery_83a058f36678dc08", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_fd58a8c832d36df0", Fluent.Translator._v)
                ComponentCard {
                    label: "Confetti"
                    Button { 
                        text: Fluent.Translator.tr("gallery_0adb4a51d235d998", Fluent.Translator._v); icon: Fluent.Enums.icon.sparkle
                        onClicked: confettiEffect.start()
                    }
                }
            }
            
        }
    }
    
    // 对话框组件 - 必须放在root级别以正确填充窗口
    MessageBox { id: demoMessageBox; title: Fluent.Translator.tr("gallery_f56c6c82203b33f6", Fluent.Translator._v); content: Fluent.Translator.tr("gallery_200bf3564876553e", Fluent.Translator._v) }
    MessageBox { 
        id: confirmBox; title: Fluent.Translator.tr("gallery_36f33adaf0942634", Fluent.Translator._v); content: Fluent.Translator.tr("gallery_7fa2094884a8778a", Fluent.Translator._v)
        onAccepted: dialogResult.text = Fluent.Translator.tr("gallery_248c56d1d038beee", Fluent.Translator._v)
        onRejected: dialogResult.text = Fluent.Translator.tr("gallery_0206596380c612b5", Fluent.Translator._v)
    }
    MessageBox { 
        id: draggableBox; title: Fluent.Translator.tr("gallery_faf52acf2fa72035", Fluent.Translator._v); content: Fluent.Translator.tr("gallery_fda29a858bda01eb", Fluent.Translator._v)
        draggable: true
    }
    MessageBox { 
        id: maskCloseBox; title: Fluent.Translator.tr("gallery_0bb79bdc93beabe5", Fluent.Translator._v); content: Fluent.Translator.tr("gallery_fc5cf77d4e27a599", Fluent.Translator._v)
        dismissOnScrimClick: true
    }
    MessageBox { 
        id: noCancelBox; title: Fluent.Translator.tr("gallery_0358d2c4093bd1d4", Fluent.Translator._v); content: Fluent.Translator.tr("gallery_9c21f6dad136bcb7", Fluent.Translator._v)
        cancelButtonVisible: false
    }
    MessageBox { 
        id: copyableBox; title: Fluent.Translator.tr("gallery_a6cc5d53a3888b48", Fluent.Translator._v); content: Fluent.Translator.tr("gallery_91c9e9dd5d5635c9", Fluent.Translator._v)
        contentCopyable: true
    }
    // Dialog - 无边框对话框
    MessageBox { id: dialogDemo; title: Fluent.Translator.tr("gallery_13a8f3d660ec7a2d", Fluent.Translator._v); content: Fluent.Translator.tr("gallery_104eef2a24a54e2a", Fluent.Translator._v) }
    ProgressDialog { id: progressDlg; title: Fluent.Translator.tr("gallery_9cbb625342267237", Fluent.Translator._v); content: Fluent.Translator.tr("gallery_f1bd46290e9ead41", Fluent.Translator._v); maxWaitingTime: Fluent.Enums.duration.toast; onTimeout: progressTimer.stop() }
    Timer { id: progressTimer; interval: Fluent.Enums.duration.toast; onTriggered: progressDlg.close() }
    
    // 彩纸效果 - 显示在主窗口级别
    Confetti { id: confettiEffect }
}
