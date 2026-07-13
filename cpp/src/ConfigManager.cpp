// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - ConfigManager 实现 (镜像 config_manager.py + settings_core.py)
#include "prism/ConfigManager.h"

#include <QByteArray>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QSaveFile>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonValue>
#include <QDebug>
#include <algorithm>
#include <array>
#include <cmath>
#include <limits>

namespace prism {

namespace {
constexpr char kDefaultConfigRelativePath[] = ".prismqml/app.json";
constexpr std::array<int, 6> kValidDpiScales = {0, 100, 125, 150, 175, 200};
constexpr std::array<int, 4> kValidWindowTypes = {0, 1, 2, 3};

enum class LoadStatus { Missing, Invalid, Valid };

LoadStatus readConfigBytes(const QString &path, QByteArray &data, QString &error) {
    if (path.isEmpty()) {
        error = QStringLiteral("empty configuration path");
        return LoadStatus::Invalid;
    }
    QFile file(path);
    if (!file.exists())
        return LoadStatus::Missing;
    if (!file.open(QIODevice::ReadOnly)) {
        error = file.errorString();
        return LoadStatus::Invalid;
    }
    data = file.readAll();
    if (file.error() != QFileDevice::NoError) {
        error = file.errorString();
        return LoadStatus::Invalid;
    }
    return LoadStatus::Valid;
}

LoadStatus parseRootObject(const QByteArray &data, QJsonObject &root,
                           QString &error) {
    QJsonParseError parseError{};
    const QJsonDocument document = QJsonDocument::fromJson(data, &parseError);
    if (parseError.error != QJsonParseError::NoError) {
        error = parseError.errorString();
        return LoadStatus::Invalid;
    }
    if (!document.isObject()) {
        error = QStringLiteral("root must be an object");
        return LoadStatus::Invalid;
    }
    root = document.object();
    return LoadStatus::Valid;
}

LoadStatus readRootObject(const QString &path, QJsonObject &root,
                          QString &error) {
    QByteArray data;
    const LoadStatus status = readConfigBytes(path, data, error);
    if (status != LoadStatus::Valid)
        return status;
    return parseRootObject(data, root, error);
}

LoadStatus readWindowObject(const QString &path, QJsonObject &window,
                            QString &error) {
    QJsonObject root;
    const LoadStatus status = readRootObject(path, root, error);
    if (status != LoadStatus::Valid)
        return status;
    const QJsonValue value = root.value(QStringLiteral("Window"));
    if (!value.isUndefined() && !value.isObject()) {
        error = QStringLiteral("Window must be an object");
        return LoadStatus::Invalid;
    }
    window = value.toObject();
    return LoadStatus::Valid;
}

bool writeAtomically(const QString &path, const QByteArray &payload) {
    if (path.isEmpty()) {
        qWarning() << "prism::ConfigManager 保存失败: 配置路径为空";
        return false;
    }
    const QString parentPath = QFileInfo(path).absolutePath();
    if (!QDir(parentPath).exists() && !QDir().mkpath(parentPath)) {
        qWarning() << "prism::ConfigManager 保存失败: 无法创建目录" << parentPath;
        return false;
    }
    QSaveFile file(path);
    if (!file.open(QIODevice::WriteOnly)) {
        qWarning() << "prism::ConfigManager 保存失败:" << file.errorString();
        return false;
    }
    if (file.write(payload) != payload.size()) {
        const QString error = file.errorString();
        file.cancelWriting();
        qWarning() << "prism::ConfigManager 写入失败:" << error;
        return false;
    }
    if (!file.commit()) {
        qWarning() << "prism::ConfigManager 提交失败:" << file.errorString();
        return false;
    }
    return true;
}

bool readOptionalBool(const QJsonObject &object, const QString &key, bool &target,
                      QString &invalidField) {
    const QJsonValue value = object.value(key);
    if (value.isUndefined())
        return true;
    if (!value.isBool()) {
        invalidField = key;
        return false;
    }
    target = value.toBool();
    return true;
}

template <std::size_t Size>
bool readOptionalInteger(const QJsonObject &object, const QString &key, int &target,
                         const std::array<int, Size> &validValues,
                         QString &invalidField) {
    const QJsonValue value = object.value(key);
    if (value.isUndefined())
        return true;
    const double number = value.toDouble(std::numeric_limits<double>::quiet_NaN());
    if (!value.isDouble() || !std::isfinite(number) || std::floor(number) != number ||
        number < std::numeric_limits<int>::min() ||
        number > std::numeric_limits<int>::max()) {
        invalidField = key;
        return false;
    }
    const int integer = static_cast<int>(number);
    if (std::find(validValues.begin(), validValues.end(), integer) == validValues.end()) {
        invalidField = key;
        return false;
    }
    target = integer;
    return true;
}
}  // namespace

ConfigManager *ConfigManager::instance() {
    static ConfigManager *s = new ConfigManager();
    return s;
}

QString resolveConfigFilePath(const QString &configured) {
    if (!configured.isEmpty())
        return configured;
    const QString environmentPath = qEnvironmentVariable(kConfigFilePathEnvironment);
    if (!environmentPath.isEmpty())
        return environmentPath;
    return QDir(QDir::homePath()).filePath(
        QString::fromLatin1(kDefaultConfigRelativePath));
}

ConfigManager::ConfigManager(QObject *parent)
    : ConfigManager(resolveConfigFilePath(), parent) {}

ConfigManager::ConfigManager(const QString &configFilePath, QObject *parent)
    : QObject(parent), m_configFilePath(configFilePath) {
    if (m_configFilePath.isEmpty()) {
        qWarning() << "prism::ConfigManager 拒绝空配置路径";
        return;
    }
    load();
}

// 配置路径: ~/.prismqml/app.json (镜像 Python DEFAULT_APP_CONFIG)
QString ConfigManager::configFilePath() const {
    return m_configFilePath;
}

QString ConfigManager::getConfigPath() const { return configFilePath(); }

void ConfigManager::load() {
    QJsonObject window;
    QString error;
    const LoadStatus status = readWindowObject(configFilePath(), window, error);
    if (status == LoadStatus::Missing)
        return;
    if (status == LoadStatus::Invalid) {
        qWarning() << "prism::ConfigManager 配置读取失败:" << error;
        return;
    }
    State candidate = m_state;
    QString invalidField;
    const bool valid =
        readOptionalBool(window, QStringLiteral("LazyLoading"), candidate.lazyLoading,
                         invalidField) &&
        readOptionalBool(window, QStringLiteral("DwmShadow"), candidate.dwmShadow,
                         invalidField) &&
        readOptionalBool(window, QStringLiteral("MicaEnabled"), candidate.micaEnabled,
                         invalidField) &&
        readOptionalInteger(window, QStringLiteral("DpiScale"), candidate.dpiScale,
                            kValidDpiScales, invalidField) &&
        readOptionalInteger(window, QStringLiteral("WindowType"), candidate.windowType,
                            kValidWindowTypes, invalidField);
    if (!valid) {
        qWarning() << "prism::ConfigManager 配置字段无效:" << invalidField;
        return;
    }
    m_state = candidate;
}

// 原子写入 (镜像 Python: 临时文件 + os.replace, 用 QSaveFile 等价)
bool ConfigManager::save(const State &candidate) const {
    QJsonObject win;
    win[QStringLiteral("LazyLoading")] = candidate.lazyLoading;
    win[QStringLiteral("DwmShadow")] = candidate.dwmShadow;
    win[QStringLiteral("MicaEnabled")] = candidate.micaEnabled;
    win[QStringLiteral("DpiScale")] = candidate.dpiScale;
    win[QStringLiteral("WindowType")] = candidate.windowType;
    QJsonObject root;
    root[QStringLiteral("Window")] = win;
    const QByteArray payload = QJsonDocument(root).toJson(QJsonDocument::Indented);
    return writeAtomically(configFilePath(), payload);
}

bool ConfigManager::commit(const State &candidate) {
    if (!save(candidate))
        return false;
    m_state = candidate;
    return true;
}

// ---- setters: 去重 + 落盘 + 发信号 (镜像 Python set 行为) ----
void ConfigManager::setLazyLoading(bool value) {
    if (m_state.lazyLoading == value) return;
    State candidate = m_state;
    candidate.lazyLoading = value;
    if (!commit(candidate)) return;
    emit lazyLoadingChanged();
    emit configChanged();
}
void ConfigManager::setDwmShadow(bool value) {
    if (m_state.dwmShadow == value) return;
    State candidate = m_state;
    candidate.dwmShadow = value;
    if (!commit(candidate)) return;
    emit dwmShadowChanged();
    emit configChanged();
}
void ConfigManager::setDpiScale(int value) {
    // 校验取值 (镜像 Python Validator.choice([0,100,125,150,175,200]))
    if (std::find(kValidDpiScales.begin(), kValidDpiScales.end(), value) ==
        kValidDpiScales.end()) {
        qWarning() << "prism::ConfigManager 无效 dpiScale:" << value;
        return;
    }
    if (m_state.dpiScale == value) return;
    State candidate = m_state;
    candidate.dpiScale = value;
    if (!commit(candidate)) return;
    emit dpiScaleChanged();
    emit configChanged();
}
void ConfigManager::setMicaEnabled(bool value) {
    if (m_state.micaEnabled == value) return;
    State candidate = m_state;
    candidate.micaEnabled = value;
    if (!commit(candidate)) return;
    emit micaEnabledChanged();
    emit configChanged();
}
void ConfigManager::setWindowType(int value) {
    // 校验取值 (镜像 Python Validator.choice([0,1,2,3]))
    if (std::find(kValidWindowTypes.begin(), kValidWindowTypes.end(), value) ==
        kValidWindowTypes.end()) {
        qWarning() << "prism::ConfigManager 无效 windowType:" << value;
        return;
    }
    if (m_state.windowType == value) return;
    State candidate = m_state;
    candidate.windowType = value;
    if (!commit(candidate)) return;
    emit windowTypeChanged();
    emit configChanged();
}

}  // namespace prism
