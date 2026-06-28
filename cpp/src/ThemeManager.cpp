// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - ThemeManager 实现 (1:1 镜像 Python core/theme.py)
#include "prism/ThemeManager.h"

#include <QGuiApplication>
#include <QPalette>
#include <QColor>

namespace prism {

// 全平台字体 fallback 链 (镜像 Python FONT_FAMILY)
static const char *kFontFamily =
    "Segoe UI Variable, Segoe UI, "        // Windows
    "-apple-system, PingFang SC, "          // macOS / iOS
    "Roboto, Noto Sans CJK SC, "            // Android / Linux
    "Microsoft YaHei UI, "                  // Windows 中文
    "sans-serif";                           // 通用兜底
static const char *kFontMonospace =
    "Cascadia Code, Consolas, "             // Windows
    "SF Mono, Menlo, "                      // macOS / iOS
    "Roboto Mono, "                         // Android
    "monospace";                            // 通用兜底

ThemeManager *ThemeManager::instance() {
    // Meyers 单例 (镜像 Python __new__ 单例)
    static ThemeManager *s_instance = new ThemeManager();
    return s_instance;
}

ThemeManager::ThemeManager(QObject *parent) : QObject(parent) {
    m_accentColor = QString::fromLatin1(DEFAULT_ACCENT);
    m_accentColorLight = lightenColor(m_accentColor, LIGHTEN_FACTOR);
    m_accentColorDark = darkenColor(m_accentColor, DARKEN_FACTOR);
}

// ==================== 属性读取器 ====================
QString ThemeManager::theme() const { return themeToString(m_theme); }

bool ThemeManager::isDark() const {
    if (m_theme == Theme::Auto) {
        // 检测系统主题 (镜像 Python: palette.window().lightness() < 128)
        if (auto *app = qobject_cast<QGuiApplication *>(QCoreApplication::instance())) {
            const QColor win = app->palette().window().color();
            return win.lightness() < 128;
        }
        return false;  // 检测失败默认 light
    }
    return m_theme == Theme::Dark;
}

QString ThemeManager::skin() const { return skinToString(m_skin); }
QString ThemeManager::fontFamily() const { return QString::fromUtf8(kFontFamily); }
QString ThemeManager::fontMonospace() const { return QString::fromUtf8(kFontMonospace); }
QString ThemeManager::accentColor() const { return m_accentColor; }
QString ThemeManager::accentColorLight() const { return m_accentColorLight; }
QString ThemeManager::accentColorDark() const { return m_accentColorDark; }

// ==================== 主题 ====================
void ThemeManager::setTheme(Theme theme) {
    if (m_theme != theme) {
        m_theme = theme;
        emit themeChanged(themeToString(theme));
    }
}
Theme ThemeManager::getTheme() const { return m_theme; }

void ThemeManager::toggleTheme() {
    setTheme(m_theme == Theme::Dark ? Theme::Light : Theme::Dark);
}

void ThemeManager::setThemeFromQml(const QString &themeStr) {
    setTheme(themeFromString(themeStr));
}

// ==================== 皮肤 ====================
void ThemeManager::setSkin(Skin skin) {
    if (m_skin != skin) {
        m_skin = skin;
        emit skinChanged(skinToString(skin));
    }
}
Skin ThemeManager::getSkin() const { return m_skin; }

void ThemeManager::setSkinFromQml(const QString &skinStr) {
    setSkin(skinFromString(skinStr));
}

// ==================== 主题色 ====================
void ThemeManager::setAccentColor(const QString &color) {
    // 校验 HEX 格式 (镜像 Python: 以 # 开头且长度 4/7/9)
    const int len = color.length();
    if (!color.startsWith(QLatin1Char('#')) || (len != 4 && len != 7 && len != 9)) {
        qWarning("prism::ThemeManager: 无效颜色格式 '%s', 需 HEX 如 #0078d4",
                 qUtf8Printable(color));
        return;  // C++ 侧不抛异常, 记日志后忽略 (与 Python raise 行为差异: 见文档)
    }
    if (m_accentColor != color) {
        m_accentColor = color;
        m_accentColorLight = lightenColor(color, LIGHTEN_FACTOR);
        m_accentColorDark = darkenColor(color, DARKEN_FACTOR);
        emit accentColorChanged(color);
    }
}
QString ThemeManager::getAccentColor() const { return m_accentColor; }

// ==================== 颜色工具 (镜像 Python HSL × factor) ====================
QString ThemeManager::lightenColor(const QString &hexColor, double factor) {
    QColor color(hexColor);
    float h, s, l, a;
    color.getHslF(&h, &s, &l, &a);
    l = qMin(1.0, l * factor);
    color.setHslF(h, s, l, a);
    return color.name();
}

QString ThemeManager::darkenColor(const QString &hexColor, double factor) {
    QColor color(hexColor);
    float h, s, l, a;
    color.getHslF(&h, &s, &l, &a);
    l = qMax(0.0, l * factor);
    color.setHslF(h, s, l, a);
    return color.name();
}

}  // namespace prism
