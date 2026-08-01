// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

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

    // ==================== Internal Props 内部属性 ====================
    property var _dialogHost: null
    property var _overlayHost: null
    property bool _completed: false

    // ==================== Readonly State 只读状态 ====================
    readonly property int _tv: Translator._v
    readonly property int _previewRadius: Enums.radius.small
    readonly property color _previewBackground: Enums.gray.background
    readonly property color _previewBorderColor: Enums.gray.border
    readonly property color _previewIconColor: Enums.gray.disabled
    readonly property color _previewTextColor: Enums.gray.text
    readonly property color _dialogBackground: Enums.gray.background
    
    // ==================== Signals 信号 ====================
    signal accepted(rect cropRect)
    signal rejected()
    signal imageSelected(url source)

    // ==================== Public Methods 公开方法 ====================
    function open() {
        var host = _ensureCurrentHost()
        if (!host) return
        if (control.type === Enums.imageCropper.type_dialog) {
            host.show()
        } else {
            host.initDefaultCropRect()
            host.open()
        }
    }

    function close() {
        if (control.type === Enums.imageCropper.type_dialog) {
            if (_dialogHost) _dialogHost.close()
        } else {
            if (_overlayHost) _overlayHost.close()
        }
    }

    function openWithSource(imageUrl) {
        control.source = imageUrl
        control.open()
    }

    // ==================== Internal Methods 内部方法 ====================
    function _ensureDialogHost() {
        if (!_dialogHost) {
            _dialogHost = dialogHostComponent.createObject(control)
            if (!_dialogHost) console.error("ImageCropper: Failed to create dialog host.")
        }
        return _dialogHost
    }

    function _ensureOverlayHost() {
        if (!_overlayHost) {
            _overlayHost = overlayHostComponent.createObject(control)
            if (!_overlayHost) console.error("ImageCropper: Failed to create overlay host.")
        }
        return _overlayHost
    }

    function _ensureCurrentHost() {
        return control.type === Enums.imageCropper.type_dialog
            ? _ensureDialogHost() : _ensureOverlayHost()
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.imageCropperDialogMetrics.previewWidth
    implicitHeight: Enums.imageCropperDialogMetrics.previewHeight

    Component.onCompleted: {
        _completed = true
        _ensureCurrentHost()
    }
    onTypeChanged: if (_completed) _ensureCurrentHost()

    // ==================== Content 内容 ====================
    // Preview thumbnail 预览缩略图
    Rectangle {
        anchors.fill: parent
        radius: control._previewRadius
        color: control._previewBackground
        border.width: Enums.border.thin
        border.color: control._previewBorderColor
        
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
                color: control._previewIconColor
            }
            Label {
                type: Enums.label.type_caption
                anchors.horizontalCenter: parent.horizontalCenter
                text: { control._tv; return Translator.tr("select_image") }
                color: control._previewTextColor
            }
        }
        
        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: fileDialog.open()
        }
    }
    
    // File dialog 文件对话框
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

    // Dialog mode 窗口模式
    Component {
        id: dialogHostComponent

        Window {
            id: cropWindow
            title: { control._tv; return Translator.tr("crop_image") }
            width: Enums.imageCropperDialogMetrics.panelWidth
            height: Enums.imageCropperDialogMetrics.panelHeight
            color: control._dialogBackground
            modality: Qt.ApplicationModal
            flags: Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint
            visible: false

            onVisibleChanged: {
                if (visible) dialogPanel.initDefaultCropRect()
            }

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
        }
    }

    // Overlay mode 遮罩模式
    // 不声明式挂 Overlay.overlay: 那样组件一创建就把自己塞进全局 QQuickOverlay,
    // 即便从未 open(_isOpen=false / visible=false), QQuickOverlay 仍会因有子项而
    // visible=true + enabled, 全屏 1200x800 吃掉所有鼠标点击(导致页面切过来后导航/
    // 内容点不动)。改为不指定 parent —— 默认留在 control 局部(invisible 不拦截),
    // 由 OverlayDialogCore.open() 在打开时经 _resolveOverlayTarget() 自动升到
    // Window.contentItem, 与项目其它 dialog 行为一致。
    Component {
        id: overlayHostComponent

        DialogBoxCore {
            id: cropOverlay

            function initDefaultCropRect() {
                overlayPanel.initDefaultCropRect()
            }

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
}
