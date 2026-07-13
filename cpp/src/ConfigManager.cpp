// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - ConfigManager 实现 (镜像 config_manager.py + settings_core.py)
#include "prism/ConfigManager.h"
#include "ConfigContracts_p.h"

#include <QDir>
#include <QFileInfo>
#include <QDebug>
#include <QJsonDocument>
#include <QJsonObject>
#include <QSaveFile>

namespace prism {

namespace {
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
}  // namespace

ConfigManager *ConfigManager::instance() {
    static ConfigManager *s = new ConfigManager();
    return s;
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

QVariantList ConfigManager::dpiScaleOptions() const {
    return prism::dpiScaleOptions();
}

QVariantList ConfigManager::windowTypeOptions() const {
    return prism::windowTypeOptions();
}

void ConfigManager::load() {
    detail::WindowConfigState candidate{
        m_state.lazyLoading,
        m_state.dwmShadow,
        m_state.micaEnabled,
        m_state.dpiScale,
        m_state.windowType,
    };
    QString error;
    QString invalidField;
    const detail::ConfigLoadStatus status = detail::readWindowConfigState(
        configFilePath(), candidate, error, invalidField);
    if (status == detail::ConfigLoadStatus::Missing) return;
    if (status == detail::ConfigLoadStatus::Invalid) {
        qWarning() << "prism::ConfigManager 配置读取失败:"
                   << (invalidField.isEmpty() ? error : invalidField);
        return;
    }
    m_state = State{
        candidate.lazyLoading,
        candidate.dwmShadow,
        candidate.micaEnabled,
        candidate.dpiScale,
        candidate.windowType,
    };
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
void ConfigManager::setDpiScale(const QVariant &candidateValue) {
    int value = 0;
    if (!strictIntegerVariant(candidateValue, value) || !isValidDpiScale(value)) {
        qWarning() << "prism::ConfigManager 无效 dpiScale:" << candidateValue;
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
void ConfigManager::setWindowType(const QVariant &candidateValue) {
    int value = 0;
    if (!strictIntegerVariant(candidateValue, value) || !isValidWindowType(value)) {
        qWarning() << "prism::ConfigManager 无效 windowType:" << candidateValue;
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
