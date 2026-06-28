// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - ThemeManager (1:1 镜像 Python core/theme.py 的 QObject)
#pragma once

#include "prism/Theme.h"
#include <QObject>
#include <QString>

namespace prism {

// ThemeManager - 主题管理器(单例) 经 setContextProperty 注入 QML, 供 Enums.qml 读取
class ThemeManager : public QObject {
    Q_OBJECT

    // ==================== 主题属性 ====================
    Q_PROPERTY(QString theme READ theme NOTIFY themeChanged)
    Q_PROPERTY(bool isDark READ isDark NOTIFY themeChanged)
    // ==================== 皮肤属性 ====================
    Q_PROPERTY(QString skin READ skin NOTIFY skinChanged)
    // ==================== 字体属性 ====================
    Q_PROPERTY(QString fontFamily READ fontFamily CONSTANT)
    Q_PROPERTY(QString fontMonospace READ fontMonospace CONSTANT)
    // ==================== 主题色属性 ====================
    Q_PROPERTY(QString accentColor READ accentColor NOTIFY accentColorChanged)
    Q_PROPERTY(QString accentColorLight READ accentColorLight NOTIFY accentColorChanged)
    Q_PROPERTY(QString accentColorDark READ accentColorDark NOTIFY accentColorChanged)

public:
    // 默认主题色: 沉稳深蓝 (镜像 Python DEFAULT_ACCENT, 白字对比度 7.09 达 WCAG AAA)
    static constexpr const char *DEFAULT_ACCENT = "#0e5a9c";
    static constexpr double LIGHTEN_FACTOR = 1.1;   // Hover 变亮系数
    static constexpr double DARKEN_FACTOR = 0.85;   // Pressed 变暗系数

    // 单例入口 (镜像 Python ThemeManager() / getThemeManager())
    static ThemeManager *instance();

    // ---- 属性读取器 ----
    QString theme() const;
    bool isDark() const;
    QString skin() const;
    QString fontFamily() const;
    QString fontMonospace() const;
    QString accentColor() const;
    QString accentColorLight() const;
    QString accentColorDark() const;

    // ---- C++ 侧枚举接口 ----
    void setTheme(Theme theme);
    Theme getTheme() const;
    void setSkin(Skin skin);
    Skin getSkin() const;
    void setAccentColor(const QString &color);
    QString getAccentColor() const;

public slots:
    // ---- QML 可调用 Slot (镜像 Python @Slot) ----
    void toggleTheme();
    void setThemeFromQml(const QString &themeStr);
    void setSkinFromQml(const QString &skinStr);

signals:
    void themeChanged(const QString &theme);
    void accentColorChanged(const QString &color);
    void skinChanged(const QString &skin);

private:
    explicit ThemeManager(QObject *parent = nullptr);
    static QString lightenColor(const QString &hexColor, double factor);
    static QString darkenColor(const QString &hexColor, double factor);

    Theme m_theme = Theme::Light;
    Skin m_skin = Skin::Fluent;
    QString m_accentColor;
    QString m_accentColorLight;
    QString m_accentColorDark;
};

}  // namespace prism
