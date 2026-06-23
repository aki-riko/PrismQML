// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

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
    
    // ==================== Picker Props 选择器属性 ====================
    property bool enableCrop: true  // Enable crop dialog 启用裁剪对话框
    property rect cropRect: Qt.rect(0.1, 0.1, 0.8, 0.8)  // Crop rect (normalized) 裁剪区域
    property string changeText: ""  // Change button text 更换按钮文本
    property string placeholderIcon: ""  // Placeholder icon 占位图标
    
    // ==================== Signals 信号 ====================
    signal clicked()
    signal avatarChanged(url newSource)
    signal cropConfirmed(url source, rect cropRect)
    
    // ==================== State 状态 ====================
    readonly property bool hovered: mouseArea.containsMouse

    // ==================== Public Methods 公开方法 ====================
    function setAvatar(url) {
        control.source = url
        control.avatarChanged(url)
    }

    // Open file dialog 打开文件对话框
    function openFilePicker() { fileDialog.open() }

    // ==================== Hover Overlay 悬停遮罩 ====================
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
                color: "white"
                icon: Enums.icon.camera
            }
            
            Label {
                type: Enums.label.type_caption
                anchors.horizontalCenter: parent.horizontalCenter
                text: control.changeText || "Change"
                color: "white"
            }
        }
    }
    
    // ==================== Interaction 交互 ====================
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        enabled: control.enabled
        hoverEnabled: true
        onClicked: {
            control.clicked()
            fileDialog.open()
        }
    }
    
    // ==================== File Dialog 文件对话框 ====================
    FileDialog {
        id: fileDialog
        title: Translator.tr("select_avatar")
        nameFilters: ["Image files (*.png *.jpg *.jpeg *.bmp *.gif)"]
        onAccepted: {
            if (control.enableCrop) {
                cropperDialog.openWithSource(selectedFile)
            } else {
                control.source = selectedFile
                control.avatarChanged(selectedFile)
            }
        }
    }
    
    // ==================== Crop Dialog 裁剪对话框 ====================
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
