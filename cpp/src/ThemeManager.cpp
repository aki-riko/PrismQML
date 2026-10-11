// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - ThemeManager 实现 (1:1 镜像 Python core/theme.py)
#include "prism/ThemeManager.h"
#include "prism/ConfigManager.h"

#include <QGuiApplication>
#include <QPalette>
#include <QColor>
#include <QCoreApplication>
#include <QStyleHints>
#include <QStringList>
#include <QTimer>
#include <QVariantMap>

#ifdef Q_OS_WIN
#include <windows.h>
#endif

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
    m_accentScale = accentScaleFor(m_accentColor);
    // Reduced-motion input is read once at construction. 减少动态效果输入在构造时读取一次。
    m_reduceMotion = readReduceMotionEnv();
    m_highContrast = detectHighContrast();
}

// ==================== 属性读取器 ====================
QString ThemeManager::theme() const { return themeToString(m_theme); }

bool ThemeManager::isDark() const {
    if (m_theme == Theme::Auto) {
        // AUTO follows the platform color scheme live. AUTO 实时跟随系统配色方案。
        // The watch is installed lazily because no GUI application may exist yet.
        // 监听延迟安装：此时 GUI 应用可能尚不存在 (镜像 Python isDark 内调用)。
        const_cast<ThemeManager *>(this)->bindSystemThemeWatch();
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
QVariantMap ThemeManager::accentScale() const { return m_accentScale; }
bool ThemeManager::reduceMotion() const { return m_reduceMotion; }
bool ThemeManager::highContrast() const { return m_highContrast; }

// ==================== 主题 ====================
void ThemeManager::setTheme(Theme theme) {
    ConfigManager::instance()->setTheme(themeToString(theme));
}

void ThemeManager::applyTheme(Theme theme) {
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

// ==================== 系统配色方案跟随 (镜像 Python bind_system_theme_watch) ====================
bool ThemeManager::bindSystemThemeWatch() {
    if (m_systemColorSchemeBound) return true;  // 幂等
    auto *app = qobject_cast<QGuiApplication *>(QCoreApplication::instance());
    if (!app) return false;  // GUI 应用尚不存在, 留待下次调用重试
    QStyleHints *hints = app->styleHints();
    if (!hints) return false;
    connect(hints, &QStyleHints::colorSchemeChanged,
            this, &ThemeManager::onSystemColorSchemeChanged);
    m_systemColorSchemeBound = true;
    return true;
}

void ThemeManager::onSystemColorSchemeChanged(Qt::ColorScheme scheme) {
    Q_UNUSED(scheme);
    // Re-notify only while Theme::Auto owns the dark state.
    // 仅在 AUTO 下重新通知；显式 LIGHT/DARK 不产生任何额外通知。
    if (m_theme != Theme::Auto || m_systemThemeNotifyPending) return;
    m_systemThemeNotifyPending = true;
    // The platform palette is refreshed after this signal returns, so wait one
    // event-loop turn before re-reading the effective dark state.
    // 平台调色板在本信号返回后才刷新，因此延后一个事件循环再重读有效深色状态。
    QTimer::singleShot(0, this, &ThemeManager::emitSystemThemeChanged);
}

void ThemeManager::emitSystemThemeChanged() {
    m_systemThemeNotifyPending = false;
    if (m_theme != Theme::Auto) return;
    // isDark is notified by themeChanged, so the existing binding contract is
    // reused instead of adding a second notify path.
    // isDark 以 themeChanged 作为通知信号，因此复用既有绑定契约而不新增通知路径。
    emit themeChanged(themeToString(m_theme));
}

// ==================== 减少动态效果 (镜像 Python reduceMotion) ====================
bool ThemeManager::readReduceMotionEnv(const QString &raw) {
    // Only documented truthy/falsy spellings are accepted. 仅接受文档化的真/假拼写。
    static const QStringList truthy{
        QStringLiteral("1"), QStringLiteral("true"),
        QStringLiteral("yes"), QStringLiteral("on")};
    static const QStringList falsy{
        QStringLiteral("0"), QStringLiteral("false"),
        QStringLiteral("no"), QStringLiteral("off")};
    const QString normalized = raw.trimmed().toCaseFolded();
    if (normalized.isEmpty()) return REDUCE_MOTION_DEFAULT;
    if (truthy.contains(normalized)) return true;
    if (falsy.contains(normalized)) return false;
    qWarning("prism::ThemeManager: %s 值非法: '%s', 已回退为 %d",
             REDUCE_MOTION_ENV, qUtf8Printable(raw),
             static_cast<int>(REDUCE_MOTION_DEFAULT));
    return REDUCE_MOTION_DEFAULT;
}

bool ThemeManager::readReduceMotionEnv() {
    const QByteArray raw = qgetenv(REDUCE_MOTION_ENV);
    // Unset and empty both fall back to the default.
    // 未设置与空值都回退默认值 (镜像 Python os.environ.get → None / 空串)。
    if (raw.isNull()) return REDUCE_MOTION_DEFAULT;
    return readReduceMotionEnv(QString::fromLocal8Bit(raw));
}

void ThemeManager::setReduceMotion(bool enabled) {
    applyReduceMotion(enabled);
}

void ThemeManager::setReduceMotionFromQml(bool enabled) {
    applyReduceMotion(enabled);
}

void ThemeManager::applyReduceMotion(bool enabled) {
    if (m_reduceMotion != enabled) {
        m_reduceMotion = enabled;
        emit reduceMotionChanged(enabled);
    }
}

bool ThemeManager::getReduceMotion() const { return m_reduceMotion; }

// ==================== 高对比度 (镜像 Python highContrast) ====================
bool ThemeManager::detectHighContrast() {
    const QByteArray raw = qgetenv(HIGH_CONTRAST_ENV);
    if (!raw.isNull() && !raw.trimmed().isEmpty()) {
        const QString value = QString::fromLocal8Bit(raw).trimmed().toCaseFolded();
        static const QStringList truthy{
            QStringLiteral("1"), QStringLiteral("true"),
            QStringLiteral("yes"), QStringLiteral("on")};
        static const QStringList falsy{
            QStringLiteral("0"), QStringLiteral("false"),
            QStringLiteral("no"), QStringLiteral("off")};
        if (truthy.contains(value)) return true;
        if (falsy.contains(value)) return false;
        qWarning("prism::ThemeManager: %s 值非法: '%s', 已忽略并回退平台判定",
                 HIGH_CONTRAST_ENV, qUtf8Printable(QString::fromLocal8Bit(raw)));
    }

#ifdef Q_OS_WIN
    HIGHCONTRASTW info{};
    info.cbSize = sizeof(info);
    if (SystemParametersInfoW(SPI_GETHIGHCONTRAST, sizeof(info), &info, 0)) {
        return (info.dwFlags & HCF_HIGHCONTRASTON) != 0;
    }
#endif
    return false;
}

bool ThemeManager::refreshHighContrast() {
    const bool detected = detectHighContrast();
    if (m_highContrast != detected) {
        m_highContrast = detected;
        emit highContrastChanged(detected);
    }
    return detected;
}

void ThemeManager::setHighContrast(bool enabled) {
    applyHighContrast(enabled);
}

void ThemeManager::setHighContrastFromQml(bool enabled) {
    applyHighContrast(enabled);
}

void ThemeManager::applyHighContrast(bool enabled) {
    if (m_highContrast != enabled) {
        m_highContrast = enabled;
        emit highContrastChanged(enabled);
    }
}

bool ThemeManager::getHighContrast() const { return m_highContrast; }

// ==================== 皮肤 ====================
void ThemeManager::setSkin(Skin skin) {
    ConfigManager::instance()->setSkin(skinToString(skin));
}

void ThemeManager::applySkin(Skin skin) {
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
    ConfigManager::instance()->setAccentColor(color);
}

void ThemeManager::applyAccentColor(const QString &color) {
    if (m_accentColor != color) {
        m_accentColor = color;
        m_accentColorLight = lightenColor(color, LIGHTEN_FACTOR);
        m_accentColorDark = darkenColor(color, DARKEN_FACTOR);
        m_accentScale = accentScaleFor(color);
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

// Shift one color's HSL lightness by a clamped delta. 按限幅增量调整 HSL 明度
// (镜像 Python _shift_lightness: max(0, min(1, l + delta)))。
QString ThemeManager::shiftLightness(const QString &hexColor, double delta) {
    QColor color(hexColor);
    float h, s, l, a;
    color.getHslF(&h, &s, &l, &a);
    const double shifted = qBound(0.0, static_cast<double>(l) + delta, 1.0);
    color.setHslF(h, s, static_cast<float>(shifted), a);
    return color.name();
}

// Derive the WinUI-style accent scale from one accent color. 派生强调色阶
// (镜像 Python accent_scale_for / ACCENT_SCALE_STEPS, 由浅到深)。
QVariantMap ThemeManager::accentScaleFor(const QString &hexColor) {
    static const struct {
        const char *name;
        double delta;
    } kAccentScaleSteps[] = {
        {"light3", 0.30},
        {"light2", 0.20},
        {"light1", 0.10},
        {"accent", 0.0},
        {"dark1", -0.10},
        {"dark2", -0.20},
        {"dark3", -0.30},
    };
    QVariantMap scale;
    for (const auto &step : kAccentScaleSteps) {
        scale.insert(QString::fromLatin1(step.name),
                     shiftLightness(hexColor, step.delta));
    }
    return scale;
}

}  // namespace prism
