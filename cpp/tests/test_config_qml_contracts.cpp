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
        function setDpiOption(index) {
            manager.setDpiScale(manager.dpiScaleOptions[index])
        }
        function setWindowOption(index) {
            manager.setWindowType(manager.windowTypeOptions[index])
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
                            const QString &expressionSource, bool dpi,
                            QObject &bridge) {
    const QString path = QDir(rootPath).filePath(
        QStringLiteral("qml-boundary/%1/app.json").arg(suffix));
    ConfigManager config(path);
    if (dpi) config.setDpiScale(150);
    else config.setWindowType(2);
    checks.check(config.waitForPersistence(), "QML setter 后后台持久化完成");
    const bool baselineReady =
        dpi ? config.dpiScale() == 150 : config.windowType() == 2;
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
    if (dpi)
        QObject::connect(&config, &ConfigManager::dpiScaleChanged,
                         [&]() { ++propertyChanges; });
    else
        QObject::connect(&config, &ConfigManager::windowTypeChanged,
                         [&]() { ++propertyChanges; });
    QObject::connect(&config, &ConfigManager::configChanged,
                     [&]() { ++configChanges; });
    checks.check(evaluateQml(&bridge, expressionSource),
                 QStringLiteral("非法 QML 表达式执行 %1").arg(suffix));
    checks.check(readBytes(path) == baselineBytes &&
                     QFileInfo(path).lastModified() == baselineModified,
                 QStringLiteral("非法 QML 零持久化 %1").arg(suffix));
    checks.check((dpi ? config.dpiScale() : config.windowType()) ==
                     (dpi ? 150 : 2),
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
                               dpiExpressions.at(i), true, bridge);
    const QStringList windowExpressions = {
        "setWindow(true)", "setWindow(1.75)", "setWindow(String(0))",
        "setWindow([1])", "setWindow({value: 1})", "setWindow(null)",
        "setWindow(-1)", "setWindow(3)", "setWindow(NaN)",
        "setWindow(Infinity)", "setWindow(-Infinity)",
    };
    for (int i = 0; i < windowExpressions.size(); ++i)
        testRejectedExpression(checks, rootPath,
                               QStringLiteral("window-%1").arg(i),
                               windowExpressions.at(i), false, bridge);
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
    checks.check(dpiOk && dpi.toList() == dpiScaleOptions(),
                 "QML 精确读取 DPI 候选顺序");
    checks.check(windowOk && window.toList() == windowTypeOptions(),
                  "QML 精确读取 WindowType 候选顺序");
}

void testOptionRoundTrips(Checks &checks, const QString &rootPath,
                          QObject &bridge) {
    ConfigManager config(
        QDir(rootPath).filePath(QStringLiteral("qml-option-roundtrip/app.json")));
    config.setDpiScale(125);
    config.setWindowType(2);
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
}

void testAcceptedValue(Checks &checks, const QString &rootPath, int value,
                       bool dpi, QObject &bridge) {
    const QString kind = dpi ? QStringLiteral("dpi") : QStringLiteral("window");
    const QString path = QDir(rootPath).filePath(
        QStringLiteral("qml-accepted/%1-%2/app.json").arg(kind).arg(value));
    ConfigManager config(path);
    const int baseline = dpi ? (value == 100 ? 125 : 100)
                             : (value == 2 ? 0 : 2);
    if (dpi) config.setDpiScale(baseline);
    else config.setWindowType(baseline);
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
    if (dpi)
        QObject::connect(&config, &ConfigManager::dpiScaleChanged,
                         [&]() { ++propertyChanges; });
    else
        QObject::connect(&config, &ConfigManager::windowTypeChanged,
                         [&]() { ++propertyChanges; });
    QObject::connect(&config, &ConfigManager::configChanged,
                     [&]() { ++configChanges; });
    const QString expression =
        (dpi ? QStringLiteral("setDpi(%1)") : QStringLiteral("setWindow(%1)"))
            .arg(value);
    checks.check(evaluateQmlAndWait(&bridge, config, expression),
                 QStringLiteral("合法 QML setter 调用 %1-%2").arg(kind).arg(value));
    const QString field = dpi ? QStringLiteral("DpiScale")
                              : QStringLiteral("WindowType");
    checks.check(config.waitForPersistence() &&
                     (dpi ? config.dpiScale() : config.windowType()) == value &&
                      readWindow(path).value(field).toInt() == value,
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
        testAcceptedValue(checks, rootPath, value, true, *bridge);
    for (int value : kValidWindowTypes)
        testAcceptedValue(checks, rootPath, value, false, *bridge);
    return checks.failures();
}

}  // namespace prism::test
