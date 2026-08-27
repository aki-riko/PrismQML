// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// ConfigManager transactional persistence regression tests. ConfigManager 事务持久化回归测试。
#include "prism/ConfigManager.h"
#include "prism/ThemeManager.h"
#include "ConfigContractTests.h"
#include "TestProcess.h"

#include <QCoreApplication>
#include <QDebug>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QTemporaryDir>

static int g_failed = 0;
#define CHECK(cond, name) do { \
    if (cond) qInfo() << "  PASS:" << name; \
    else { qCritical() << "  FAIL:" << name; ++g_failed; } \
} while (0)

using namespace prism;

static bool writeJson(const QString &path, const QJsonObject &root) {
    if (!QDir().mkpath(QFileInfo(path).absolutePath()))
        return false;
    QFile file(path);
    if (!file.open(QIODevice::WriteOnly | QIODevice::Truncate))
        return false;
    const QByteArray data = QJsonDocument(root).toJson(QJsonDocument::Compact);
    return file.write(data) == data.size();
}

static bool writeBytes(const QString &path, const QByteArray &data) {
    if (!QDir().mkpath(QFileInfo(path).absolutePath()))
        return false;
    QFile file(path);
    return file.open(QIODevice::WriteOnly | QIODevice::Truncate) &&
           file.write(data) == data.size();
}

static QJsonObject readRoot(const QString &path) {
    QFile file(path);
    if (!file.open(QIODevice::ReadOnly))
        return {};
    return QJsonDocument::fromJson(file.readAll()).object();
}

static QJsonObject readWindow(const QString &path) {
    return readRoot(path).value(QStringLiteral("Window")).toObject();
}

static QJsonObject readAppearance(const QString &path) {
    return readRoot(path).value(QStringLiteral("Appearance")).toObject();
}

static QJsonObject validWindow() {
    return {
        {QStringLiteral("LazyLoading"), false},
        {QStringLiteral("LazyAnimationType"), 9},
        {QStringLiteral("DwmShadow"), false},
        {QStringLiteral("MicaEnabled"), true},
        {QStringLiteral("DpiScale"), 150},
        {QStringLiteral("WindowType"), 2},
    };
}

static QJsonObject invalidWindow(const QString &field, const QJsonValue &value) {
    QJsonObject window = validWindow();
    window[field] = value;
    return window;
}

static QJsonObject validAppearance() {
    return {
        {QStringLiteral("Theme"), QStringLiteral("dark")},
        {QStringLiteral("Skin"), QStringLiteral("neobrutalism")},
        {QStringLiteral("Language"), QStringLiteral("en")},
        {QStringLiteral("AccentColor"), QStringLiteral("#e81123")},
    };
}

static QJsonObject invalidAppearance(const QString &field,
                                     const QJsonValue &value) {
    QJsonObject appearance = validAppearance();
    appearance[field] = value;
    return appearance;
}

static bool hasDefaults(const ConfigManager &config) {
    return config.lazyLoading() && config.dwmShadow() &&
           config.lazyAnimationType() == 7 && !config.micaEnabled() && config.dpiScale() == 0 &&
           config.windowType() == 1 && config.theme() == QStringLiteral("auto") &&
           config.skin() == QStringLiteral("fluent") &&
           config.language() == QStringLiteral("auto") &&
           config.accentColor() == QStringLiteral("#0e5a9c");
}

struct SignalCounts {
    int config = 0;
    int lazy = 0;
    int lazyAnimation = 0;
    int shadow = 0;
    int mica = 0;
    int dpi = 0;
    int window = 0;
    int theme = 0;
    int skin = 0;
    int language = 0;
    int accent = 0;
    bool committedBeforeNotify = true;

    int properties() const {
        return lazy + lazyAnimation + shadow + mica + dpi + window + theme + skin + language +
               accent;
    }
};

class EnvironmentOverride {
public:
    EnvironmentOverride(const char *name, const QByteArray &value)
        : m_name(name), m_hadValue(qEnvironmentVariableIsSet(name)),
          m_original(qgetenv(name)) {
        qputenv(name, value);
    }

    ~EnvironmentOverride() {
        if (m_hadValue)
            qputenv(m_name, m_original);
        else
            qunsetenv(m_name);
    }

private:
    const char *m_name;
    bool m_hadValue;
    QByteArray m_original;
};

