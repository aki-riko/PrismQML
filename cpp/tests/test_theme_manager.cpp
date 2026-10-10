// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - ThemeManager 镜像契约测试
// Mirror contract tests for reduceMotion / accentScale / AUTO system following.
// 覆盖 reduceMotion 环境变量矩阵、accentScale 逐值一致、AUTO 实时跟随系统配色方案。
#include "prism/ConfigManager.h"
#include "prism/Theme.h"
#include "prism/ThemeManager.h"
#include "TestProcess.h"

#include <QCoreApplication>
#include <QDebug>
#include <QEventLoop>
#include <QGuiApplication>
#include <QMetaMethod>
#include <QMetaObject>
#include <QMetaProperty>
#include <QPalette>
#include <QQmlComponent>
#include <QQmlContext>
#include <QQmlEngine>
#include <QQmlError>
#include <QStringList>
#include <QStyleHints>
#include <QTimer>
#include <QVariantMap>

#include <memory>

static int g_failed = 0;
#define CHECK(cond, name) do { \
    if (cond) qInfo() << "  PASS:" << name; \
    else { qCritical() << "  FAIL:" << name; ++g_failed; } \
} while (0)

using namespace prism;

// Run exactly one event-loop turn so a deferred QTimer::singleShot(0) can fire.
// 执行恰好一个事件循环轮次，使延后的 QTimer::singleShot(0) 通知得以发出。
static void spinOneEventLoopTurn() {
    QEventLoop loop;
    QTimer::singleShot(0, &loop, &QEventLoop::quit);
    loop.exec();
}

// ==================== reduceMotion: 环境变量解析矩阵 ====================
enum class MotionGroup {
    Truthy,
    Falsy,
    TruthyVariants,
    FalsyVariants,
    Illegal,
    Empty,
};

struct MotionCase {
    MotionGroup group;
    const char *raw;
    bool expected;
};

// Single source of truth for the environment matrix. The PARITY_MOTION lines
// printed from this table are diffed against the Python probe output.
// 环境变量矩阵的唯一真源；据此打印的 PARITY_MOTION 行与 Python 探针输出逐行 diff。
static const MotionCase kMotionCases[] = {
    {MotionGroup::Truthy, "1", true},
    {MotionGroup::Truthy, "true", true},
    {MotionGroup::Truthy, "yes", true},
    {MotionGroup::Truthy, "on", true},
    {MotionGroup::Falsy, "0", false},
    {MotionGroup::Falsy, "false", false},
    {MotionGroup::Falsy, "no", false},
    {MotionGroup::Falsy, "off", false},
    {MotionGroup::TruthyVariants, " TRUE ", true},
    {MotionGroup::TruthyVariants, "\tOn\n", true},
    {MotionGroup::TruthyVariants, "Yes", true},
    {MotionGroup::TruthyVariants, "1 ", true},
    {MotionGroup::TruthyVariants, "  oN  ", true},
    {MotionGroup::FalsyVariants, " OFF ", false},
    {MotionGroup::FalsyVariants, "False", false},
    {MotionGroup::FalsyVariants, "\nno\t", false},
    {MotionGroup::FalsyVariants, "0 ", false},
    {MotionGroup::FalsyVariants, "  fAlSe  ", false},
    {MotionGroup::Illegal, "maybe", false},
    {MotionGroup::Illegal, "2", false},
    {MotionGroup::Illegal, "enable", false},
    {MotionGroup::Illegal, "truthy", false},
    {MotionGroup::Illegal, "1.0", false},
    {MotionGroup::Illegal, "0x0", false},
    {MotionGroup::Illegal, "yes!", false},
    {MotionGroup::Illegal, "-1", false},
    {MotionGroup::Illegal, "\xE6\x98\xAF", false},  // U+662F 是
    {MotionGroup::Empty, "", false},
    {MotionGroup::Empty, "   ", false},
    {MotionGroup::Empty, "\t\n", false},
};

