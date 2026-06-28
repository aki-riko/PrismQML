// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - 主题枚举转换 + 全局自由函数实现 (镜像 Python theme.py 末尾全局函数)
#include "prism/Theme.h"
#include "prism/ThemeManager.h"

namespace prism {

// ==================== 枚举 <-> 字符串 (与 Python .value 对齐) ====================
QString themeToString(Theme t) {
    switch (t) {
        case Theme::Light: return QStringLiteral("light");
        case Theme::Dark:  return QStringLiteral("dark");
        case Theme::Auto:  return QStringLiteral("auto");
    }
    return QStringLiteral("light");
}

Theme themeFromString(const QString &s) {
    const QString v = s.toLower();
    if (v == QLatin1String("dark")) return Theme::Dark;
    if (v == QLatin1String("auto")) return Theme::Auto;
    return Theme::Light;  // 默认 light (镜像 Python theme_map.get(..., Theme.LIGHT))
}

QString skinToString(Skin s) {
    switch (s) {
        case Skin::Fluent:       return QStringLiteral("fluent");
        case Skin::Neobrutalism: return QStringLiteral("neobrutalism");
    }
    return QStringLiteral("fluent");
}

Skin skinFromString(const QString &s) {
    const QString v = s.toLower();
    if (v == QLatin1String("neobrutalism")) return Skin::Neobrutalism;
    return Skin::Fluent;  // 默认 fluent
}

// ==================== 全局自由函数 (转发到单例, 镜像 Python 模块级函数) ====================
void setTheme(Theme theme)              { ThemeManager::instance()->setTheme(theme); }
Theme getTheme()                        { return ThemeManager::instance()->getTheme(); }
void setSkin(Skin skin)                 { ThemeManager::instance()->setSkin(skin); }
Skin getSkin()                          { return ThemeManager::instance()->getSkin(); }
bool isDark()                           { return ThemeManager::instance()->isDark(); }
void setAccentColor(const QString &c)   { ThemeManager::instance()->setAccentColor(c); }
QString getAccentColor()                { return ThemeManager::instance()->getAccentColor(); }
QColor accentQColor()                   { return QColor(ThemeManager::instance()->getAccentColor()); }

}  // namespace prism