static void observeSignals(ConfigManager &config, const QString &path,
                           SignalCounts &counts) {
    QObject::connect(&config, &ConfigManager::configChanged,
                     [&counts]() { ++counts.config; });
    QObject::connect(&config, &ConfigManager::lazyLoadingChanged, [&]() {
        ++counts.lazy; counts.committedBeforeNotify &=
            !config.lazyLoading() && !readWindow(path).value("LazyLoading").toBool(true);
    });
    QObject::connect(&config, &ConfigManager::lazyAnimationTypeChanged, [&]() {
        ++counts.lazyAnimation; counts.committedBeforeNotify &=
            config.lazyAnimationType() == 9 &&
            readWindow(path).value("LazyAnimationType").toInt() == 9;
    });
    QObject::connect(&config, &ConfigManager::dwmShadowChanged, [&]() {
        ++counts.shadow; counts.committedBeforeNotify &=
            !config.dwmShadow() && !readWindow(path).value("DwmShadow").toBool(true);
    });
    QObject::connect(&config, &ConfigManager::micaEnabledChanged, [&]() {
        ++counts.mica; counts.committedBeforeNotify &=
            config.micaEnabled() && readWindow(path).value("MicaEnabled").toBool();
    });
    QObject::connect(&config, &ConfigManager::dpiScaleChanged, [&]() {
        ++counts.dpi; counts.committedBeforeNotify &=
            config.dpiScale() == 150 && readWindow(path).value("DpiScale").toInt() == 150;
    });
    QObject::connect(&config, &ConfigManager::windowTypeChanged, [&]() {
        ++counts.window; counts.committedBeforeNotify &=
            config.windowType() == 2 && readWindow(path).value("WindowType").toInt() == 2;
    });
    QObject::connect(&config, &ConfigManager::themeChanged, [&]() {
        ++counts.theme; counts.committedBeforeNotify &=
            config.theme() == QStringLiteral("dark") &&
            readAppearance(path).value("Theme").toString() == QStringLiteral("dark") &&
            ThemeManager::instance()->theme() == QStringLiteral("dark");
    });
    QObject::connect(&config, &ConfigManager::skinChanged, [&]() {
        ++counts.skin; counts.committedBeforeNotify &=
            config.skin() == QStringLiteral("neobrutalism") &&
            readAppearance(path).value("Skin").toString() ==
                QStringLiteral("neobrutalism") &&
            ThemeManager::instance()->skin() == QStringLiteral("neobrutalism");
    });
    QObject::connect(&config, &ConfigManager::languageChanged, [&]() {
        ++counts.language; counts.committedBeforeNotify &=
            config.language() == QStringLiteral("en") &&
            readAppearance(path).value("Language").toString() == QStringLiteral("en");
    });
    QObject::connect(&config, &ConfigManager::accentColorChanged, [&]() {
        ++counts.accent; counts.committedBeforeNotify &=
            config.accentColor() == QStringLiteral("#e81123") &&
            readAppearance(path).value("AccentColor").toString() ==
                QStringLiteral("#e81123") &&
            ThemeManager::instance()->accentColor() == QStringLiteral("#e81123");
    });
}

static void applyAllChanges(ConfigManager &config) {
    config.setLazyLoading(false);
    config.setLazyAnimationType(9);
    config.setDwmShadow(false);
    config.setMicaEnabled(true);
    config.setDpiScale(150);
    config.setWindowType(2);
    config.setTheme(QStringLiteral("dark"));
    config.setSkin(QStringLiteral("neobrutalism"));
    config.setLanguage(QStringLiteral("en"));
    config.setAccentColor(QStringLiteral("#e81123"));
    CHECK(config.waitForPersistence(), "十个 setter 后后台持久化完成");
}

static void testPathResolution(const QTemporaryDir &directory,
                               const QString &environmentPath) {
    qInfo() << "=== 配置路径解析 ===";
    CHECK(resolveConfigFilePath() == environmentPath,
          "默认路径接受 PRISMQML_CONFIG_FILE 覆盖");
    const QString explicitPath =
        directory.filePath(QStringLiteral("explicit/app.json"));
    CHECK(resolveConfigFilePath(explicitPath) == explicitPath,
          "显式配置路径优先于环境变量");
}