static const char *motionGroupName(MotionGroup group) {
    switch (group) {
        case MotionGroup::Truthy: return "reduceMotion: 1/true/yes/on -> true";
        case MotionGroup::Falsy: return "reduceMotion: 0/false/no/off -> false";
        case MotionGroup::TruthyVariants: return "reduceMotion: 真值大小写与首尾空白容错";
        case MotionGroup::FalsyVariants: return "reduceMotion: 假值大小写与首尾空白容错";
        case MotionGroup::Illegal: return "reduceMotion: 非法值告警并回退 false";
        case MotionGroup::Empty: return "reduceMotion: 空值/纯空白回退 false";
    }
    return "reduceMotion: unknown group";
}

// Canonical escaping shared with the Python probe (backslash first).
// 与 Python 探针共享的规范转义（反斜杠优先）。
static QString motionDisplay(const QString &value) {
    QString escaped = value;
    escaped.replace(QLatin1Char('\\'), QLatin1String("\\\\"));
    escaped.replace(QLatin1Char('\t'), QLatin1String("\\t"));
    escaped.replace(QLatin1Char('\n'), QLatin1String("\\n"));
    escaped.replace(QLatin1Char('\r'), QLatin1String("\\r"));
    // Keep the parity channel ASCII-only so both sides stay byte-comparable
    // regardless of the console code page. 保持对比通道为纯 ASCII，使两侧在任意
    // 控制台代码页下都可按字节比较。
    QString ascii;
    ascii.reserve(escaped.size());
    for (const QChar &character : escaped) {
        const ushort code = character.unicode();
        if (code > 0x7E)
            ascii += QString::asprintf("\\u%04X", code);
        else
            ascii += character;
    }
    return QLatin1Char('"') + ascii + QLatin1Char('"');
}

static void testReduceMotionEnvMatrix() {
    int mismatches = 0;
    for (const MotionCase &item : kMotionCases) {
        const QString raw = QString::fromUtf8(item.raw);
        const bool actual = ThemeManager::readReduceMotionEnv(raw);
        if (actual != item.expected) {
            ++mismatches;
            qCritical() << "  MISMATCH raw=" << motionDisplay(raw)
                        << "actual=" << actual << "expected=" << item.expected;
        }
        qInfo().noquote() << QStringLiteral("PARITY_MOTION raw=%1 -> %2")
                                 .arg(motionDisplay(raw),
                                      actual ? QStringLiteral("true")
                                             : QStringLiteral("false"));
    }
    CHECK(mismatches == 0,
          "reduceMotion: 30 组输入与 Python read_reduce_motion_env 逐值一致");

    const MotionGroup groups[] = {
        MotionGroup::Truthy, MotionGroup::Falsy, MotionGroup::TruthyVariants,
        MotionGroup::FalsyVariants, MotionGroup::Illegal, MotionGroup::Empty};
    for (const MotionGroup group : groups) {
        bool groupOk = true;
        int count = 0;
        for (const MotionCase &item : kMotionCases) {
            if (item.group != group) continue;
            ++count;
            groupOk = groupOk
                      && (ThemeManager::readReduceMotionEnv(
                              QString::fromUtf8(item.raw))
                          == item.expected);
        }
        CHECK(groupOk && count > 0, motionGroupName(group));
    }

    CHECK(ThemeManager::REDUCE_MOTION_DEFAULT == false
              && ThemeManager::readReduceMotionEnv(QStringLiteral("1"))
                     != ThemeManager::REDUCE_MOTION_DEFAULT,
          "reduceMotion: 默认值与 Python _REDUCE_MOTION_DEFAULT 一致");
}

// ==================== reduceMotion: 环境变量决定构造初值 ====================
static void testReduceMotionEnvDrivesInitialState() {
    // ThemeManager is a lazily constructed process singleton, so the environment
    // variable must be set before the first instance() call.
    // ThemeManager 是延迟构造的进程单例，因此必须在首次 instance() 之前设置环境变量。
    qputenv(ThemeManager::REDUCE_MOTION_ENV, QByteArrayLiteral("yes"));
    ThemeManager *manager = ThemeManager::instance();
    CHECK(manager->reduceMotion(),
          "reduceMotion: PRISM_REDUCE_MOTION=yes 决定构造初值 true");
    CHECK(manager->getReduceMotion() == manager->reduceMotion(),
          "reduceMotion: getReduceMotion 与属性读取一致");
    CHECK(isReduceMotion(), "reduceMotion: 全局 isReduceMotion() 转发到单例");

    qputenv(ThemeManager::REDUCE_MOTION_ENV, QByteArrayLiteral("off"));
    CHECK(!ThemeManager::readReduceMotionEnv(),
          "reduceMotion: 环境变量 off 静态读取 false");
    qputenv(ThemeManager::REDUCE_MOTION_ENV, QByteArrayLiteral("banana"));
    CHECK(!ThemeManager::readReduceMotionEnv(),
          "reduceMotion: 环境变量非法值静态读取回退 false");
    qunsetenv(ThemeManager::REDUCE_MOTION_ENV);
    CHECK(!ThemeManager::readReduceMotionEnv(),
          "reduceMotion: 环境变量未设置静态读取 false");
}

