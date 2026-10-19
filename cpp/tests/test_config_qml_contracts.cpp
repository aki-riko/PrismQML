// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// QML ConfigManager boundary regression tests. QML 配置边界回归测试。
#include "ConfigContractTests.h"

#include "prism/ConfigManager.h"

#include <QCoreApplication>
#include <QDateTime>
#include <QDebug>
#include <QDir>
#include <QEventLoop>
#include <QFile>
#include <QFileInfo>
#include <QJsonDocument>
#include <QJsonObject>
#include <QQmlComponent>
#include <QQmlContext>
#include <QQmlEngine>
#include <QQmlExpression>
#include <QStringList>
#include <QTimer>
#include <QUrl>
#include <functional>
#include <memory>

namespace prism::test {
namespace {

constexpr int kQmlLoadTimeoutMs = 5000;
constexpr char kQmlBridgeSource[] = R"(
    import QtQml
    QtObject {
        property var manager
        function setDpi(value) { manager.setDpiScale(value) }
        function setWindow(value) { manager.setWindowType(value) }
        function setStyle(value) { manager.setLazyLoadingStyle(value) }
        function setDpiOption(index) {
            manager.setDpiScale(manager.dpiScaleOptions[index])
        }
        function setWindowOption(index) {
            manager.setWindowType(manager.windowTypeOptions[index])
        }
        function setStyleOption(index) {
            manager.setLazyLoadingStyle(manager.lazyLoadingStyleOptions[index])
        }
    }
)";

class Checks {
public:
    void check(bool condition, const QString &name) {
        if (condition) {
            qInfo() << "  PASS:" << name;
        } else {
            qCritical() << "  FAIL:" << name;
            ++m_failures;
        }
    }

    int failures() const { return m_failures; }

private:
    int m_failures = 0;
};

class ManagerBinding {
public:
    ManagerBinding(QObject &bridge, ConfigManager &config) : m_bridge(bridge) {
        m_bound = m_bridge.setProperty(
            "manager", QVariant::fromValue(static_cast<QObject *>(&config)));
    }

    ~ManagerBinding() {
        m_bridge.setProperty(
            "manager", QVariant::fromValue(static_cast<QObject *>(nullptr)));
    }