static void testValidLoad(const QTemporaryDir &directory) {
    const QString path = directory.filePath(QStringLiteral("valid/app.json"));
    CHECK(writeJson(path, {
              {QStringLiteral("Window"), validWindow()},
              {QStringLiteral("Appearance"), validAppearance()},
          }),
          "写入合法配置夹具");
    ConfigManager config(path);
    CHECK(!config.lazyLoading() && config.lazyAnimationType() == 9 &&
              !config.dwmShadow() && config.micaEnabled() &&
              config.dpiScale() == 150 && config.windowType() == 2 &&
              config.theme() == QStringLiteral("dark") &&
              config.skin() == QStringLiteral("neobrutalism") &&
              config.language() == QStringLiteral("en") &&
              config.accentColor() == QStringLiteral("#e81123"),
          "合法配置一次性加载窗口与外观全部字段");
    CHECK(ThemeManager::instance()->theme() == QStringLiteral("dark") &&
              ThemeManager::instance()->skin() == QStringLiteral("neobrutalism") &&
              ThemeManager::instance()->accentColor() == QStringLiteral("#e81123"),
          "C++ 宿主加载后恢复外观运行时状态");
}

static void testLegacyWindowLoad(const QTemporaryDir &directory) {
    const QString path =
        directory.filePath(QStringLiteral("legacy-window-only/app.json"));
    CHECK(writeJson(path, {{QStringLiteral("Window"), validWindow()}}),
          "写入旧版仅 Window 配置夹具");
    ConfigManager config(path);
    CHECK(!config.lazyLoading() && !config.dwmShadow() && config.micaEnabled() &&
              config.dpiScale() == 150 && config.windowType() == 2 &&
              config.theme() == QStringLiteral("auto") &&
              config.skin() == QStringLiteral("fluent") &&
              config.language() == QStringLiteral("auto") &&
              config.accentColor() == QStringLiteral("#0e5a9c"),
          "旧版 Window 配置兼容加载并补齐外观默认值");
}

static void testRejectedLoad(const QString &path, const QJsonObject &window,
                             const char *fixtureName, const char *resultName) {
    CHECK(writeJson(path, {{QStringLiteral("Window"), window}}), fixtureName);
    ConfigManager config(path);
    CHECK(hasDefaults(config), resultName);
}

static void testRawRejectedLoad(const QString &path, const QByteArray &data,
                                const char *name) {
    CHECK(writeBytes(path, data), "写入结构错误真实 JSON");
    ConfigManager config(path);
    CHECK(hasDefaults(config), name);
}

static void testRejectedAppearanceLoad(const QString &path,
                                       const QJsonObject &appearance,
                                       const char *fixtureName,
                                       const char *resultName) {
    CHECK(writeJson(path, {
              {QStringLiteral("Window"), validWindow()},
              {QStringLiteral("Appearance"), appearance},
          }), fixtureName);
    ConfigManager config(path);
    CHECK(hasDefaults(config), resultName);
}