// ==================== reduceMotion: 运行时开关与通知契约 ====================
static void testReduceMotionRuntimeSwitch() {
    ThemeManager *manager = ThemeManager::instance();
    manager->setReduceMotion(false);

    QList<bool> emissions;
    const QMetaObject::Connection connection = QObject::connect(
        manager, &ThemeManager::reduceMotionChanged,
        [&emissions](bool enabled) { emissions.append(enabled); });

    manager->setReduceMotion(true);
    CHECK(emissions == QList<bool>{true},
          "reduceMotion: 真实变化时 reduceMotionChanged 发出一次");

    manager->setReduceMotion(true);
    CHECK(emissions.size() == 1, "reduceMotion: 重复设置同值不重复通知");

    CHECK(QMetaObject::invokeMethod(manager, "setReduceMotionFromQml",
                                    Qt::DirectConnection, Q_ARG(bool, false)),
          "reduceMotion: QML 入口 setReduceMotionFromQml(bool) 可经元对象调用");
    CHECK(emissions == (QList<bool>{true, false}),
          "reduceMotion: QML 入口与 C++ setter 走同一提交路径");

    setReduceMotion(true);
    CHECK(emissions == (QList<bool>{true, false, true}),
          "reduceMotion: 全局 setReduceMotion() 转发到单例");
    manager->setReduceMotion(false);
    QObject::disconnect(connection);

    const QMetaObject *meta = manager->metaObject();
    const int index = meta->indexOfProperty("reduceMotion");
    const QMetaProperty property = index >= 0 ? meta->property(index) : QMetaProperty();
    CHECK(property.isValid() && property.typeName() == QByteArrayLiteral("bool")
              && property.notifySignal()
                     == QMetaMethod::fromSignal(&ThemeManager::reduceMotionChanged)
              && !property.isWritable(),
          "reduceMotion: Q_PROPERTY 只读且 notify=reduceMotionChanged");
}

// ==================== accentScale: 与 Python 侧逐值一致 ====================
struct ScaleCase {
    const char *input;
    const char *light3;
    const char *light2;
    const char *light1;
    const char *accent;
    const char *dark1;
    const char *dark2;
    const char *dark3;
};

// Expected values are the output of the Python implementation
// (prismqml/python/core/theme.py accent_scale_for) for the same inputs; the
// PARITY lines printed below are diffed against that probe's output.
// 期望值是 Python 实现 (theme.py accent_scale_for) 对同一输入的产出；下方 PARITY
// 行会与该探针输出逐行 diff，diff 为空才算逐值一致。
static const ScaleCase kScaleCases[] = {
    {"#0e5a9c", "#53a7f0", "#258feb", "#1275cb", "#0e5a9c", "#0a3f6d", "#06243e", "#010910"},
    {"#0078d4", "#6ec0ff", "#3baaff", "#0894ff", "#0078d4", "#005ba1", "#003e6e", "#00213b"},
    {"#107c10", "#3fe63f", "#1cd61c", "#16a916", "#107c10", "#0a4f0a", "#042204", "#000000"},
    {"#e81123", "#f89aa2", "#f46b76", "#f13b4b", "#e81123", "#b80e1c", "#890a15", "#59070d"},
    {"#f97316", "#fdcdab", "#fcaf79", "#fa9148", "#f97316", "#d65b06", "#a54604", "#733103"},
    {"#123456", "#2e81d3", "#2467aa", "#1b4e80", "#123456", "#091b2c", "#000102", "#000000"},
    {"#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#e6e6e6", "#cccccc", "#b3b3b3"},
    {"#000000", "#4d4d4d", "#333333", "#1a1a1a", "#000000", "#000000", "#000000", "#000000"},
    {"#7f7f7f", "#cccccc", "#b2b2b2", "#999999", "#7f7f7f", "#666666", "#4c4c4c", "#333333"},
    {"#ff0000", "#ff9999", "#ff6666", "#ff3333", "#ff0000", "#cc0000", "#990000", "#660000"},
    {"#00ff00", "#99ff99", "#66ff66", "#33ff33", "#00ff00", "#00cc00", "#009900", "#006600"},
    {"#0000ff", "#9999ff", "#6666ff", "#3333ff", "#0000ff", "#0000cc", "#000099", "#000066"},
    {"#abc", "#ffffff", "#eaeef2", "#cad5df", "#aabbcc", "#8aa2b9", "#6a88a6", "#536f8a"},
    {"#0e5a9cff", "#f3f8ff", "#c0d9ff", "#8dbbff", "#5a9cff", "#277dff", "#0061f3", "#004dc0"},
};
static constexpr int kScaleCaseCount =
    int(sizeof(kScaleCases) / sizeof(kScaleCases[0]));

