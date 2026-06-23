// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

pragma Singleton
import QtQuick

// Translator - Multilingual translator singleton 多语言翻译器单例
// Translations loaded from external JSON files in i18n/ directory
// 翻译数据从 i18n/ 目录的外部 JSON 文件加载
// Usage: Translator.setLanguage(Enums.lang.zh_CN) 用法
QtObject {
    id: translator
    
    // Current language (default auto - follow system) 当前语言
    property string language: "auto"
    
    // Actual resolved language 实际解析后的语言
    property string _resolvedLanguage: "en"
    
    // Translation version trigger 翻译版本触发器
    // Bind to this in components to auto-update translations 组件绑定此属性实现自动更新
    property int _v: 0
    
    // Loaded translation dictionaries cache 已加载的翻译字典缓存
    property var _cache: ({})
    
    // English fallback dictionary 英语回退字典
    property var _fallback: ({})
    
    // Current active dictionary 当前活动字典
    property var _currentDict: ({})
    
    // i18n directory path i18n目录路径
    readonly property string _i18nPath: Qt.resolvedUrl("i18n/")
    
    // Language change signal 语言变化信号
    signal languageUpdated(string lang)
    
    // Detect system language 检测系统语言
    function detectSystemLanguage() {
        var locale = Qt.locale().name  // e.g. "zh_CN", "en_US", "ja_JP"
        
        // Direct match 直接匹配
        if (_isValidLang(locale)) {
            return locale
        }
        
        // Try language code only (e.g. "zh" from "zh_CN") 尝试仅语言代码
        var langCode = locale.split("_")[0]
        
        // Language code mapping 语言代码映射
        var langMap = {
            "zh": "zh_CN",  // Chinese defaults to Simplified 中文默认简体
            "en": "en",
            "ja": "ja",
            "ko": "ko",
            "de": "de",
            "fr": "fr",
            "es": "es",
            "ru": "ru",
            "pt": "pt",
            "it": "it",
            "ar": "ar",
            "hi": "hi",
            "vi": "vi",
            "th": "th",
            "id": "id",
            "tr": "tr",
            "pl": "pl",
            "nl": "nl",
            "uk": "uk"
        }
        
        return langMap[langCode] || "en"  // Fallback to English 默认英语
    }
    
    // Check if language code is valid 检查语言代码是否有效
    function _isValidLang(code) {
        var validLangs = [
            "en", "zh_CN", "zh_TW", "ja", "ko", "de", "fr", "es",
            "ru", "pt", "it", "ar", "hi", "vi", "th", "id", "tr", "pl", "nl", "uk"
        ]
        return validLangs.indexOf(code) >= 0
    }
    
    // Load translation JSON file synchronously 同步加载翻译 JSON 文件
    // 注意：使用同步模式因为此方法在 Singleton 初始化时调用，
    // 翻译数据必须在 QML binding 生效前就绪。
    // 已知限制：大文件或慢磁盘可能短暂阻塞 UI。
    // 缓解措施：JSON 文件通常 <10KB，且有 _cache 避免重复加载。
    function _loadTranslation(langCode) {
        if (_cache[langCode]) {
            return _cache[langCode]
        }

        try {
            var xhr = new XMLHttpRequest()
            var url = _i18nPath + langCode + ".json"
            xhr.open("GET", url, false)  // synchronous — see comment above
            xhr.send()

            if (xhr.status === 200 || xhr.status === 0) {
                var dict = JSON.parse(xhr.responseText)
                _cache[langCode] = dict
                return dict
            } else {
                console.warn("Translator: Failed to load", langCode + ".json, status:", xhr.status)
                return {}
            }
        } catch (e) {
            console.warn("Translator: Cannot load", langCode + ".json:", e, "— ensure QML_XHR_ALLOW_FILE_READ=1")
            return {}
        }
    }
    
    // Set language 设置语言
    function setLanguage(lang) {
        language = lang
        
        // Resolve actual language 解析实际语言
        if (lang === "auto") {
            _resolvedLanguage = detectSystemLanguage()
        } else if (_isValidLang(lang)) {
            _resolvedLanguage = lang
        } else {
            console.warn("Translator: Unsupported language:", lang)
            _resolvedLanguage = "en"
        }
        
        // Load translation 加载翻译
        _currentDict = _loadTranslation(_resolvedLanguage)
        
        _v++  // Increment version to trigger bindings 递增版本触发绑定更新
        languageUpdated(_resolvedLanguage)
    }
    
    // Get translated text 获取翻译文本
    function tr(key) {
        return _currentDict[key] || _fallback[key] || key
    }
    
    // rtr — void(_v) 无法在调用侧 binding 中建立依赖, 不推荐
    // 推荐: text: { void(Translator._v); return Translator.tr("key") }
    function rtr(key) {
        void(_v)
        return tr(key)
    }
    
    // Initialize on startup 启动时初始化
    Component.onCompleted: {
        // 利用延时避免引擎生命周期过早在 Component.onCompleted 中发送 XMLHttpRequest
        Qt.callLater(function() {
            // Load English fallback first 先加载英语回退
            _fallback = _loadTranslation("en")
            
            // Auto-detect system language on first load 首次加载时自动检测系统语言
            if (language === "auto") {
                _resolvedLanguage = detectSystemLanguage()
                _currentDict = _loadTranslation(_resolvedLanguage)
                console.log("Translator: Auto-detected language:", _resolvedLanguage, "(System locale:", Qt.locale().name + ")")
            }
        })
    }
    
    // Supported languages list (sorted by user count) 支持的语言列表
    readonly property var supportedLanguages: [
        { code: "auto", name: "Auto (Follow System)", nativeName: "跟随系统" },
        { code: "en", name: "English", nativeName: "English" },
        { code: "zh_CN", name: "Chinese (Simplified)", nativeName: "简体中文" },
        { code: "zh_TW", name: "Chinese (Traditional)", nativeName: "繁體中文" },
        { code: "hi", name: "Hindi", nativeName: "हिन्दी" },
        { code: "es", name: "Spanish", nativeName: "Español" },
        { code: "ar", name: "Arabic", nativeName: "العربية" },
        { code: "pt", name: "Portuguese", nativeName: "Português" },
        { code: "ru", name: "Russian", nativeName: "Русский" },
        { code: "ja", name: "Japanese", nativeName: "日本語" },
        { code: "de", name: "German", nativeName: "Deutsch" },
        { code: "fr", name: "French", nativeName: "Français" },
        { code: "ko", name: "Korean", nativeName: "한국어" },
        { code: "it", name: "Italian", nativeName: "Italiano" },
        { code: "vi", name: "Vietnamese", nativeName: "Tiếng Việt" },
        { code: "th", name: "Thai", nativeName: "ไทย" },
        { code: "id", name: "Indonesian", nativeName: "Bahasa Indonesia" },
        { code: "tr", name: "Turkish", nativeName: "Türkçe" },
        { code: "pl", name: "Polish", nativeName: "Polski" },
        { code: "nl", name: "Dutch", nativeName: "Nederlands" },
        { code: "uk", name: "Ukrainian", nativeName: "Українська" }
    ]
}
