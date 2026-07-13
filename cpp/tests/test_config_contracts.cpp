// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// Shared configuration contract regression tests. 共享配置合同回归测试。
#include "ConfigContractTests.h"

#include "prism/ConfigContracts.h"
#include "prism/ConfigManager.h"

#include <QByteArray>
#include <QDebug>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QList>
#include <QVariant>
#include <array>

namespace prism::test {
namespace {

constexpr std::array<const char *, 4> kDpiEnvironmentNames = {
    kQtAutoScreenScaleFactorEnvironment,
    kQtScreenScaleFactorsEnvironment,
    kQtEnableHighDpiScalingEnvironment,
    kQtScaleFactorEnvironment,
};

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

class DpiEnvironmentSnapshot {
public:
    DpiEnvironmentSnapshot() {
        for (std::size_t i = 0; i < kDpiEnvironmentNames.size(); ++i) {
            m_hadValue[i] = qEnvironmentVariableIsSet(kDpiEnvironmentNames[i]);
            m_values[i] = qgetenv(kDpiEnvironmentNames[i]);
        }
    }

    ~DpiEnvironmentSnapshot() {
        for (std::size_t i = 0; i < kDpiEnvironmentNames.size(); ++i) {
            if (m_hadValue[i])
                qputenv(kDpiEnvironmentNames[i], m_values[i]);
            else
                qunsetenv(kDpiEnvironmentNames[i]);
        }
    }

private:
    std::array<bool, kDpiEnvironmentNames.size()> m_hadValue{};
    std::array<QByteArray, kDpiEnvironmentNames.size()> m_values{};
};

struct StartupFallbackCase {
    QString name;
    QByteArray payload;
};

bool writeBytes(const QString &path, const QByteArray &payload) {
    if (!QDir().mkpath(QFileInfo(path).absolutePath())) return false;
    QFile file(path);
    return file.open(QIODevice::WriteOnly | QIODevice::Truncate) &&
           file.write(payload) == payload.size();
}

QByteArray fullWindowPayload(const QByteArray &dpiToken,
                             const QByteArray &windowTypeToken) {
    return QByteArrayLiteral(
               "{\"Window\":{\"LazyLoading\":false,\"DwmShadow\":false,"
               "\"MicaEnabled\":true,\"DpiScale\":") +
           dpiToken + QByteArrayLiteral(",\"WindowType\":") +
           windowTypeToken + QByteArrayLiteral("}}");
}

QByteArray fullWindowPayload(const QByteArray &dpiToken) {
    return fullWindowPayload(dpiToken, QByteArrayLiteral("2"));
}

void dirtyDpiEnvironment() {
    for (const char *name : kDpiEnvironmentNames) qputenv(name, "dirty");
}

bool followsSystemEnvironment() {
    return qgetenv(kQtEnableHighDpiScalingEnvironment) == "1" &&
           !qEnvironmentVariableIsSet(kQtAutoScreenScaleFactorEnvironment) &&
           !qEnvironmentVariableIsSet(kQtScreenScaleFactorsEnvironment) &&
           !qEnvironmentVariableIsSet(kQtScaleFactorEnvironment);
}

bool fixedEnvironment(const QByteArray &factor) {
    return qgetenv(kQtEnableHighDpiScalingEnvironment) == "0" &&
           qgetenv(kQtScaleFactorEnvironment) == factor &&
           !qEnvironmentVariableIsSet(kQtAutoScreenScaleFactorEnvironment) &&
           !qEnvironmentVariableIsSet(kQtScreenScaleFactorsEnvironment);
}

template <std::size_t Size>
QVariantList variantOptions(const std::array<int, Size> &values) {
    QVariantList result;
    for (int value : values) result.append(value);
    return result;
}

bool hasDefaults(const ConfigManager &config) {
    return config.lazyLoading() && config.dwmShadow() &&
           !config.micaEnabled() && config.dpiScale() == 0 &&
           config.windowType() == 1;
}

}  // namespace

int runConfigStartupContractTests(const QString &rootPath) {
    qInfo() << "=== 启动前 DPI 共享合同 ===";
    Checks checks;
    DpiEnvironmentSnapshot environmentSnapshot;
    checks.check(dpiScaleOptions() == variantOptions(kValidDpiScales),
                 "DPI options 精确镜像共享候选顺序");
    checks.check(windowTypeOptions() == variantOptions(kValidWindowTypes),
                 "WindowType options 精确镜像共享候选顺序");
    int integer = -1;
    checks.check(strictIntegerVariant(QVariant(150), integer) && integer == 150,
                 "严格 QVariant 边界接受原生 int");
    checks.check(!strictIntegerVariant(QVariant(true), integer) &&
                     !strictIntegerVariant(QVariant(150.0), integer) &&
                     !strictIntegerVariant(QVariant(QStringLiteral("150")), integer) &&
                     !strictIntegerVariant(QVariant(QVariantList{150}), integer),
                 "严格 QVariant 边界拒绝 bool/float/string/container");

    const std::array<QByteArray, 6> expectedFactors = {
        QByteArray(), QByteArrayLiteral("1.0"), QByteArrayLiteral("1.25"),
        QByteArrayLiteral("1.5"), QByteArrayLiteral("1.75"),
        QByteArrayLiteral("2.0"),
    };
    for (std::size_t i = 0; i < kValidDpiScales.size(); ++i) {
        const int scale = kValidDpiScales[i];
        const QString path = QDir(rootPath).filePath(
            QStringLiteral("startup-valid/%1/app.json").arg(scale));
        checks.check(writeBytes(path, fullWindowPayload(QByteArray::number(scale))),
                     QStringLiteral("写入合法启动配置 %1").arg(scale));
        dirtyDpiEnvironment();
        checks.check(applyDpiScaleBeforeApplication(path) == scale,
                     QStringLiteral("启动接受声明候选 %1").arg(scale));
        checks.check(scale == 0 ? followsSystemEnvironment()
                                : fixedEnvironment(expectedFactors[i]),
                     QStringLiteral("启动环境精确归一化 %1").arg(scale));
    }

    const QList<StartupFallbackCase> fallbackCases = {
        {QStringLiteral("string"), fullWindowPayload("\"150\"")},
        {QStringLiteral("array"), fullWindowPayload("[150]")},
        {QStringLiteral("object"), fullWindowPayload("{\"value\":150}")},
        {QStringLiteral("bool"), fullWindowPayload("true")},
        {QStringLiteral("integral-float"), fullWindowPayload("150.0")},
        {QStringLiteral("fractional"), fullWindowPayload("150.5")},
        {QStringLiteral("negative"), fullWindowPayload("-1")},
        {QStringLiteral("oversized"), fullWindowPayload("999")},
        {QStringLiteral("null"), fullWindowPayload("null")},
        {QStringLiteral("nan"), fullWindowPayload("NaN")},
        {QStringLiteral("infinity"), fullWindowPayload("Infinity")},
        {QStringLiteral("negative-infinity"), fullWindowPayload("-Infinity")},
        {QStringLiteral("missing-key"), QByteArrayLiteral("{\"Window\":{}}")},
        {QStringLiteral("malformed"), QByteArrayLiteral("{")},
        {QStringLiteral("array-root"), QByteArrayLiteral("[]")},
        {QStringLiteral("window-array"), QByteArrayLiteral("{\"Window\":[]}")},
        {QStringLiteral("invalid-peer"), fullWindowPayload("150", "3")},
        {QStringLiteral("invalid-bool-peer"), QByteArrayLiteral(
             "{\"Window\":{\"LazyLoading\":\"false\",\"DpiScale\":150,"
             "\"WindowType\":2}}")},
    };
    for (const StartupFallbackCase &testCase : fallbackCases) {
        const QString path = QDir(rootPath).filePath(
            QStringLiteral("startup-fallback/%1/app.json").arg(testCase.name));
        checks.check(writeBytes(path, testCase.payload),
                     QStringLiteral("写入回退夹具 %1").arg(testCase.name));
        dirtyDpiEnvironment();
        checks.check(applyDpiScaleBeforeApplication(path) == 0,
                     QStringLiteral("非法启动输入回退 %1").arg(testCase.name));
        checks.check(followsSystemEnvironment(),
                     QStringLiteral("回退环境无污染 %1").arg(testCase.name));
    }

    const QString missingPath =
        QDir(rootPath).filePath(QStringLiteral("startup-missing/app.json"));
    dirtyDpiEnvironment();
    checks.check(applyDpiScaleBeforeApplication(missingPath) == 0,
                 "缺失启动配置回退系统模式");
    checks.check(followsSystemEnvironment(), "缺失配置清除脏 Qt DPI 环境");
    return checks.failures();
}

int runConfigParserContractTests(const QString &rootPath) {
    qInfo() << "=== JSON 词法扫描合同 ===";
    Checks checks;
    const QString escapedPath =
        QDir(rootPath).filePath(QStringLiteral("parser-escaped/app.json"));
    checks.check(writeBytes(escapedPath, QByteArrayLiteral(
        "{\"\\u0057indow\":{\"LazyLoading\":false,\"DwmShadow\":false,"
        "\"MicaEnabled\":true,\"Dpi\\u0053cale\":150,"
        "\"Window\\u0054ype\":2}}")), "写入转义字段名 JSON");
    ConfigManager escaped(escapedPath);
    checks.check(!escaped.lazyLoading() && !escaped.dwmShadow() &&
                     escaped.micaEnabled() && escaped.dpiScale() == 150 &&
                     escaped.windowType() == 2,
                 "转义字段名按真实键严格加载");

    const QString duplicateValidPath =
        QDir(rootPath).filePath(QStringLiteral("parser-duplicate-valid/app.json"));
    checks.check(writeBytes(duplicateValidPath, QByteArrayLiteral(
        "{\"Window\":{\"DpiScale\":150.0,\"DpiScale\":125,"
        "\"WindowType\":2}}")), "写入最后整数重复键 JSON");
    ConfigManager duplicateValid(duplicateValidPath);
    checks.check(duplicateValid.dpiScale() == 125 &&
                     duplicateValid.windowType() == 2,
                 "重复键按最后整数词法和值加载");

    const QString duplicateInvalidPath =
        QDir(rootPath).filePath(QStringLiteral("parser-duplicate-invalid/app.json"));
    checks.check(writeBytes(duplicateInvalidPath, QByteArrayLiteral(
        "{\"Window\":{\"DpiScale\":125,\"DpiScale\":150.0,"
        "\"WindowType\":2}}")), "写入最后积分浮点重复键 JSON");
    ConfigManager duplicateInvalid(duplicateInvalidPath);
    checks.check(hasDefaults(duplicateInvalid),
                 "重复键最后为积分浮点时整份回退");

    const QString bomPath =
        QDir(rootPath).filePath(QStringLiteral("parser-bom/app.json"));
    checks.check(writeBytes(bomPath, QByteArray::fromHex("efbbbf") +
        QByteArrayLiteral("{\"Window\":{\"LazyLoading\":false}}")),
        "写入 UTF-8 BOM JSON");
    ConfigManager bom(bomPath);
    checks.check(hasDefaults(bom), "UTF-8 BOM 与 Python utf-8 合同一致地拒绝");
    return checks.failures();
}

}  // namespace prism::test