static const QStringList &scaleKeys() {
    static const QStringList keys{QStringLiteral("light3"), QStringLiteral("light2"),
                                   QStringLiteral("light1"), QStringLiteral("accent"),
                                   QStringLiteral("dark1"), QStringLiteral("dark2"),
                                   QStringLiteral("dark3")};
    return keys;
}

static QStringList scaleValues(const QVariantMap &scale) {
    QStringList values;
    for (const QString &key : scaleKeys())
        values.append(scale.value(key).toString());
    return values;
}

static void testAccentScaleMatchesPython() {
    int mismatches = 0;
    for (int i = 0; i < kScaleCaseCount; ++i) {
        const ScaleCase &item = kScaleCases[i];
        const QString input = QString::fromLatin1(item.input);
        const QStringList expected{
            QString::fromLatin1(item.light3), QString::fromLatin1(item.light2),
            QString::fromLatin1(item.light1), QString::fromLatin1(item.accent),
            QString::fromLatin1(item.dark1), QString::fromLatin1(item.dark2),
            QString::fromLatin1(item.dark3)};
        const QStringList actual = scaleValues(ThemeManager::accentScaleFor(input));
        if (actual != expected) {
            ++mismatches;
            qCritical() << "  MISMATCH" << input << "actual=" << actual
                        << "expected=" << expected;
        }
        QStringList parts;
        for (int keyIndex = 0; keyIndex < scaleKeys().size(); ++keyIndex) {
            parts.append(scaleKeys().at(keyIndex) + QLatin1Char('=')
                         + actual.at(keyIndex));
        }
        qInfo().noquote() << QStringLiteral("PARITY input=%1 %2")
                                 .arg(input, parts.join(QLatin1Char(' ')));
    }
    CHECK(mismatches == 0,
          "accentScale: 14 组输入逐值等于 Python accent_scale_for 产出");
    CHECK(scaleKeys().size() == 7 && kScaleCaseCount == 14,
          "accentScale: 色阶键序为 light3..dark3 共 7 档");
}