static void testInvalidFieldLoads(const QTemporaryDir &directory) {
    testRejectedLoad(directory.filePath(QStringLiteral("invalid-choice/app.json")),
                     invalidWindow(QStringLiteral("DpiScale"), 999),
                     "写入非法 DPI 真实 JSON",
                     "非法 DPI 使整份加载回退默认状态");
    testRejectedLoad(directory.filePath(QStringLiteral("invalid-lazy-animation/app.json")),
                     invalidWindow(QStringLiteral("LazyAnimationType"), 8),
                     "写入非法懒加载动画类型真实 JSON",
                     "非法懒加载动画类型使整份加载回退默认状态");
    testRejectedLoad(directory.filePath(QStringLiteral("invalid-type/app.json")),
                     invalidWindow(QStringLiteral("DpiScale"), QStringLiteral("150")),
                     "写入类型错误真实 JSON",
                     "字段类型错误不留下部分加载状态");
    testRejectedLoad(directory.filePath(QStringLiteral("invalid-bool/app.json")),
                     invalidWindow(QStringLiteral("LazyLoading"),
                                   QStringLiteral("false")),
                     "写入布尔类型错误真实 JSON",
                     "布尔字段类型错误不留下部分加载状态");
    testRejectedLoad(directory.filePath(QStringLiteral("invalid-window/app.json")),
                     invalidWindow(QStringLiteral("WindowType"), 99),
                     "写入非法窗口类型真实 JSON",
                     "非法窗口类型使整份加载回退默认状态");
    testRejectedLoad(directory.filePath(QStringLiteral("missing-window-type/app.json")),
                     invalidWindow(QStringLiteral("WindowType"), 3),
                     "写入不存在的窗口类型 3",
                     "WindowType=3 使整份加载回退默认状态");
    testRejectedLoad(directory.filePath(QStringLiteral("bool-dpi/app.json")),
                     invalidWindow(QStringLiteral("DpiScale"), true),
                     "写入 bool DPI 真实 JSON",
                     "bool DPI 使整份加载回退默认状态");
    testRejectedLoad(directory.filePath(QStringLiteral("array-dpi/app.json")),
                     invalidWindow(QStringLiteral("DpiScale"), QJsonArray{150}),
                     "写入容器 DPI 真实 JSON",
                     "容器 DPI 使整份加载回退默认状态");
    testRejectedLoad(directory.filePath(QStringLiteral("fractional-dpi/app.json")),
                     invalidWindow(QStringLiteral("DpiScale"), 150.5),
                     "写入小数 DPI 真实 JSON",
                     "小数 DPI 使整份加载回退默认状态");
    testRawRejectedLoad(
        directory.filePath(QStringLiteral("integral-float-dpi/app.json")),
        QByteArrayLiteral(
            "{\"Window\":{\"LazyLoading\":false,\"DwmShadow\":false,"
            "\"MicaEnabled\":true,\"DpiScale\":150.0,\"WindowType\":2}}"),
        "积分浮点词法 DPI 仍被严格拒绝");
    testRejectedAppearanceLoad(
        directory.filePath(QStringLiteral("invalid-theme/app.json")),
        invalidAppearance(QStringLiteral("Theme"), QStringLiteral("sepia")),
        "写入非法主题真实 JSON", "非法主题使整份加载回退默认状态");
    testRejectedAppearanceLoad(
        directory.filePath(QStringLiteral("invalid-skin/app.json")),
        invalidAppearance(QStringLiteral("Skin"), QStringLiteral("classic")),
        "写入非法皮肤真实 JSON", "非法皮肤使整份加载回退默认状态");
    testRejectedAppearanceLoad(
        directory.filePath(QStringLiteral("invalid-language/app.json")),
        invalidAppearance(QStringLiteral("Language"), QStringLiteral("xx")),
        "写入非法语言真实 JSON", "非法语言使整份加载回退默认状态");
    testRejectedAppearanceLoad(
        directory.filePath(QStringLiteral("invalid-accent/app.json")),
        invalidAppearance(QStringLiteral("AccentColor"), QStringLiteral("#zzzzzz")),
        "写入非法主题色真实 JSON", "非法主题色使整份加载回退默认状态");
    testRejectedAppearanceLoad(
        directory.filePath(QStringLiteral("invalid-theme-type/app.json")),
        invalidAppearance(QStringLiteral("Theme"), 1),
        "写入主题类型错误真实 JSON", "外观字段类型错误不留下部分加载状态");
}

static void testLoads(const QTemporaryDir &directory) {
    qInfo() << "=== 严格且全有或全无的加载 ===";
    ConfigManager missing(
        directory.filePath(QStringLiteral("missing/app.json")));
    CHECK(hasDefaults(missing), "缺失配置使用完整默认状态");
    testValidLoad(directory);
    testLegacyWindowLoad(directory);
    testInvalidFieldLoads(directory);
    testRawRejectedLoad(directory.filePath(QStringLiteral("malformed/app.json")),
                        QByteArrayLiteral("{"), "畸形 JSON 保持完整默认状态");
    testRawRejectedLoad(directory.filePath(QStringLiteral("array-root/app.json")),
                        QByteArrayLiteral("[]"), "数组根节点保持完整默认状态");
    testRawRejectedLoad(directory.filePath(QStringLiteral("window-array/app.json")),
                        QByteArrayLiteral("{\"Window\":[]}"),
                        "Window 非对象保持完整默认状态");
    testRawRejectedLoad(directory.filePath(QStringLiteral("appearance-array/app.json")),
                        QByteArrayLiteral("{\"Appearance\":[]}"),
                        "Appearance 非对象保持完整默认状态");
}

