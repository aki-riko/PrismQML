// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Dialogs
import "../.."
import "../icons"
import "../buttons/Button"
import "../data/Label"

// DropZone - Drop file widget like Fluent Design 拖放文件组件
// Supports single/multiple files and folder mode 支持单文件/多文件/文件夹模式
Rectangle {
    id: control
    
    // ==================== Size Priority (manual, Rectangle can't extend Widget) ====================
    // Size Priority (manual, Rectangle can't extend Widget) 尺寸优先级（手动实现，Rectangle无法继承Widget）
    property real preferredWidth: 0
    property real preferredHeight: 0
    property real contentWidth: Enums.controlSize.toastWidth - 10  // 350
    property real contentHeight: Enums.controlSize.dropFileHeight  // 140
    implicitWidth: preferredWidth > 0 ? preferredWidth : contentWidth
    implicitHeight: preferredHeight > 0 ? preferredHeight : contentHeight
    
    // ==================== Public Props 公开属性 ====================
    property bool multiple: false  // Allow multiple files 允许多文件
    property bool folderMode: false  // Folder only mode 仅文件夹模式
    property var allowedExtensions: []  // Allowed suffixes like ["jpg", "png"] 允许的后缀（如 ["jpg", "png"]）
    property string initialDir: ""  // Initial directory 初始目录

    // Custom text 自定义文字
    property string dropText: folderMode ? Translator.tr("drop_folder_hint") :
                              (allowedExtensions.length > 0 ? Translator.tr("drop_file_hint") + " (" + allowedExtensions.join(", ").toUpperCase() + ")" : Translator.tr("drop_file_hint"))
    property string orText: Translator.tr("or") // orText 或者
    property string browseFileText: Translator.tr("browse_file")
    property string browseFolderText: Translator.tr("browse_folder")
    
    // ==================== Signals 信号 ====================
    signal fileSelected(string file)
    signal filesSelected(var files)
    signal folderSelected(string folder)
    
    // ==================== Readonly Props 只读属性 ====================
    readonly property bool hovered: mouseArea.containsMouse || browseFileBtn.hovered || browseFolderBtn.hovered
    readonly property bool dragActive: dropArea.containsDrag

    // ==================== Public Methods 公共方法 ====================
    // Clear 清除
    function clear() { /* Already implemented via signal handlers 已通过信号处理实现 */ }

    // ==================== Appearance 外观 ====================
    radius: Enums.radius.small
    color: Enums.transparent
    border.width: 0
    
    // ==================== Dashed Border 虚线边框 ====================
    Canvas {
        id: dashedBorder
        anchors.fill: parent
        
        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            ctx.setLineDash([6, 4])
            ctx.strokeStyle = dragActive ? Enums.accentColor : 
                             (hovered ? Enums.stateColor.borderStrong : Enums.stateColor.borderSubtle)
            ctx.lineWidth = 1.5
            ctx.beginPath()
            ctx.roundedRect(1, 1, width - 2, height - 2, control.radius, control.radius)
            ctx.stroke()
        }
        
        Component.onCompleted: requestPaint()
        
        Connections {
            target: control
            function onHoveredChanged() { dashedBorder.requestPaint() }
            function onDragActiveChanged() { dashedBorder.requestPaint() }
        }
    }
    
    // ==================== Content 内容 ====================
    Column {
        anchors.centerIn: parent
        spacing: Enums.spacing.xs
        
        // Drop text 拖放提示文字
        Label {
            type: Enums.label.type_body
            anchors.horizontalCenter: parent.horizontalCenter
            text: control.dropText
        }
        
        // Or text 或者文字
        Label {
            type: Enums.label.type_body
            anchors.horizontalCenter: parent.horizontalCenter
            text: control.orText
            color: Enums.textColor.secondary
        }
        
        // Browse buttons 浏览按钮区域
        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: Enums.spacing.m
            
            // Browse file button 浏览文件按钮
            ButtonCore {
                id: browseFileBtn
                text: control.browseFileText
                style: Enums.button.style_hyperlink
                visible: !control.folderMode
                onClicked: fileDialog.open()
            }
            
            // Separator 分隔符 /
            Label {
                type: Enums.label.type_body
                text: "/"
                color: Enums.textColor.tertiary
                visible: !control.folderMode
                anchors.verticalCenter: parent.verticalCenter
            }
            
            // Browse folder button 浏览文件夹按钮
            ButtonCore {
                id: browseFolderBtn
                text: control.browseFolderText
                style: Enums.button.style_hyperlink
                onClicked: folderDialog.open()
            }
        }
    }
    
    // ==================== Drop Area 拖放区域 ====================
    DropArea {
        id: dropArea
        anchors.fill: parent
        
        onDropped: (drop) => {
            if (drop.hasUrls) {
                var files = []
                for (var i = 0; i < drop.urls.length; i++) {
                    var url = drop.urls[i].toString().replace("file:///", "")
                    files.push(url)
                    if (!control.multiple && !control.folderMode) break
                }
                
                if (control.folderMode) {
                    if (files.length > 0) control.folderSelected(files[0])
                } else if (control.multiple) {
                    control.filesSelected(files)
                } else {
                    if (files.length > 0) control.fileSelected(files[0])
                }
            }
        }
    }
    
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        z: Enums.zIndex.background
    }
    
    // ==================== Dialogs 对话框 ====================
    FileDialog {
        id: fileDialog
        title: Translator.tr("select_file")
        currentFolder: control.initialDir ? "file:///" + control.initialDir : ""
        fileMode: control.multiple ? FileDialog.OpenFiles : FileDialog.OpenFile
        nameFilters: control.allowedExtensions.length > 0 ? ["支持的文件 (*." + control.allowedExtensions.join(" *.") + ")"] : []
        
        onAccepted: {
            var files = []
            for (var i = 0; i < selectedFiles.length; i++) {
                files.push(selectedFiles[i].toString().replace("file:///", ""))
            }
            if (control.multiple) {
                control.filesSelected(files)
            } else if (files.length > 0) {
                control.fileSelected(files[0])
            }
        }
    }
    
    FolderDialog {
        id: folderDialog
        title: Translator.tr("select_folder")
        currentFolder: control.initialDir ? "file:///" + control.initialDir : ""
        
        onAccepted: {
            control.folderSelected(selectedFolder.toString().replace("file:///", ""))
        }
    }
}