// ==================== accentScale: 属性缓存与通知契约 ====================
static void testAccentScaleFollowsAccentColor() {
    ThemeManager *manager = ThemeManager::instance();
    const QString defaultAccent = QString::fromLatin1(ThemeManager::DEFAULT_ACCENT);
    manager->setAccentColor(defaultAccent);
    ConfigManager::instance()->waitForPersistence();

    CHECK(scaleValues(manager->accentScale())
              == scaleValues(ThemeManager::accentScaleFor(defaultAccent)),
          "accentScale: 属性缓存与纯函数派生结果一致 (默认强调色)");

    QList<QString> accents;
    const QMetaObject::Connection connection = QObject::connect(
        manager, &ThemeManager::accentColorChanged,
        [&accents](const QString &color) { accents.append(color); });

    manager->setAccentColor(QStringLiteral("#0078d4"));
    ConfigManager::instance()->waitForPersistence();
    CHECK(accents == QList<QString>{QStringLiteral("#0078d4")},
          "accentScale: 强调色真实变化时 accentColorChanged 发出一次");

    const QVariantMap updated = manager->accentScale();
    CHECK(updated.value(QStringLiteral("light3")).toString() == QStringLiteral("#6ec0ff")
              && updated.value(QStringLiteral("dark3")).toString() == QStringLiteral("#00213b"),
          "accentScale: 强调色变化后缓存色阶同步更新");
    CHECK(getAccentScale() == updated,
          "accentScale: 全局 getAccentScale() 转发到单例");

    manager->setAccentColor(QStringLiteral("#0078d4"));
    ConfigManager::instance()->waitForPersistence();
    CHECK(accents.size() == 1, "accentScale: 重复设置同色不重复通知");
    QObject::disconnect(connection);

    const QMetaObject *meta = manager->metaObject();
    const int index = meta->indexOfProperty("accentScale");
    const QMetaProperty property = index >= 0 ? meta->property(index) : QMetaProperty();
    CHECK(property.isValid() && property.typeName() == QByteArrayLiteral("QVariantMap")
              && property.notifySignal()
                     == QMetaMethod::fromSignal(&ThemeManager::accentColorChanged),
          "accentScale: Q_PROPERTY 类型 QVariantMap 且 notify=accentColorChanged");

    manager->setAccentColor(defaultAccent);
    ConfigManager::instance()->waitForPersistence();
}

