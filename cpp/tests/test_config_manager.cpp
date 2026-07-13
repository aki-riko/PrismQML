// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// ConfigManager transactional persistence regression tests. ConfigManager 事务持久化回归测试。
#include "prism/ConfigManager.h"
#include "TestProcess.h"

#include <QCoreApplication>
#include <QDebug>
#include <QDir>
#include <QFile>
#include <QFileInfo>
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

static QJsonObject readWindow(const QString &path) {
    QFile file(path);
    if (!file.open(QIODevice::ReadOnly))
        return {};
    return QJsonDocument::fromJson(file.readAll()).object()
        .value(QStringLiteral("Window")).toObject();
}

static QJsonObject validWindow() {
    return {
        {QStringLiteral("LazyLoading"), false},
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

static bool hasDefaults(const ConfigManager &config) {
    return config.lazyLoading() && config.dwmShadow() &&
           !config.micaEnabled() && config.dpiScale() == 0 &&
           config.windowType() == 1;
}

struct SignalCounts {
    int config = 0;
    int lazy = 0;
    int shadow = 0;
    int mica = 0;
    int dpi = 0;
    int window = 0;
    bool committedBeforeNotify = true;

    int properties() const { return lazy + shadow + mica + dpi + window; }
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
}

static void applyAllChanges(ConfigManager &config) {
    config.setLazyLoading(false);
    config.setDwmShadow(false);
    config.setMicaEnabled(true);
    config.setDpiScale(150);
    config.setWindowType(2);
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
    CHECK(writeJson(path, {{QStringLiteral("Window"), validWindow()}}),
          "写入合法配置夹具");
    ConfigManager config(path);
    CHECK(!config.lazyLoading() && !config.dwmShadow() && config.micaEnabled() &&
              config.dpiScale() == 150 && config.windowType() == 2,
          "合法配置一次性加载全部字段");
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

static void testInvalidFieldLoads(const QTemporaryDir &directory) {
    testRejectedLoad(directory.filePath(QStringLiteral("invalid-choice/app.json")),
                     invalidWindow(QStringLiteral("DpiScale"), 999),
                     "写入非法 DPI 真实 JSON",
                     "非法 DPI 使整份加载回退默认状态");
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
}

static void testLoads(const QTemporaryDir &directory) {
    qInfo() << "=== 严格且全有或全无的加载 ===";
    ConfigManager missing(
        directory.filePath(QStringLiteral("missing/app.json")));
    CHECK(hasDefaults(missing), "缺失配置使用完整默认状态");
    testValidLoad(directory);
    testInvalidFieldLoads(directory);
    testRawRejectedLoad(directory.filePath(QStringLiteral("malformed/app.json")),
                        QByteArrayLiteral("{"), "畸形 JSON 保持完整默认状态");
    testRawRejectedLoad(directory.filePath(QStringLiteral("array-root/app.json")),
                        QByteArrayLiteral("[]"), "数组根节点保持完整默认状态");
    testRawRejectedLoad(directory.filePath(QStringLiteral("window-array/app.json")),
                        QByteArrayLiteral("{\"Window\":[]}"),
                        "Window 非对象保持完整默认状态");
}

static void testSuccessfulCommit(const QTemporaryDir &directory) {
    qInfo() << "=== 成功提交后才更新内存与信号 ===";
    const QString path = directory.filePath(QStringLiteral("success/app.json"));
    ConfigManager config(path);
    SignalCounts counts;
    observeSignals(config, path, counts);
    applyAllChanges(config);
    CHECK(readWindow(path) == validWindow(), "五个 setter 原子保存完整候选状态");
    CHECK(counts.config == 5 && counts.lazy == 1 && counts.shadow == 1 &&
              counts.mica == 1 && counts.dpi == 1 && counts.window == 1,
          "每个成功 setter 只发对应属性信号和 configChanged");
    CHECK(counts.committedBeforeNotify, "属性信号观察到的内存和磁盘均已提交");
    config.setDpiScale(999);
    config.setWindowType(99);
    config.setMicaEnabled(true);
    CHECK(counts.config == 5 && counts.properties() == 5,
          "非法值和相同值均不保存也不发信号");
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
    CHECK(hasDefaults(config), "父路径为普通文件时五个 setter 均不提交");
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
    CHECK(!config.micaEnabled() && counts.config == 0 && counts.properties() == 0 &&
              QFileInfo(target).isDir(),
          "目标为目录时保持旧内存、零信号且目录不变");
}

static void testEmptyExplicitPath() {
    ConfigManager config(QString{});
    SignalCounts counts;
    observeSignals(config, QString(), counts);
    config.setMicaEnabled(true);
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
    QCoreApplication app(argc, argv);
    QTemporaryDir directory(
        QDir::tempPath() + QStringLiteral("/prism-config-manager-XXXXXX"));
    CHECK(directory.isValid(), "进程唯一临时目录创建成功");
    if (!directory.isValid()) return 2;
    const QString environmentPath =
        directory.filePath(QStringLiteral("environment/app.json"));
    EnvironmentOverride environment(
        kConfigFilePathEnvironment, QFile::encodeName(environmentPath));
    testPathResolution(directory, environmentPath);
    testLoads(directory);
    testSuccessfulCommit(directory);
    testFileSystemFailures(directory);
    CHECK(directory.remove(), "所有配置句柄关闭后临时目录可删除");
    qInfo() << "";
    if (g_failed == 0) qInfo() << "ALL_TESTS_PASSED";
    else qCritical() << "TESTS_FAILED:" << g_failed;
    return g_failed == 0 ? 0 : 1;
}
