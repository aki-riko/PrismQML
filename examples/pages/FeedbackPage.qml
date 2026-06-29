// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

// 导入组件
import PrismQML
import PrismQML as Fluent

// 反馈组件页面
Item {
    id: root
    
    function iconPath(name) {
        return Fluent.Enums.iconPath + name + ".svg"
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
                Text { text: "反馈组件"; font.pixelSize: Fluent.Enums.typography.displayLarge; font.bold: true; color: Fluent.Enums.textColor.primary; font.family: Fluent.Enums.fontFamily }
                Text { text: "prismqml.controls.feedback"; font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.secondary; font.family: Fluent.Enums.fontFamily }
            }
            
            // 进度指示
            ExampleCard {
                title: "进度指示"
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
                title: "骨架屏"
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
                            Text { text: "方形个人信息骨架"; font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.secondaryForeground; bottomPadding: Fluent.Enums.spacing.m }
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
                            Text { text: "圆形个人信息骨架"; font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.secondaryForeground; bottomPadding: Fluent.Enums.spacing.m }
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
            
            // 信息条
            ExampleCard {
                title: "信息条"
                description: "InfoBar"
                Column {
                    spacing: Fluent.Enums.spacing.m
                    ComponentCard { label: "severity: info"; InfoBar { title: "Info"; content: "信息提示"; severity: "info"; width: 320; duration: Fluent.Enums.duration.notification } }
                    ComponentCard { label: "severity: success"; InfoBar { title: "Success"; content: "操作成功"; severity: "success"; width: 320; duration: Fluent.Enums.duration.notification } }
                    ComponentCard { label: "severity: warning"; InfoBar { title: "Warning"; content: "请注意"; severity: "warning"; width: 320; duration: Fluent.Enums.duration.notification } }
                    ComponentCard { label: "severity: error"; InfoBar { title: "Error"; content: "发生错误"; severity: "error"; width: 320; duration: Fluent.Enums.duration.notification } }
                    ComponentCard { label: "severity: processing"; InfoBar { title: "Processing"; content: "处理中..."; severity: "processing"; width: 320; duration: Fluent.Enums.duration.notification } }
                }
            }
            
            // NotificationManager - InfoBar - 6个位置
            ExampleCard {
                title: "NotificationManager.infoBar"
                description: "InfoBar - 左上/中上/右上/左下/中下/右下"
                Row {
                    spacing: Fluent.Enums.spacing.l
                    Button { style: Fluent.Enums.button.style_filled; level: 0; text: "Info"; onClicked: NotificationManager.infoBar.info(root, "提示", "左上位置", Fluent.Enums.duration.notification, 0) }
                    Button { style: Fluent.Enums.button.style_filled; level: 1; text: "Success"; onClicked: NotificationManager.infoBar.success(root, "成功", "中上位置", Fluent.Enums.duration.notification, 1) }
                    Button { style: Fluent.Enums.button.style_filled; level: 2; text: "Warning"; onClicked: NotificationManager.infoBar.warning(root, "警告", "右上位置", Fluent.Enums.duration.notification, 2) }
                    Button { style: Fluent.Enums.button.style_filled; level: 3; text: "Error"; onClicked: NotificationManager.infoBar.error(root, "错误", "左下位置", Fluent.Enums.duration.notification, 3) }
                    Button { style: Fluent.Enums.button.style_filled; level: 4; text: "Attention"; onClicked: NotificationManager.infoBar.attention(root, "注意", "中下位置", Fluent.Enums.duration.notification, 4) }
                    Button { style: Fluent.Enums.button.style_filled; level: 5; text: "Processing"; onClicked: NotificationManager.infoBar.processing(root, "处理中", "右下位置", Fluent.Enums.duration.notification, 5) }
                }
            }
            
            // NotificationManager - Toast - 6个位置
            ExampleCard {
                title: "NotificationManager.toast"
                description: "Toast - 左上/中上/右上/左下/中下/右下"
                Row {
                    spacing: Fluent.Enums.spacing.l
                    Button { style: Fluent.Enums.button.style_filled; level: 0; text: "Info"; onClicked: NotificationManager.toast.info(root, "提示", "左上位置", Fluent.Enums.duration.notification, 0) }
                    Button { style: Fluent.Enums.button.style_filled; level: 1; text: "Success"; onClicked: NotificationManager.toast.success(root, "成功", "中上位置", Fluent.Enums.duration.notification, 1) }
                    Button { style: Fluent.Enums.button.style_filled; level: 2; text: "Warning"; onClicked: NotificationManager.toast.warning(root, "警告", "右上位置", Fluent.Enums.duration.notification, 2) }
                    Button { style: Fluent.Enums.button.style_filled; level: 3; text: "Error"; onClicked: NotificationManager.toast.error(root, "错误", "左下位置", Fluent.Enums.duration.notification, 3) }
                    Button { style: Fluent.Enums.button.style_filled; level: 4; text: "Attention"; onClicked: NotificationManager.toast.attention(root, "注意", "中下位置", Fluent.Enums.duration.notification, 4) }
                    Button { style: Fluent.Enums.button.style_filled; level: 5; text: "Processing"; onClicked: NotificationManager.toast.processing(root, "处理中", "右下位置", Fluent.Enums.duration.notification, 5) }
                }
            }
            
            // NotificationManager - Desktop (InfoBar样式) - 6个位置
            ExampleCard {
                title: "NotificationManager.desktop (InfoBar)"
                description: "桌面InfoBar通知 (独立窗口) - 左上/中上/右上/左下/中下/右下"
                Row {
                    spacing: Fluent.Enums.spacing.l
                    Button { style: Fluent.Enums.button.style_filled; level: 0; text: "Info"; onClicked: NotificationManager.desktop.infoBar("info", "提示", "左上位置", Fluent.Enums.duration.notification, 0) }
                    Button { style: Fluent.Enums.button.style_filled; level: 1; text: "Success"; onClicked: NotificationManager.desktop.infoBar("success", "成功", "中上位置", Fluent.Enums.duration.notification, 1) }
                    Button { style: Fluent.Enums.button.style_filled; level: 2; text: "Warning"; onClicked: NotificationManager.desktop.infoBar("warning", "警告", "右上位置", Fluent.Enums.duration.notification, 2) }
                    Button { style: Fluent.Enums.button.style_filled; level: 3; text: "Error"; onClicked: NotificationManager.desktop.infoBar("error", "错误", "左下位置", Fluent.Enums.duration.notification, 3) }
                    Button { style: Fluent.Enums.button.style_filled; level: 4; text: "Attention"; onClicked: NotificationManager.desktop.infoBar("attention", "注意", "中下位置", Fluent.Enums.duration.notification, 4) }
                    Button { style: Fluent.Enums.button.style_filled; level: 5; text: "Processing"; onClicked: NotificationManager.desktop.infoBar("processing", "处理中", "右下位置", Fluent.Enums.duration.notification, 5) }
                }
            }
            
            // NotificationManager - Desktop (Toast样式) - 6个位置
            ExampleCard {
                title: "NotificationManager.desktop (Toast)"
                description: "桌面Toast通知 (独立窗口) - 左上/中上/右上/左下/中下/右下"
                Row {
                    spacing: Fluent.Enums.spacing.l
                    Button { style: Fluent.Enums.button.style_filled; level: 0; text: "Info"; onClicked: NotificationManager.desktop.info("提示", "左上位置", Fluent.Enums.duration.notification, 0) }
                    Button { style: Fluent.Enums.button.style_filled; level: 1; text: "Success"; onClicked: NotificationManager.desktop.success("成功", "中上位置", Fluent.Enums.duration.notification, 1) }
                    Button { style: Fluent.Enums.button.style_filled; level: 2; text: "Warning"; onClicked: NotificationManager.desktop.warning("警告", "右上位置", Fluent.Enums.duration.notification, 2) }
                    Button { style: Fluent.Enums.button.style_filled; level: 3; text: "Error"; onClicked: NotificationManager.desktop.error("错误", "左下位置", Fluent.Enums.duration.notification, 3) }
                    Button { style: Fluent.Enums.button.style_filled; level: 4; text: "Attention"; onClicked: NotificationManager.desktop.info("注意", "中下位置", Fluent.Enums.duration.notification, 4) }
                    Button { style: Fluent.Enums.button.style_filled; level: 5; text: "Processing"; onClicked: NotificationManager.desktop.info("处理中", "右下位置", Fluent.Enums.duration.notification, 5) }
                }
            }
            
            // InfoBar进度模式
            ExampleCard {
                title: "InfoBar 进度模式"
                description: "五种进度feature：普通/进度条/不确定进度条/进度环/不确定进度环"
                Column {
                    spacing: Fluent.Enums.spacing.l
                    
                    // 静态展示
                    Row {
                        spacing: Fluent.Enums.spacing.m
                        ComponentCard { 
                            label: "进度条 60%"
                            InfoBar { 
                                title: "下载中"; message: "60%"
                                feature: Fluent.Enums.notification.feature_progress_bar
                                progress: 0.6; width: 280
                                duration: Fluent.Enums.duration.notification
                            }
                        }
                        ComponentCard { 
                            label: "不确定进度条"
                            InfoBar { 
                                title: "加载中"; message: "请稍候..."
                                feature: Fluent.Enums.notification.feature_indeterminate_bar
                                width: 280
                                duration: Fluent.Enums.duration.notification
                            }
                        }
                    }
                    Row {
                        spacing: Fluent.Enums.spacing.m
                        ComponentCard { 
                            label: "进度环 40%"
                            InfoBar { 
                                title: "上传中"; message: "40%"
                                feature: Fluent.Enums.notification.feature_progress_ring
                                progress: 0.4; width: 280
                                duration: Fluent.Enums.duration.notification
                            }
                        }
                        ComponentCard { 
                            label: "不确定进度环"
                            InfoBar { 
                                title: "处理中"; message: "请稍候..."
                                feature: Fluent.Enums.notification.feature_indeterminate_ring
                                width: 280
                                duration: Fluent.Enums.duration.notification
                            }
                        }
                    }
                    
                    // 弹出演示
                    Row {
                        spacing: Fluent.Enums.spacing.l
                        Button { 
                            text: "进度条"; style: Fluent.Enums.button.style_primary
                            onClicked: {
                                var bar = NotificationManager.infoBar.progressBar(root, "下载中", "正在下载文件...")
                                // 模拟进度
                                var progress = 0
                                var timer = Qt.createQmlObject('import QtQuick; Timer { interval: 100; repeat: true; running: true }', bar)
                                timer.triggered.connect(function() {
                                    progress += 0.05
                                    bar.progress = progress
                                    if (progress >= 1) timer.destroy()
                                })
                            }
                        }
                        Button { text: "不确定进度条"; onClicked: NotificationManager.infoBar.indeterminateBar(root, "加载中", "正在处理...") }
                        Button { 
                            text: "进度环"
                            onClicked: {
                                var ring = NotificationManager.infoBar.progressRing(root, "上传中", "正在上传...")
                                var progress = 0
                                var timer = Qt.createQmlObject('import QtQuick; Timer { interval: 80; repeat: true; running: true }', ring)
                                timer.triggered.connect(function() {
                                    progress += 0.03
                                    ring.progress = progress
                                    if (progress >= 1) timer.destroy()
                                })
                            }
                        }
                        Button { text: "不确定进度环"; onClicked: NotificationManager.infoBar.indeterminateRing(root, "同步中", "正在同步数据...") }
                    }
                }
            }
            
            // Toast进度模式
            ExampleCard {
                title: "Toast 进度模式"
                description: "Toast的四种进度feature"
                Row {
                    spacing: Fluent.Enums.spacing.l
                    Button { 
                        text: "进度条"; style: Fluent.Enums.button.style_primary
                        onClicked: {
                            var bar = NotificationManager.toast.progressBar(root, "下载中", "正在下载...")
                            var progress = 0
                            var timer = Qt.createQmlObject('import QtQuick; Timer { interval: 100; repeat: true; running: true }', bar)
                            timer.triggered.connect(function() {
                                progress += 0.05
                                bar.progress = progress
                                if (progress >= 1) timer.destroy()
                            })
                        }
                    }
                    Button { text: "不确定进度条"; onClicked: NotificationManager.toast.indeterminateBar(root, "处理中", "请稍候...") }
                    Button { 
                        text: "进度环"
                        onClicked: {
                            var ring = NotificationManager.toast.progressRing(root, "上传中", "正在上传...")
                            var progress = 0
                            var timer = Qt.createQmlObject('import QtQuick; Timer { interval: 80; repeat: true; running: true }', ring)
                            timer.triggered.connect(function() {
                                progress += 0.03
                                ring.progress = progress
                                if (progress >= 1) timer.destroy()
                            })
                        }
                    }
                    Button { text: "不确定进度环"; onClicked: NotificationManager.toast.indeterminateRing(root, "同步中", "正在同步...") }
                }
            }
            
            // 状态组件 - StateWidget（统一组件）
            ExampleCard {
                title: "状态组件"
                description: "StateWidget（统一状态组件，用stateType区分）"
                Row {
                    spacing: Fluent.Enums.demoMetrics.gapLarge
                    ComponentCard { label: "type_no_data"; StateWidget { width: 160; height: 180; stateType: Fluent.Enums.state.type_no_data } }
                    ComponentCard { label: "type_result (success)"; StateWidget { width: 160; height: 180; stateType: Fluent.Enums.state.type_result; severity: "success"; title: "提交成功" } }
                    ComponentCard { label: "type_result (error)"; StateWidget { width: 160; height: 180; stateType: Fluent.Enums.state.type_result; severity: "error"; title: "操作失败" } }
                    ComponentCard { label: "type_no_internet"; StateWidget { width: 160; height: 200; stateType: Fluent.Enums.state.type_no_internet } }
                }
            }
            
            
            // 对话框
            ExampleCard {
                title: "对话框"
                description: "MessageBox / DialogBoxCore / ProgressDialog"
                Column {
                    spacing: Fluent.Enums.spacing.l
                    Row {
                        spacing: Fluent.Enums.spacing.l
                        ComponentCard { label: "MessageBox"; Button { text: "消息框"; onClicked: demoMessageBox.open() } }
                        ComponentCard { label: "确认框"; Button { text: "确认框"; onClicked: confirmBox.open() } }
                        ComponentCard { label: "可拖拽"; Button { text: "可拖拽"; onClicked: draggableBox.open() } }
                        ComponentCard { label: "点击遮罩关闭"; Button { text: "点击遮罩关闭"; onClicked: maskCloseBox.open() } }
                        Text { id: dialogResult; text: "结果: 未操作"; font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.secondary; topPadding: Fluent.Enums.spacing.m }
                    }
                    Row {
                        spacing: Fluent.Enums.spacing.l
                        ComponentCard { label: "无边框对话框"; Button { text: "无边框对话框"; onClicked: dialogDemo.open() } }
                        ComponentCard { label: "ProgressDialog"; Button { text: "ProgressDialog"; onClicked: { progressDlg.open(); progressTimer.start() } } }
                        ComponentCard { label: "隐藏取消按钮"; Button { text: "隐藏取消"; onClicked: noCancelBox.open() } }
                        ComponentCard { label: "内容可复制"; Button { text: "可复制"; onClicked: copyableBox.open() } }
                    }
                }
            }
            
            // 弹出层 - Flyout (6种动画)
            ExampleCard {
                title: "Flyout 弹出层"
                description: "Flyout - 6种动画: pullUp/dropDown/slideLeft/slideRight/fadeIn/none + modal模态"
                Row {
                    spacing: Fluent.Enums.spacing.l
                    ComponentCard {
                        label: "PullUp"
                        Button { id: flyoutBtn1; text: "上拉"; onClicked: flyout1.show() }
                        Flyout { id: flyout1; target: flyoutBtn1; title: "提示"; content: "上拉弹出"; animationType: Fluent.Enums.flyout.pullUp }
                    }
                    ComponentCard {
                        label: "DropDown"
                        Button { id: flyoutBtn2; text: "下拉"; onClicked: flyout2.show() }
                        Flyout { id: flyout2; target: flyoutBtn2; title: "提示"; content: "下拉弹出"; animationType: Fluent.Enums.flyout.dropDown; deleteOnClose: false }
                    }
                    ComponentCard {
                        label: "SlideLeft"
                        Button { id: flyoutBtn3; text: "左滑"; onClicked: flyout3.show() }
                        Flyout { id: flyout3; target: flyoutBtn3; title: "提示"; content: "左滑弹出"; animationType: Fluent.Enums.flyout.slideLeft; deleteOnClose: false }
                    }
                    ComponentCard {
                        label: "SlideRight"
                        Button { id: flyoutBtn5; text: "右滑"; onClicked: flyout5.show() }
                        Flyout { id: flyout5; target: flyoutBtn5; title: "提示"; content: "右滑弹出"; animationType: Fluent.Enums.flyout.slideRight; deleteOnClose: false }
                    }
                    ComponentCard {
                        label: "FadeIn"
                        Button { id: flyoutBtn4; text: "淡入"; onClicked: flyout4.show() }
                        Flyout { id: flyout4; target: flyoutBtn4; title: "提示"; content: "淡入弹出"; animationType: Fluent.Enums.flyout.fadeIn; deleteOnClose: false }
                    }
                    ComponentCard {
                        label: "非模态"
                        Button { id: flyoutBtn6; text: "非模态"; onClicked: flyout6.show() }
                        Flyout { id: flyout6; target: flyoutBtn6; title: "非模态提示"; content: "不会自动关闭"; modal: false; deleteOnClose: false }
                    }
                }
            }
            
            // TeachingTip (带箭头)
            ExampleCard {
                title: "TeachingTip 教学提示"
                description: "TeachingTip - 带箭头的教学提示 (anchor_bottom/top/left/right...)"
                Row {
                    spacing: Fluent.Enums.spacing.l
                    ComponentCard {
                        label: "Bottom"
                        Button { id: tipBtn1; text: "底部"; onClicked: tip1.show() }
                        TeachingTip { id: tip1; target: tipBtn1; title: "教程"; content: "底部箭头"; anchorPosition: Fluent.Enums.teachingTip.anchor_bottom; deleteOnClose: false }
                    }
                    ComponentCard {
                        label: "Top"
                        Button { id: tipBtn2; text: "顶部"; onClicked: tip2.show() }
                        TeachingTip { id: tip2; target: tipBtn2; title: "教程"; content: "顶部箭头"; anchorPosition: Fluent.Enums.teachingTip.anchor_top; deleteOnClose: false }
                    }
                    ComponentCard {
                        label: "Left"
                        Button { id: tipBtn3; text: "左侧"; onClicked: tip3.show() }
                        TeachingTip { id: tip3; target: tipBtn3; title: "教程"; content: "左侧箭头"; anchorPosition: Fluent.Enums.teachingTip.anchor_left; deleteOnClose: false }
                    }
                    ComponentCard {
                        label: "Right"
                        Button { id: tipBtn4; text: "右侧"; onClicked: tip4.show() }
                        TeachingTip { id: tip4; target: tipBtn4; title: "教程"; content: "右侧箭头"; anchorPosition: Fluent.Enums.teachingTip.anchor_right; deleteOnClose: false }
                    }
                    ComponentCard {
                        label: "非模态"
                        Button { id: tipBtnModal; text: "非模态"; onClicked: tipModal.show() }
                        TeachingTip { id: tipModal; target: tipBtnModal; title: "非模态提示"; content: "不会自动关闭"; anchorPosition: Fluent.Enums.teachingTip.anchor_bottom; modal: false; deleteOnClose: false }
                    }
                }
            }
            
            
            // 其他弹出组件
            ExampleCard {
                title: "其他弹出组件"
                description: "ToolTip"
                Row {
                    spacing: Fluent.Enums.spacing.l
                    ComponentCard {
                        label: "ToolTip"
                        Rectangle {
                            width: 90; height: 30; color: Fluent.Enums.hoverColor; radius: Fluent.Enums.radius.small
                            Text { anchors.centerIn: parent; text: "悬浮"; font.pixelSize: Fluent.Enums.demoMetrics.toolTipFontSize; color: Fluent.Enums.textColor.primary }
                            ToolTip { id: demoTooltip; x: (parent.width - width) / 2; y: parent.height + 5; text: "这是ToolTip" }
                            MouseArea { anchors.fill: parent; hoverEnabled: true; onEntered: demoTooltip.show(); onExited: demoTooltip.hide() }
                        }
                    }
                }
            }
            
            
            // 彩纸动画
            ExampleCard {
                title: "彩纸动画"
                description: "Confetti（显示在主窗口）"
                ComponentCard {
                    label: "Confetti"
                    Button { 
                        text: "触发彩纸"; icon: Fluent.Enums.icon.sparkle
                        onClicked: confettiEffect.start()
                    }
                }
            }
            
        }
    }
    
    // 对话框组件 - 必须放在root级别以正确填充窗口
    MessageBox { id: demoMessageBox; title: "提示"; content: "这是一条消息" }
    MessageBox { 
        id: confirmBox; title: "确认"; content: "确定要执行此操作吗？"
        onAccepted: dialogResult.text = "结果: 确定"
        onRejected: dialogResult.text = "结果: 取消"
    }
    MessageBox { 
        id: draggableBox; title: "可拖拽对话框"; content: "拖动此对话框试试"
        draggable: true
    }
    MessageBox { 
        id: maskCloseBox; title: "点击遮罩关闭"; content: "点击遮罩层可以关闭此对话框"
        dismissOnScrimClick: true
    }
    MessageBox { 
        id: noCancelBox; title: "仅确定按钮"; content: "此对话框只有确定按钮"
        cancelButtonVisible: false
    }
    MessageBox { 
        id: copyableBox; title: "可复制内容"; content: "选中此文本可以复制：PrismQML是一个QML组件库"
        contentCopyable: true
    }
    // Dialog - 无边框对话框
    MessageBox { id: dialogDemo; title: "这是一个无边框对话框"; content: "这是一个无边框对话框的示例内容，可以在这里放置任意自定义文本，用于演示对话框的标题、正文与按钮布局效果。" }
    ProgressDialog { id: progressDlg; title: "请耐心等待..."; content: "正在准备下载任务中 ..."; maxWaitingTime: Fluent.Enums.duration.toast; onTimeout: progressTimer.stop() }
    Timer { id: progressTimer; interval: Fluent.Enums.duration.toast; onTriggered: progressDlg.close() }
    
    // 彩纸效果 - 显示在主窗口级别
    Confetti { id: confettiEffect }
}