    bool isBound() const { return m_bound; }

private:
    QObject &m_bridge;
    bool m_bound = false;
};

// 整数枚举字段的 QML 边界描述: 把 DpiScale / WindowType / LazyLoadingStyle
// 三个同构字段的参数收敛到一处, 保证新增字段与既有字段走完全相同的断言。
enum class BoundaryKind { Dpi, Window, Style };

struct BoundarySpec {
    BoundaryKind kind;
    const char *name;
    const char *field;
    int accepted;
    int fallback;
    const int *validValues;
    int validCount;
};

constexpr int kDpiBoundaryValues[] = {0, 100, 125, 150, 175, 200};
constexpr int kWindowBoundaryValues[] = {0, 1, 2};
constexpr int kStyleBoundaryValues[] = {0, 1};

constexpr BoundarySpec kDpiBoundary{
    BoundaryKind::Dpi, "dpi", "DpiScale", 150, 100,
    kDpiBoundaryValues, 6};
constexpr BoundarySpec kWindowBoundary{
    BoundaryKind::Window, "window", "WindowType", 2, 0,
    kWindowBoundaryValues, 3};
constexpr BoundarySpec kStyleBoundary{
    BoundaryKind::Style, "style", "LazyLoadingStyle", 1, 0,
    kStyleBoundaryValues, 2};

// 基线值可能与出厂默认相同(如 LazyLoadingStyle 默认 0), 直接 set 不会落盘。
// 先写一个不同的合法值再写基线, 保证基线真实存在且内容等于基线。
// The baseline may equal the factory default, so write a different valid value
// first and then the baseline to guarantee a persisted baseline file.
int seedValueFor(const BoundarySpec &spec, int baseline) {
    for (int i = 0; i < spec.validCount; ++i) {
        if (spec.validValues[i] != baseline) return spec.validValues[i];
    }
    return baseline;
}

int boundaryValue(const ConfigManager &config, BoundaryKind kind) {
    switch (kind) {
    case BoundaryKind::Dpi: return config.dpiScale();
    case BoundaryKind::Window: return config.windowType();
    case BoundaryKind::Style: return config.lazyLoadingStyle();
    }
    return -1;
}

void setBoundaryValue(ConfigManager &config, BoundaryKind kind, int value) {
    switch (kind) {
    case BoundaryKind::Dpi: config.setDpiScale(value); return;
    case BoundaryKind::Window: config.setWindowType(value); return;
    case BoundaryKind::Style: config.setLazyLoadingStyle(value); return;
    }
}

void connectBoundarySignal(ConfigManager &config, BoundaryKind kind,
                           const std::function<void()> &handler) {
    switch (kind) {
    case BoundaryKind::Dpi:
        QObject::connect(&config, &ConfigManager::dpiScaleChanged, handler);
        return;
    case BoundaryKind::Window:
        QObject::connect(&config, &ConfigManager::windowTypeChanged, handler);
        return;
    case BoundaryKind::Style:
        QObject::connect(&config, &ConfigManager::lazyLoadingStyleChanged,
                         handler);
        return;
    }
}

QByteArray readBytes(const QString &path) {
    QFile file(path);
    return file.open(QIODevice::ReadOnly) ? file.readAll() : QByteArray();
}

QJsonObject readWindow(const QString &path) {
    return QJsonDocument::fromJson(readBytes(path)).object()
        .value(QStringLiteral("Window")).toObject();
}

bool setSentinelModificationTime(const QString &path) {
    QFile file(path);
    return file.open(QIODevice::ReadWrite) &&
           file.setFileTime(QDateTime::fromSecsSinceEpoch(946684800, Qt::UTC),
                            QFileDevice::FileModificationTime);
}

QVariant evaluateQmlValue(QObject *bridge, const QString &source, bool &ok) {
    QQmlExpression expression(QQmlEngine::contextForObject(bridge), bridge, source);
    const QVariant result = expression.evaluate();
    ok = !expression.hasError();
    if (!ok)
        qCritical() << "QML expression failed:" << expression.error().toString();
    return result;
}

bool evaluateQml(QObject *bridge, const QString &source) {
    bool ok = false;
    evaluateQmlValue(bridge, source, ok);
    return ok;
}

bool evaluateQmlAndWait(QObject *bridge, ConfigManager &config,
                        const QString &source) {
    return evaluateQml(bridge, source) && config.waitForPersistence();
}

QObject *createQmlBridge(QQmlEngine &engine, QQmlComponent &component) {
    component.setData(QByteArray(kQmlBridgeSource),
                      QUrl(QStringLiteral("inline:cpp-config-contract.qml")));
    if (component.isLoading()) {
        QEventLoop loop;
        QObject::connect(&component, &QQmlComponent::statusChanged, &loop,
                         [&loop](QQmlComponent::Status status) {
                             if (status != QQmlComponent::Loading) loop.quit();
                         });
        QTimer::singleShot(kQmlLoadTimeoutMs, &loop, &QEventLoop::quit);
        if (component.isLoading()) loop.exec();
    }
    if (component.isReady()) return component.create(engine.rootContext());
    qCritical() << "QML bridge component status:" << component.status();
    for (const QQmlError &error : component.errors()) qCritical() << error.toString();
    return nullptr;
}

void testRejectedExpression(Checks &checks, const QString &rootPath,
                            const QString &suffix,
                            const QString &expressionSource,
                            const BoundarySpec &spec, QObject &bridge) {
    const QString path = QDir(rootPath).filePath(
        QStringLiteral("qml-boundary/%1/app.json").arg(suffix));
    ConfigManager config(path);
    setBoundaryValue(config, spec.kind, spec.accepted);
    checks.check(config.waitForPersistence(), "QML setter 后后台持久化完成");
    const bool baselineReady = boundaryValue(config, spec.kind) == spec.accepted;
    checks.check(baselineReady && !readBytes(path).isEmpty(),
                 QStringLiteral("非法 QML 基线已提交 %1").arg(suffix));
    if (!baselineReady || readBytes(path).isEmpty()) return;
    ManagerBinding binding(bridge, config);
    checks.check(binding.isBound(),
                 QStringLiteral("非法 QML manager 绑定 %1").arg(suffix));
    if (!binding.isBound()) return;
    checks.check(setSentinelModificationTime(path),
                 QStringLiteral("设置持久化探针 %1").arg(suffix));
    const QByteArray baselineBytes = readBytes(path);
    const QDateTime baselineModified = QFileInfo(path).lastModified();
    int propertyChanges = 0;
    int configChanges = 0;
    connectBoundarySignal(config, spec.kind, [&]() { ++propertyChanges; });
    QObject::connect(&config, &ConfigManager::configChanged,
                     [&]() { ++configChanges; });
    checks.check(evaluateQml(&bridge, expressionSource),
                 QStringLiteral("非法 QML 表达式执行 %1").arg(suffix));
    checks.check(readBytes(path) == baselineBytes &&
                     QFileInfo(path).lastModified() == baselineModified,
                 QStringLiteral("非法 QML 零持久化 %1").arg(suffix));
    checks.check(boundaryValue(config, spec.kind) == spec.accepted,
                 QStringLiteral("非法 QML 内存不变 %1").arg(suffix));
    checks.check(propertyChanges == 0 && configChanges == 0,
                 QStringLiteral("非法 QML 零成功信号 %1").arg(suffix));
}

void testRejectedBoundaries(Checks &checks, const QString &rootPath,
                            QObject &bridge) {
    qInfo() << "=== 真实 QML setter 原始类型边界 ===";
    const QStringList dpiExpressions = {
        "setDpi(true)", "setDpi(125.75)", "setDpi(String(100))",
        "setDpi([175])", "setDpi({value: 175})", "setDpi(null)",
        "setDpi(-1)", "setDpi(NaN)", "setDpi(Infinity)",
        "setDpi(-Infinity)",
    };
    for (int i = 0; i < dpiExpressions.size(); ++i)
        testRejectedExpression(checks, rootPath,
                               QStringLiteral("dpi-%1").arg(i),
                               dpiExpressions.at(i), kDpiBoundary, bridge);
    const QStringList windowExpressions = {
        "setWindow(true)", "setWindow(1.75)", "setWindow(String(0))",
        "setWindow([1])", "setWindow({value: 1})", "setWindow(null)",
        "setWindow(-1)", "setWindow(3)", "setWindow(NaN)",
        "setWindow(Infinity)", "setWindow(-Infinity)",
    };
    for (int i = 0; i < windowExpressions.size(); ++i)
        testRejectedExpression(checks, rootPath,
                               QStringLiteral("window-%1").arg(i),
                               windowExpressions.at(i), kWindowBoundary, bridge);
    const QStringList styleExpressions = {
        "setStyle(true)", "setStyle(1.5)", "setStyle(String(1))",
        "setStyle([1])", "setStyle({value: 1})", "setStyle(null)",
        "setStyle(-1)", "setStyle(2)", "setStyle(7)", "setStyle(NaN)",
        "setStyle(Infinity)", "setStyle(-Infinity)",
    };
    for (int i = 0; i < styleExpressions.size(); ++i)
        testRejectedExpression(checks, rootPath,
                               QStringLiteral("style-%1").arg(i),
                               styleExpressions.at(i), kStyleBoundary, bridge);
}

void testOptions(Checks &checks, const QString &rootPath, QObject &bridge) {
    ConfigManager config(
        QDir(rootPath).filePath(QStringLiteral("qml-options/app.json")));
    ManagerBinding binding(bridge, config);
    checks.check(binding.isBound(), "QML options manager 绑定成功");
    if (!binding.isBound()) return;
    bool dpiOk = false;
    const QVariant dpi = evaluateQmlValue(
        &bridge, QStringLiteral("manager.dpiScaleOptions"), dpiOk);
    bool windowOk = false;
    const QVariant window = evaluateQmlValue(
        &bridge, QStringLiteral("manager.windowTypeOptions"), windowOk);
    bool styleOk = false;
    const QVariant style = evaluateQmlValue(
        &bridge, QStringLiteral("manager.lazyLoadingStyleOptions"), styleOk);
    checks.check(dpiOk && dpi.toList() == dpiScaleOptions(),
                 "QML 精确读取 DPI 候选顺序");
    checks.check(windowOk && window.toList() == windowTypeOptions(),
                   "QML 精确读取 WindowType 候选顺序");
    checks.check(styleOk && style.toList() == lazyLoadingStyleOptions(),
                   "QML 精确读取 LazyLoadingStyle 候选顺序");
}

void testOptionRoundTrips(Checks &checks, const QString &rootPath,
                          QObject &bridge) {
    ConfigManager config(
        QDir(rootPath).filePath(QStringLiteral("qml-option-roundtrip/app.json")));
    config.setDpiScale(125);
    config.setWindowType(2);
    config.setLazyLoadingStyle(1);
    checks.check(config.waitForPersistence(), "QML 组合 setter 后后台持久化完成");
    ManagerBinding binding(bridge, config);
    checks.check(binding.isBound(), "QML 候选元素 manager 绑定成功");
    if (!binding.isBound()) return;
    for (int i = 0; i < static_cast<int>(kValidDpiScales.size()); ++i) {
        const QString expression = QStringLiteral("setDpiOption(%1)").arg(i);
        const bool invoked = evaluateQmlAndWait(&bridge, config, expression);
        checks.check(invoked && config.waitForPersistence() &&
                         config.dpiScale() == kValidDpiScales[i],
                     QStringLiteral("DPI 候选元素真实往返 %1").arg(i));
    }
    for (int i = 0; i < static_cast<int>(kValidWindowTypes.size()); ++i) {
        const QString expression = QStringLiteral("setWindowOption(%1)").arg(i);
        const bool invoked = evaluateQmlAndWait(&bridge, config, expression);
        checks.check(invoked && config.waitForPersistence() &&
                         config.windowType() == kValidWindowTypes[i],
                     QStringLiteral("WindowType 候选元素真实往返 %1").arg(i));
    }
    for (int i = 0; i < static_cast<int>(kValidLazyLoadingStyles.size()); ++i) {
        const QString expression = QStringLiteral("setStyleOption(%1)").arg(i);
        const bool invoked = evaluateQmlAndWait(&bridge, config, expression);
        checks.check(invoked && config.waitForPersistence() &&
                         config.lazyLoadingStyle() == kValidLazyLoadingStyles[i],
                     QStringLiteral("LazyLoadingStyle 候选元素真实往返 %1").arg(i));
    }
}

void testAcceptedValue(Checks &checks, const QString &rootPath, int value,
                       const BoundarySpec &spec, QObject &bridge) {
    const QString kind = QString::fromLatin1(spec.name);
    const QString path = QDir(rootPath).filePath(
        QStringLiteral("qml-accepted/%1-%2/app.json").arg(kind).arg(value));
    ConfigManager config(path);
    const int baseline = value == spec.accepted ? spec.fallback : spec.accepted;
    setBoundaryValue(config, spec.kind, seedValueFor(spec, baseline));
    setBoundaryValue(config, spec.kind, baseline);
    checks.check(config.waitForPersistence(), "QML 回滚 setter 后后台持久化完成");
    checks.check(!readBytes(path).isEmpty(),
                 QStringLiteral("合法 QML 基线已落盘 %1-%2").arg(kind).arg(value));
    ManagerBinding binding(bridge, config);
    checks.check(binding.isBound(),
                 QStringLiteral("合法 QML manager 绑定 %1-%2")
                     .arg(kind).arg(value));
    if (!binding.isBound()) return;
    int propertyChanges = 0;
    int configChanges = 0;
    connectBoundarySignal(config, spec.kind, [&]() { ++propertyChanges; });
    QObject::connect(&config, &ConfigManager::configChanged,
                     [&]() { ++configChanges; });
    const QString expression =
        QStringLiteral("set%1(%2)")
            .arg(kind.left(1).toUpper() + kind.mid(1))
            .arg(value);
    checks.check(evaluateQmlAndWait(&bridge, config, expression),
                 QStringLiteral("合法 QML setter 调用 %1-%2").arg(kind).arg(value));
    checks.check(config.waitForPersistence() &&
                     boundaryValue(config, spec.kind) == value &&
                     readWindow(path).value(QString::fromLatin1(spec.field))
                             .toInt() == value,
                 QStringLiteral("合法候选提交 %1-%2").arg(kind).arg(value));
    checks.check(config.waitForPersistence() && propertyChanges == 1 &&
                     configChanges == 1,
                 QStringLiteral("合法候选单次信号 %1-%2").arg(kind).arg(value));
    checks.check(setSentinelModificationTime(path),
                 QStringLiteral("设置同值探针 %1-%2").arg(kind).arg(value));
    const QByteArray committedBytes = readBytes(path);
    const QDateTime committedModified = QFileInfo(path).lastModified();
    checks.check(evaluateQmlAndWait(&bridge, config, expression),
                 QStringLiteral("QML 同值调用 %1-%2").arg(kind).arg(value));
    checks.check(propertyChanges == 1 && configChanges == 1 &&
                     readBytes(path) == committedBytes &&
                     QFileInfo(path).lastModified() == committedModified,
                 QStringLiteral("QML 同值零写入 %1-%2").arg(kind).arg(value));
}

}  // namespace

int runConfigQmlContractTests(const QString &rootPath) {
    Checks checks;
    QQmlEngine engine;
    QQmlComponent component(&engine);
    std::unique_ptr<QObject> bridge(createQmlBridge(engine, component));
    checks.check(bridge != nullptr, "共享 QML ConfigManager bridge 创建成功");
    if (!bridge) return checks.failures();
    testRejectedBoundaries(checks, rootPath, *bridge);
    qInfo() << "=== 真实 QML setter 合法候选 ===";
    testOptions(checks, rootPath, *bridge);
    testOptionRoundTrips(checks, rootPath, *bridge);
    for (int value : kValidDpiScales)
        testAcceptedValue(checks, rootPath, value, kDpiBoundary, *bridge);
    for (int value : kValidWindowTypes)
        testAcceptedValue(checks, rootPath, value, kWindowBoundary, *bridge);
    for (int value : kValidLazyLoadingStyles)
        testAcceptedValue(checks, rootPath, value, kStyleBoundary, *bridge);
    return checks.failures();
}

}  // namespace prism::test