static void testSuccessfulCommit(const QTemporaryDir &directory) {
    qInfo() << "=== 成功提交后才更新内存与信号 ===";
    const QString path = directory.filePath(QStringLiteral("success/app.json"));
    ConfigManager config(path);
    SignalCounts counts;
    observeSignals(config, path, counts);
    applyAllChanges(config);
    CHECK(readWindow(path) == validWindow() &&
              readAppearance(path) == validAppearance(),
           "十个 setter 原子保存完整窗口与外观候选状态");
    CHECK(counts.config == 10 && counts.lazy == 1 && counts.lazyAnimation == 1 && counts.shadow == 1 &&
              counts.mica == 1 && counts.dpi == 1 && counts.window == 1 &&
              counts.theme == 1 && counts.skin == 1 && counts.language == 1 &&
              counts.accent == 1,
          "每个成功 setter 只发对应属性信号和 configChanged");
    CHECK(counts.committedBeforeNotify, "属性信号观察到的内存和磁盘均已提交");
    ConfigManager reloaded(path);
    CHECK(!reloaded.lazyLoading() && !reloaded.dwmShadow() &&
              reloaded.lazyAnimationType() == 9 && reloaded.micaEnabled() && reloaded.dpiScale() == 150 &&
              reloaded.windowType() == 2 &&
              reloaded.theme() == QStringLiteral("dark") &&
              reloaded.skin() == QStringLiteral("neobrutalism") &&
              reloaded.language() == QStringLiteral("en") &&
              reloaded.accentColor() == QStringLiteral("#e81123"),
          "重新构造 C++ ConfigManager 后恢复十项持久化状态");
    config.setDpiScale(999);
    config.setWindowType(3);
    config.setWindowType(99);
    config.setTheme(QStringLiteral("sepia"));
    config.setSkin(QStringLiteral("classic"));
    config.setLanguage(QStringLiteral("xx"));
    config.setAccentColor(QStringLiteral("#zzzzzz"));
    config.setMicaEnabled(true);
    CHECK(config.waitForPersistence(), "保存失败队列已结算");
    CHECK(counts.config == 10 && counts.properties() == 10,
          "非法值和相同值均不保存也不发信号");
}

static void testEphemeralAppearanceIgnoresSharedSkin(
    const QTemporaryDir &directory) {
    qInfo() << "=== 未授权外观持久化保持 Fluent 默认 ===";
    const QString path =
        directory.filePath(QStringLiteral("shared-appearance/app.json"));
    const QJsonObject root{
        {QStringLiteral("Window"), validWindow()},
        {QStringLiteral("Appearance"), QJsonObject{
            {QStringLiteral("Theme"), QStringLiteral("dark")},
            {QStringLiteral("Skin"), QStringLiteral("vintage_ticket")},
            {QStringLiteral("Language"), QStringLiteral("zh_CN")},
            {QStringLiteral("AccentColor"), QStringLiteral("#123456")},
        }},
    };
    CHECK(writeJson(path, root), "写入共享复古票据配置夹具");
    QFile baselineFile(path);
    CHECK(baselineFile.open(QIODevice::ReadOnly), "读取共享配置基线");
    const QByteArray baseline = baselineFile.readAll();
    baselineFile.close();

    ConfigManager config(path, false);
    CHECK(!config.lazyLoading() && !config.dwmShadow() &&
              config.micaEnabled() && config.dpiScale() == 150 &&
              config.windowType() == 2,
          "禁用外观持久化仍恢复 Window 配置");
    CHECK(config.theme() == QStringLiteral("auto") &&
              config.skin() == QStringLiteral("fluent") &&
              config.language() == QStringLiteral("auto") &&
              config.accentColor() == QStringLiteral("#0e5a9c") &&
              ThemeManager::instance()->skin() == QStringLiteral("fluent"),
          "共享 vintage_ticket 不覆盖 Fluent 运行时默认值");

    config.setTheme(QStringLiteral("light"));
    config.setSkin(QStringLiteral("neobrutalism"));
    config.setLanguage(QStringLiteral("en"));
    config.setAccentColor(QStringLiteral("#abcdef"));
    CHECK(!config.persistencePending() &&
              config.theme() == QStringLiteral("light") &&
              config.skin() == QStringLiteral("neobrutalism") &&
              config.language() == QStringLiteral("en") &&
              config.accentColor() == QStringLiteral("#abcdef") &&
              ThemeManager::instance()->skin() ==
                  QStringLiteral("neobrutalism"),
          "禁用策略下外观仅在当前进程切换");
    QFile unchanged(path);
    CHECK(unchanged.open(QIODevice::ReadOnly) &&
              unchanged.readAll() == baseline,
          "进程内外观切换不改写共享配置");
    unchanged.close();
    QJsonObject latestAppearance = root.value(
        QStringLiteral("Appearance")).toObject();
    latestAppearance[QStringLiteral("Skin")] = QStringLiteral("neumorphism");
    CHECK(writeJson(path, {
              {QStringLiteral("Window"), validWindow()},
              {QStringLiteral("Appearance"), latestAppearance},
          }),
          "模拟并发应用更新共享 Appearance");
    config.setMicaEnabled(false);
    CHECK(config.waitForPersistence(), "Window 修改完成后台持久化");
    CHECK(!readWindow(path).value(QStringLiteral("MicaEnabled")).toBool() &&
              readAppearance(path) == latestAppearance,
          "Window 写入保留磁盘最新未托管 Appearance");
}

