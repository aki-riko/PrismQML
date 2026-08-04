// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Dialogs
import "../../.."
import "../../icons"
import "../../inputs"
import "../Label"

// AvatarSelector - Avatar selector component 头像选择器组件
// Extends Avatar with file selection and cropping 扩展Avatar添加文件选择和裁剪
Avatar {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property bool enableCrop: true  // Enable crop dialog 启用裁剪对话框
    property rect cropRect: Qt.rect(0.1, 0.1, 0.8, 0.8)  // Crop rect (normalized) 裁剪区域
    property string changeText: ""  // Change button text 更换按钮文本
    property string placeholderIcon: ""  // Placeholder icon 占位图标

    // ==================== Readonly State 只读状态 ====================
    readonly property bool hovered: mouseArea.containsMouse
    readonly property string _defaultChangeText: {
        Translator._v
        return Translator.tr("change")
    }
    readonly property string _imageFilesText: {
        Translator._v
        return Translator.tr("image_files")
    }

    // ==================== Internal Props 内部属性 ====================
    property var _fileDialog: null
    property var _cropperDialog: null

    // ==================== Signals 信号 ====================
    signal clicked()
    signal avatarChanged(url newSource)
    signal cropConfirmed(url source, rect cropRect)

    // ==================== Public Methods 公开方法 ====================
    function setAvatar(url) {
        control.source = url
        control.avatarChanged(url)
    }

    // Open file dialog 打开文件对话框
    function openFilePicker() {
        var dialog = _ensureFileDialog()
        if (!dialog) {
            console.error("AvatarSelector: Failed to create FileDialog.")
            return
        }
        dialog.open()
    }

    // ==================== Internal Methods 内部方法 ====================
    function _ensureFileDialog() {
        if (!_fileDialog) _fileDialog = fileDialogComponent.createObject(control)
        return _fileDialog
    }

    function _ensureCropperDialog() {
        if (!_cropperDialog) _cropperDialog = cropperDialogComponent.createObject(control)
        return _cropperDialog
    }

    function _prewarmDialogs() {
        _ensureFileDialog()
        if (enableCrop) _ensureCropperDialog()
    }

    // ==================== Content 内容 ====================
    // Hover overlay 悬停遮罩
    Rectangle {
        anchors.fill: parent
        radius: parent.radius
        color: Enums.stateColor.dialogOverlay
        opacity: hovered ? 1 : 0
        antialiasing: true
        
        Behavior on opacity { NumberAnimation { duration: Enums.duration.normal } }
        
        Column {
            anchors.centerIn: parent
            spacing: Enums.spacing.xs
            
            Icon {
                anchors.horizontalCenter: parent.horizontalCenter
                iconSize: control.size * 0.35
                color: Enums.themeColors.accentForeground
                icon: Enums.icon.camera
            }
            
            Label {
                type: Enums.label.type_caption
                anchors.horizontalCenter: parent.horizontalCenter
                text: control.changeText || control._defaultChangeText
                color: Enums.themeColors.accentForeground
            }
        }
    }

    // Interaction 交互
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        enabled: control.enabled
        hoverEnabled: true
        onEntered: control._prewarmDialogs()
        onClicked: {
            control.clicked()
            control.openFilePicker()
        }
    }
    
    // File dialog 文件对话框
    Component {
        id: fileDialogComponent

        FileDialog {
            title: { Translator._v; return Translator.tr("select_avatar") }
            nameFilters: [control._imageFilesText + " (*.png *.jpg *.jpeg *.bmp *.gif)"]
            onAccepted: {
                if (control.enableCrop) {
                    var cropper = control._ensureCropperDialog()
                    if (!cropper) {
                        console.error("AvatarSelector: Failed to create ImageCropperDialog.")
                        return
                    }
                    cropper.openWithSource(selectedFile)
                } else {
                    control.source = selectedFile
                    control.avatarChanged(selectedFile)
                }
            }
        }
    }
    
    // Crop dialog 裁剪对话框
    Component {
        id: cropperDialogComponent

        ImageCropperDialog {
            id: cropperDialog
            visible: false
            width: 0
            height: 0
            cropShape: Enums.imageCropper.shape_circle

            onAccepted: (rect) => {
                control.source = cropperDialog.source
                control.cropRect = rect
                control.avatarChanged(cropperDialog.source)
                control.cropConfirmed(cropperDialog.source, rect)
            }
        }
    }
}
