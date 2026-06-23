// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// Lang - Language codes 语言代码
QtObject {
    // State component types 状态组件类型
    readonly property int type_no_data: 1      // 无数据（EmptyDataState）
    readonly property int type_no_internet: 2  // 无网络（OfflineState）
    
    // Language codes 语言代码
    readonly property string auto: "auto"  // Auto-detect system language 自动检测系统语言
    readonly property string en: "en"
    readonly property string zh_CN: "zh_CN"
    readonly property string zh_TW: "zh_TW"
    readonly property string hi: "hi"
    readonly property string es: "es"
    readonly property string ar: "ar"
    readonly property string pt: "pt"
    readonly property string ru: "ru"
    readonly property string ja: "ja"
    readonly property string de: "de"
    readonly property string fr: "fr"
    readonly property string ko: "ko"
    readonly property string it: "it"
    readonly property string vi: "vi"
    readonly property string th: "th"
    readonly property string id: "id"
    readonly property string tr: "tr"
    readonly property string pl: "pl"
    readonly property string nl: "nl"
    readonly property string uk: "uk"
}