// ==================== AUTO: 实时跟随系统配色方案 ====================
static void testAutoFollowsSystemColorScheme() {
    ThemeManager *manager = ThemeManager::instance();
    QStyleHints *hints = QGuiApplication::styleHints();
    CHECK(hints != nullptr, "AUTO: QGuiApplication::styleHints() 可用");
    if (!hints)
        return;

    manager->setTheme(Theme::Auto);
    ConfigManager::instance()->waitForPersistence();
    CHECK(manager->theme() == QStringLiteral("auto"), "AUTO: 主题已提交为 auto");

    CHECK(manager->bindSystemThemeWatch(),
          "AUTO: bindSystemThemeWatch() 在 GUI 应用存在时返回 true");
    CHECK(manager->bindSystemThemeWatch(), "AUTO: bindSystemThemeWatch() 幂等");

    int themeChangedCount = 0;
    QStringList emittedThemes;
    const QMetaObject::Connection connection = QObject::connect(
        manager, &ThemeManager::themeChanged,
        [&themeChangedCount, &emittedThemes](const QString &theme) {
            ++themeChangedCount;
            emittedThemes.append(theme);
        });

    // Probe whether the platform plugin really delivers colorSchemeChanged.
    // 探测平台插件是否真的投递 colorSchemeChanged。
    int probeCount = 0;
    const QMetaObject::Connection probe = QObject::connect(
        hints, &QStyleHints::colorSchemeChanged,
        [&probeCount](Qt::ColorScheme) { ++probeCount; });
    const Qt::ColorScheme originalScheme = hints->colorScheme();
    hints->setColorScheme(Qt::ColorScheme::Dark);
    spinOneEventLoopTurn();
    const bool platformDelivers = probeCount > 0;
    QObject::disconnect(probe);

    if (platformDelivers) {
        const bool paletteDark =
            QGuiApplication::palette().window().color().lightness() < 128;
        qInfo() << "  INFO: AUTO_REAL_SIGNAL_VERIFIED platform="
                << QGuiApplication::platformName()
                << "scheme=" << int(hints->colorScheme())
                << "paletteDark=" << paletteDark;
        CHECK(themeChangedCount == 1
                  && emittedThemes == QStringList{QStringLiteral("auto")},
              "AUTO: 真实 colorSchemeChanged 后延后一轮通知 themeChanged 一次");
        CHECK(manager->isDark() == paletteDark,
              "AUTO: isDark 与刷新后的平台调色板一致 (真实信号驱动)");
        CHECK(paletteDark,
              "AUTO: 真实 setColorScheme(Dark) 使平台调色板变深");

        themeChangedCount = 0;
        emittedThemes.clear();
        hints->setColorScheme(Qt::ColorScheme::Light);
        spinOneEventLoopTurn();
        CHECK(themeChangedCount == 1 && !manager->isDark(),
              "AUTO: 真实 setColorScheme(Light) 后 isDark 跟随为 false");
    } else {
        qInfo() << "  SKIP(platform): AUTO_REAL_SIGNAL_UNAVAILABLE platform="
                << QGuiApplication::platformName()
                << "probeCount=" << probeCount
                << "scheme=" << int(hints->colorScheme())
                << "-> 改用真实信号的元对象投递验证连接与时序";
        // Drive the very same connection through the real signal's meta-method.
        // 通过真实信号的元方法投递，验证的是同一条真实连接与同一时序。
        themeChangedCount = 0;
        emittedThemes.clear();
        QMetaObject::invokeMethod(hints, "colorSchemeChanged", Qt::DirectConnection,
                                  Q_ARG(Qt::ColorScheme, Qt::ColorScheme::Dark));
        CHECK(themeChangedCount == 0,
              "AUTO: 槽内不读取未刷新调色板, 信号返回时尚未通知");
        spinOneEventLoopTurn();
        CHECK(themeChangedCount == 1
                  && emittedThemes == QStringList{QStringLiteral("auto")},
              "AUTO: 延后一个事件循环后通知 themeChanged 一次");

        themeChangedCount = 0;
        emittedThemes.clear();
        QMetaObject::invokeMethod(hints, "colorSchemeChanged", Qt::DirectConnection,
                                  Q_ARG(Qt::ColorScheme, Qt::ColorScheme::Dark));
        QMetaObject::invokeMethod(hints, "colorSchemeChanged", Qt::DirectConnection,
                                  Q_ARG(Qt::ColorScheme, Qt::ColorScheme::Light));
        spinOneEventLoopTurn();
        CHECK(themeChangedCount == 1,
              "AUTO: 通知挂起期间的重复信号合并为一次通知");
    }

    // Explicit LIGHT/DARK must not produce any extra notification.
    // 显式 LIGHT/DARK 不得产生任何额外通知。
    for (const Theme explicitTheme : {Theme::Light, Theme::Dark}) {
        manager->setTheme(explicitTheme);
        ConfigManager::instance()->waitForPersistence();
        themeChangedCount = 0;
        emittedThemes.clear();
        QMetaObject::invokeMethod(hints, "colorSchemeChanged", Qt::DirectConnection,
                                  Q_ARG(Qt::ColorScheme, Qt::ColorScheme::Dark));
        spinOneEventLoopTurn();
        QMetaObject::invokeMethod(hints, "colorSchemeChanged", Qt::DirectConnection,
                                  Q_ARG(Qt::ColorScheme, Qt::ColorScheme::Light));
        spinOneEventLoopTurn();
        const char *explicitName =
            explicitTheme == Theme::Light
                ? "AUTO: 显式 LIGHT 下系统配色变化不产生额外通知"
                : "AUTO: 显式 DARK 下系统配色变化不产生额外通知";
        CHECK(themeChangedCount == 0, explicitName);
    }

    // A pending AUTO notify must not fire after switching to an explicit theme.
    // AUTO 下挂起通知后切到显式主题，延后回调不得再追加通知。
    manager->setTheme(Theme::Auto);
    ConfigManager::instance()->waitForPersistence();
    themeChangedCount = 0;
    emittedThemes.clear();
    QMetaObject::invokeMethod(hints, "colorSchemeChanged", Qt::DirectConnection,
                              Q_ARG(Qt::ColorScheme, Qt::ColorScheme::Dark));
    manager->setTheme(Theme::Dark);
    ConfigManager::instance()->waitForPersistence();
    spinOneEventLoopTurn();
    CHECK(themeChangedCount == 1
              && emittedThemes == QStringList{QStringLiteral("dark")},
          "AUTO: 挂起通知期间切到显式主题后延后回调不再追加通知");
    QObject::disconnect(connection);

    hints->setColorScheme(originalScheme);
    spinOneEventLoopTurn();
}

