// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// Auth - Authentication related enums 认证相关枚举
// Usage 用法: Enums.auth.mode_login, Enums.auth.oauth_github

QtObject {
    // ==================== Login Mode 登录模式 ====================
    readonly property int mode_login: 0      // Login mode 登录模式
    readonly property int mode_register: 1   // Register mode 注册模式
    
    // ==================== OAuth Providers OAuth提供商 ====================
    readonly property int oauth_github: 0     // GitHub
    readonly property int oauth_google: 1     // Google
    readonly property int oauth_microsoft: 2  // Microsoft
    readonly property int oauth_apple: 3      // Apple
    readonly property int oauth_facebook: 4   // Facebook
    readonly property int oauth_twitter: 5    // Twitter/X
    readonly property int oauth_discord: 6    // Discord
    readonly property int oauth_gitlab: 7     // GitLab
    readonly property int oauth_bitbucket: 8  // Bitbucket
    readonly property int oauth_linkedin: 9   // LinkedIn
    
    // ==================== OAuth Provider Names OAuth提供商名称 ====================
    readonly property var oauthNames: ({
        0: "GitHub",
        1: "Google",
        2: "Microsoft",
        3: "Apple",
        4: "Facebook",
        5: "Twitter",
        6: "Discord",
        7: "GitLab",
        8: "Bitbucket",
        9: "LinkedIn"
    })
    
    // ==================== OAuth Provider Icons OAuth提供商图标 ====================
    // Using Icon names 使用Icon图标名
    readonly property var oauthIcons: ({
        0: "branch",           // GitHub - branch icon
        1: "globe",            // Google - globe icon
        2: "window",           // Microsoft - window icon
        3: "phone",            // Apple - phone icon
        4: "people",           // Facebook - people icon
        5: "chat",             // Twitter - chat icon
        6: "headset",          // Discord - headset icon
        7: "branch_fork",      // GitLab - branch_fork icon
        8: "repo",             // Bitbucket - repo icon
        9: "person",           // LinkedIn - person icon
    })
    
    // ==================== Form Validation 表单验证 ====================
    readonly property int validation_none: 0       // No validation 无验证
    readonly property int validation_required: 1   // Required field 必填项
    readonly property int validation_email: 2      // Email format 邮箱格式
    readonly property int validation_password: 3   // Password strength 密码强度
    readonly property int validation_match: 4      // Fields must match 字段必须匹配
    
    // ==================== Password Strength 密码强度 ====================
    readonly property int strength_weak: 0         // Weak password 弱密码
    readonly property int strength_medium: 1       // Medium password 中等密码
    readonly property int strength_strong: 2       // Strong password 强密码
    readonly property int strength_very_strong: 3  // Very strong password 非常强密码
    
    // ==================== Helper Functions 辅助函数 ====================
    function getOAuthName(provider) {
        return oauthNames[provider] || "Unknown"
    }
    
    function getOAuthIcon(provider) {
        return oauthIcons[provider] || "person"
    }
}
