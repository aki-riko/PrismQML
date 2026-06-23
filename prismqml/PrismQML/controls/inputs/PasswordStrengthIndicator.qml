// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."
import "../data/Label"

// PasswordStrengthIndicator - Pure QtQuick implementation 密码强度指示器纯QtQuick实现
// Display password strength 显示密码强度
Item {
    id: control
    
    property string password: ""
    property int strength: calculateStrength(password)  // 0-4
    
    readonly property var strengthColors: Enums.passwordStrengthColors.palette
    readonly property var strengthTexts: ["Very Weak", "Weak", "Fair", "Strong", "Very Strong"]  // Strength texts 强度文本
    
    implicitWidth: 200
    implicitHeight: Enums.controlSize.statusBarHeight
    
    function calculateStrength(pwd) {
        if (!pwd || pwd.length === 0) return 0
        
        var score = 0
        
        // Length 长度
        if (pwd.length >= 8) score++
        if (pwd.length >= 12) score++
        
        // Contains digits 包含数字
        if (/\d/.test(pwd)) score++
        
        // Contains uppercase 包含大写字母
        if (/[A-Z]/.test(pwd)) score++
        
        // Contains special chars 包含特殊字符
        if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(pwd)) score++
        
        return Math.min(4, Math.max(0, score - 1))
    }
    
    Row {
        anchors.left: parent.left
        anchors.right: strengthLabel.left
        anchors.rightMargin: Enums.spacing.l
        anchors.verticalCenter: parent.verticalCenter
        spacing: Enums.spacing.xs
        
        Repeater {
            model: 4
            
            Rectangle {
                width: (parent.width - 12) / 4
                height: Enums.controlSize.progressBarHeight
                radius: Enums.radius.tiny
                color: index < control.strength ? strengthColors[control.strength] : (Enums.stateColor.border)
                
                Behavior on color { ColorAnimation { duration: Enums.duration.medium } }
            }
        }
    }
    
    Label {
        id: strengthLabel
        type: Enums.label.type_caption
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        text: control.password ? strengthTexts[control.strength] : ""
        color: control.password ? strengthColors[control.strength] : Enums.transparent
        
        Behavior on color { ColorAnimation { duration: Enums.duration.medium } }
    }
}