// ==================== QML 消费面: 与 Enums.qml 读取路径一致 ====================
// Enums.qml reads ThemeManager.reduceMotion / ThemeManager.accentScale directly;
// this reproduces that consumption path through a real QQmlEngine.
// Enums.qml 直接读取 ThemeManager.reduceMotion / ThemeManager.accentScale；
// 这里用真实 QQmlEngine 复现该消费路径。
static void testQmlSurfaceContract() {
    ThemeManager *manager = ThemeManager::instance();
    manager->setAccentColor(QStringLiteral("#0078d4"));
    ConfigManager::instance()->waitForPersistence();

    QQmlEngine engine;
    engine.rootContext()->setContextProperty(QStringLiteral("ThemeManager"), manager);

    QQmlComponent component(&engine);
    component.setData(R"QML(
import QtQml

QtObject {
    readonly property var scale: ThemeManager.accentScale
    readonly property bool reduced: ThemeManager.reduceMotion
    readonly property string light3: ThemeManager.accentScale.light3
    readonly property string dark3: ThemeManager.accentScale.dark3
    function setReduced(value) { ThemeManager.setReduceMotionFromQml(value) }
}
)QML", QUrl(QStringLiteral("inline:PrismThemeManagerProbe")));

    CHECK(!component.isError(), "QML: ThemeManager 消费面组件编译通过");
    if (component.isError()) {
        for (const QQmlError &error : component.errors())
            qCritical() << "  QML ERROR:" << error.toString();
        return;
    }
    if (component.status() == QQmlComponent::Loading) {
        QEventLoop loop;
        QTimer timeout;
        timeout.setSingleShot(true);
        QObject::connect(&component, &QQmlComponent::statusChanged,
                         &loop, &QEventLoop::quit);
        QObject::connect(&timeout, &QTimer::timeout, &loop, &QEventLoop::quit);
        timeout.start(10000);
        while (component.status() == QQmlComponent::Loading && timeout.isActive())
            loop.exec();
    }

    std::unique_ptr<QObject> probe(component.create());
    if (!probe) {
        qCritical() << "  QML STATUS:" << int(component.status());
        for (const QQmlError &error : component.errors())
            qCritical() << "  QML ERROR:" << error.toString();
    }
    CHECK(probe != nullptr, "QML: ThemeManager 消费面组件实例化通过");
    if (!probe)
        return;

    CHECK(probe->property("scale").toMap().size() == 7
              && probe->property("light3").toString() == QStringLiteral("#6ec0ff")
              && probe->property("dark3").toString() == QStringLiteral("#00213b"),
          "QML: accentScale 以 QVariantMap 暴露 7 档且逐值正确");
    CHECK(probe->property("reduced").toBool() == manager->reduceMotion(),
          "QML: reduceMotion 只读属性与单例一致");

    manager->setReduceMotion(false);
    CHECK(QMetaObject::invokeMethod(probe.get(), "setReduced", Qt::DirectConnection,
                                    Q_ARG(QVariant, true)),
          "QML: setReduceMotionFromQml 可从 QML 调用");
    CHECK(manager->reduceMotion(), "QML: QML 调用后运行时开关生效");
    CHECK(probe->property("reduced").toBool(),
          "QML: reduceMotion 绑定随 reduceMotionChanged 刷新");

    manager->setReduceMotion(false);
    manager->setAccentColor(QString::fromLatin1(ThemeManager::DEFAULT_ACCENT));
    ConfigManager::instance()->waitForPersistence();
}

int main(int argc, char *argv[]) {
    if (!prism::test::configureNonInteractiveProcess()) return 2;
    QGuiApplication app(argc, argv);
    qInfo() << "=== platform:" << QGuiApplication::platformName() << "===";

    qInfo() << "=== reduceMotion 环境变量矩阵 ===";
    testReduceMotionEnvMatrix();
    testReduceMotionEnvDrivesInitialState();
    testReduceMotionRuntimeSwitch();

    qInfo() << "=== accentScale 逐值一致 ===";
    testAccentScaleMatchesPython();
    testAccentScaleFollowsAccentColor();

    qInfo() << "=== QML 消费面 ===";
    testQmlSurfaceContract();

    qInfo() << "=== AUTO 实时跟随系统配色方案 ===";
    testAutoFollowsSystemColorScheme();

    qInfo() << "";
    if (g_failed == 0)
        qInfo() << "ALL_TESTS_PASSED";
    else
        qCritical() << "TESTS_FAILED:" << g_failed;
    return g_failed == 0 ? 0 : 1;
}