static void testBlockedParent(const QTemporaryDir &directory) {
    const QString blocker = directory.filePath(QStringLiteral("parent-blocker"));
    const QByteArray blockerContent = QByteArrayLiteral("unchanged");
    QFile blockerFile(blocker);
    CHECK(blockerFile.open(QIODevice::WriteOnly), "创建普通文件父路径阻断器");
    CHECK(blockerFile.write(blockerContent) == blockerContent.size(),
          "写入父路径阻断器");
    blockerFile.close();
    const QString path = QDir(blocker).filePath(QStringLiteral("app.json"));
    ConfigManager config(path);
    SignalCounts counts;
    observeSignals(config, path, counts);
    applyAllChanges(config);
    CHECK(hasDefaults(config), "父路径为普通文件时九个 setter 均不提交");
    CHECK(counts.config == 0 && counts.properties() == 0,
          "真实保存失败不泄露任何成功信号");
    QFile unchanged(blocker);
    CHECK(unchanged.open(QIODevice::ReadOnly) && unchanged.readAll() == blockerContent,
          "保存失败不改写阻断器文件");
}

static void testDirectoryTarget(const QTemporaryDir &directory) {
    const QString target = directory.filePath(QStringLiteral("directory-target"));
    CHECK(QDir().mkpath(target), "创建目录目标阻断器");
    ConfigManager config(target);
    SignalCounts counts;
    observeSignals(config, target, counts);
    config.setMicaEnabled(true);
    CHECK(config.waitForPersistence(), "目录目标保存队列已结算");
    CHECK(!config.micaEnabled() && counts.config == 0 && counts.properties() == 0 &&
              QFileInfo(target).isDir(),
          "目标为目录时保持旧内存、零信号且目录不变");
}

static void testEmptyExplicitPath() {
    ConfigManager config(QString{});
    SignalCounts counts;
    observeSignals(config, QString(), counts);
    config.setMicaEnabled(true);
    CHECK(config.waitForPersistence(), "空路径保存队列已结算");
    CHECK(hasDefaults(config) && counts.config == 0 && counts.properties() == 0,
          "空显式路径 fail closed 且零未提交通知");
}

static void testFileSystemFailures(const QTemporaryDir &directory) {
    qInfo() << "=== 真实文件系统失败零提交 ===";
    testBlockedParent(directory);
    testDirectoryTarget(directory);
    testEmptyExplicitPath();
}

int main(int argc, char *argv[]) {
    if (!prism::test::configureNonInteractiveProcess()) return 2;
    QTemporaryDir directory(
        QDir::tempPath() + QStringLiteral("/prism-config-manager-XXXXXX"));
    CHECK(directory.isValid(), "进程唯一临时目录创建成功");
    if (!directory.isValid()) return 2;
    g_failed += prism::test::runConfigStartupContractTests(directory.path());
    QCoreApplication app(argc, argv);
    const QString environmentPath =
        directory.filePath(QStringLiteral("environment/app.json"));
    EnvironmentOverride environment(
        kConfigFilePathEnvironment, QFile::encodeName(environmentPath));
    testPathResolution(directory, environmentPath);
    testLoads(directory);
    g_failed += prism::test::runConfigParserContractTests(directory.path());
    testSuccessfulCommit(directory);
    testEphemeralAppearanceIgnoresSharedSkin(directory);
    g_failed += prism::test::runConfigQmlContractTests(directory.path());
    testFileSystemFailures(directory);
    CHECK(directory.remove(), "所有配置句柄关闭后临时目录可删除");
    qInfo() << "";
    if (g_failed == 0) qInfo() << "ALL_TESTS_PASSED";
    else qCritical() << "TESTS_FAILED:" << g_failed;
    return g_failed == 0 ? 0 : 1;
}
