// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick.Controls
import QtQuick.Dialogs
import "../.."
import "../icons"
import "../dialogs"
import "../data/Label"
import "_internal"
import QtQuick.Window  // 置于库import后:原生Window名归库后不被覆盖
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// ImageCropper - Unified image cropper 统一图片裁剪器
// type_dialog: standalone window 独立窗口
// type_overlay: overlay on parent (like MessageBox) 遮罩覆盖
Item {
    id: control
    
    // ==================== Translation Trigger 翻译触发器 ====================
    readonly property int _tv: Translator._v
    
    // ==================== Public Props 公开属性 ====================
    property int type: Enums.imageCropper.type_dialog
    property url source: ""
    property int cropShape: Enums.imageCropper.shape_rect
    property real aspectRatio: 0
    property rect cropRect: Qt.rect(
        Enums.imageCropperDialogMetrics.cropRectDefaultX,
        Enums.imageCropperDialogMetrics.cropRectDefaultY,
        Enums.imageCropperDialogMetrics.cropRectDefaultW,
        Enums.imageCropperDialogMetrics.cropRectDefaultH
    )
    
    // ==================== Signals 信号 ====================
    signal accepted(rect cropRect)
    signal rejected()
    signal imageSelected(url source)
    
    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.imageCropperDialogMetrics.previewWidth
    implicitHeight: Enums.imageCropperDialogMetrics.previewHeight

    // ==================== Public Methods 公开方法 ====================
    function open() {
        if (control.type === Enums.imageCropper.type_dialog) {
            cropWindow.show()
        } else {
            overlayPanel.initDefaultCropRect()
            cropOverlay.open()
        }
    }

    function close() {
        if (control.type === Enums.imageCropper.type_dialog) {
            cropWindow.close()
        } else {
            cropOverlay.close()
        }
    }

    function openWithSource(imageUrl) {
        control.source = imageUrl
        control.open()
    }

    // ==================== Preview Thumbnail 预览缩略图 ====================
    Rectangle {
        anchors.fill: parent
        radius: Enums.radius.small
        color: Enums.gray.background
        border.width: Enums.border.thin
        border.color: Enums.gray.border
        
        Image {
            anchors.fill: parent
            anchors.margins: Enums.spacing.xs
            source: control.source
            fillMode: Image.PreserveAspectCrop
            visible: control.source.toString() !== ""
        }
        
        Column {
            anchors.centerIn: parent
            spacing: Enums.spacing.xxs
            visible: control.source.toString() === ""
            
            Icon {
                anchors.horizontalCenter: parent.horizontalCenter
                icon: Enums.icon.image
                iconSize: Enums.iconSize.m
                color: Enums.gray.disabled
            }
            Label {
                type: Enums.label.type_caption
                anchors.horizontalCenter: parent.horizontalCenter
                text: { control._tv; return Translator.tr("select_image") }
                color: Enums.gray.text
            }
        }
        
        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: fileDialog.open()
        }
    }
    
    // ==================== File Dialog 文件对话框 ====================
    FileDialog {
        id: fileDialog
        title: { control._tv; return Translator.tr("select_image") }
        nameFilters: ["Image files (*.png *.jpg *.jpeg *.bmp *.gif)"]
        onAccepted: {
            control.source = selectedFile
            control.imageSelected(selectedFile)
            control.open()
        }
    }

    // ==================== Dialog Mode 窗口模式 ====================
    Window {
        id: cropWindow
        title: { control._tv; return Translator.tr("crop_image") }
        width: Enums.imageCropperDialogMetrics.panelWidth
        height: Enums.imageCropperDialogMetrics.panelHeight
        color: Enums.gray.background
        modality: Qt.ApplicationModal
        flags: Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint
        visible: false
        
        ImageCropperPanel {
            id: dialogPanel
            anchors.fill: parent
            anchors.margins: Enums.spacing.xxl
            source: control.source
            cropShape: control.cropShape
            cropRect: control.cropRect
            onCropRectUpdated: (newRect) => { control.cropRect = newRect }
            onConfirmClicked: { cropWindow.close(); control.accepted(control.cropRect) }
            onCancelClicked: { cropWindow.close(); control.rejected() }
        }
        
        onVisibleChanged: {
            if (visible) dialogPanel.initDefaultCropRect()
        }
    }

    // ==================== Overlay Mode 遮罩模式 ====================
    // 不声明式挂 Overlay.overlay: 那样组件一创建就把自己塞进全局 QQuickOverlay,
    // 即便从未 open(_isOpen=false / visible=false), QQuickOverlay 仍会因有子项而
    // visible=true + enabled, 全屏 1200x800 吃掉所有鼠标点击(导致页面切过来后导航/
    // 内容点不动)。改为不指定 parent —— 默认留在 control 局部(invisible 不拦截),
    // 由 OverlayDialogCore.open() 在打开时经 _resolveOverlayTarget() 自动升到
    // Window.contentItem, 与项目其它 dialog 行为一致。
    DialogBoxCore {
        id: cropOverlay
        actionsVisible: false
        
        ImageCropperPanel {
            id: overlayPanel
            implicitWidth: Enums.imageCropperDialogMetrics.panelWidth
            implicitHeight: Enums.imageCropperDialogMetrics.panelHeight
            source: control.source
            cropShape: control.cropShape
            cropRect: control.cropRect
            onCropRectUpdated: (newRect) => { control.cropRect = newRect }
            onConfirmClicked: { cropOverlay.close(); control.accepted(control.cropRect) }
            onCancelClicked: { cropOverlay.close(); control.rejected() }
        }
    }
}
