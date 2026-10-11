// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - ThemeManager (1:1 镜像 Python core/theme.py 的 QObject)
#pragma once

#include "prism/Theme.h"
#include <QObject>
#include <QString>
#include <QVariantMap>

namespace prism {

class ConfigManager;

// ThemeManager - 主题管理器(单例) 经 setContextProperty 注入 QML, 供 Enums.qml 读取
class ThemeManager : public QObject {
    Q_OBJECT

    // ==================== 主题属性 ====================
    Q_PROPERTY(QString theme READ theme NOTIFY themeChanged)
    Q_PROPERTY(bool isDark READ isDark NOTIFY themeChanged)
    // ==================== 减少动态效果属性 ====================
    Q_PROPERTY(bool reduceMotion READ reduceMotion NOTIFY reduceMotionChanged)
    // ==================== 高对比度属性 ====================
    Q_PROPERTY(bool highContrast READ highContrast NOTIFY highContrastChanged)
    // ==================== 皮肤属性 ====================
    Q_PROPERTY(QString skin READ skin NOTIFY skinChanged)
    // ==================== 字体属性 ====================
    Q_PROPERTY(QString fontFamily READ fontFamily CONSTANT)
    Q_PROPERTY(QString fontMonospace READ fontMonospace CONSTANT)
    // ==================== 主题色属性 ====================
    Q_PROPERTY(QString accentColor READ accentColor NOTIFY accentColorChanged)
    Q_PROPERTY(QString accentColorLight READ accentColorLight NOTIFY accentColorChanged)
    Q_PROPERTY(QString accentColorDark READ accentColorDark NOTIFY accentColorChanged)
    Q_PROPERTY(QVariantMap accentScale READ accentScale NOTIFY accentColorChanged)

public:
    // 默认主题色: 沉稳深蓝 (镜像 Python DEFAULT_ACCENT, 白字对比度 7.09 达 WCAG AAA)
    static constexpr const char *DEFAULT_ACCENT = "#0e5a9c";
    static constexpr double LIGHTEN_FACTOR = 1.1;   // Hover 变亮系数
    static constexpr double DARKEN_FACTOR = 0.85;   // Pressed 变暗系数

    // Reduced-motion environment input name. 减少动态效果环境变量名
    // (镜像 Python REDUCE_MOTION_ENV)。
    static constexpr const char *REDUCE_MOTION_ENV = "PRISM_REDUCE_MOTION";
    // Fallback for unset/empty/illegal input. 未设置/空值/非法值的回退结果
    // (镜像 Python _REDUCE_MOTION_DEFAULT)。
    static constexpr bool REDUCE_MOTION_DEFAULT = false;
    // High-contrast environment input name. 高对比度环境变量名。
    static constexpr const char *HIGH_CONTRAST_ENV = "PRISM_HIGH_CONTRAST";

    // 单例入口 (镜像 Python ThemeManager() / getThemeManager())
    static ThemeManager *instance();

    // Parse one explicit raw value. 解析显式原始值；非法值告警并回退默认值
    // (镜像 Python read_reduce_motion_env(raw))。
    static bool readReduceMotionEnv(const QString &raw);
    // Read PRISM_REDUCE_MOTION from the environment. 从环境变量读取
    // PRISM_REDUCE_MOTION (镜像 Python read_reduce_motion_env())。
    static bool readReduceMotionEnv();

    // Derive the WinUI-style accent scale from one accent color. 从单个强调色
    // 派生 WinUI 风格色阶 light3..dark3 (镜像 Python accent_scale_for)。
    static QVariantMap accentScaleFor(const QString &hexColor);

    // ---- 属性读取器 ----
    QString theme() const;
    bool isDark() const;
    bool reduceMotion() const;
    bool highContrast() const;
    QString skin() const;
    QString fontFamily() const;
    QString fontMonospace() const;
    QString accentColor() const;
    QString accentColorLight() const;
    QString accentColorDark() const;
    QVariantMap accentScale() const;

    // ---- C++ 侧枚举接口 ----
    void setTheme(Theme theme);
    Theme getTheme() const;
    void setSkin(Skin skin);
    Skin getSkin() const;
    void setAccentColor(const QString &color);
    QString getAccentColor() const;
    void setReduceMotion(bool enabled);
    bool getReduceMotion() const;
    void setHighContrast(bool enabled);
    bool getHighContrast() const;
    bool refreshHighContrast();

    // Subscribe Theme::Auto to the platform color scheme. 订阅平台配色方案；
    // 幂等，GUI 应用尚不存在时返回 false 并留待下次调用重试
    // (镜像 Python bind_system_theme_watch)。
    bool bindSystemThemeWatch();

public slots:
    // ---- QML 可调用 Slot (镜像 Python @Slot) ----
    void toggleTheme();
    void setThemeFromQml(const QString &themeStr);
    void setSkinFromQml(const QString &skinStr);
    void setReduceMotionFromQml(bool enabled);
    void setHighContrastFromQml(bool enabled);

signals:
    void themeChanged(const QString &theme);
    void accentColorChanged(const QString &color);
    void skinChanged(const QString &skin);
    void reduceMotionChanged(bool enabled);
    void highContrastChanged(bool enabled);

private:
    friend class ConfigManager;
    explicit ThemeManager(QObject *parent = nullptr);
    void applyTheme(Theme theme);
    void applySkin(Skin skin);
    void applyAccentColor(const QString &color);
    void applyReduceMotion(bool enabled);
    void applyHighContrast(bool enabled);
    static bool detectHighContrast();
    void onSystemColorSchemeChanged(Qt::ColorScheme scheme);
    void emitSystemThemeChanged();
    static QString lightenColor(const QString &hexColor, double factor);
    static QString darkenColor(const QString &hexColor, double factor);
    static QString shiftLightness(const QString &hexColor, double delta);

    Theme m_theme = Theme::Light;
    Skin m_skin = Skin::Fluent;
    QString m_accentColor;
    QString m_accentColorLight;
    QString m_accentColorDark;
    QVariantMap m_accentScale;
    bool m_reduceMotion = REDUCE_MOTION_DEFAULT;
    bool m_highContrast = false;
    // Lazy platform color-scheme watch state. 平台配色方案监听状态(延迟安装)
    bool m_systemColorSchemeBound = false;
    bool m_systemThemeNotifyPending = false;
};

}  // namespace prism
