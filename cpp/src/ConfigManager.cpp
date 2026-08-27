// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - ConfigManager 实现 (镜像 config_manager.py + settings_core.py)
#include "prism/ConfigManager.h"
#include "prism/ThemeManager.h"
#include "ConfigContracts_p.h"

#include <QDir>
#include <QCoreApplication>
#include <QEventLoop>
#include <QFile>
#include <QFileInfo>
#include <QDebug>
#include <QJsonDocument>
#include <QJsonObject>
#include <QSaveFile>
#include <QTimer>
#include <QtConcurrentRun>

namespace prism {

ConfigManager *ConfigManager::s_instance = nullptr;

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

bool mergeLatestAppearance(const QString &path, QByteArray &payload) {
    QFile file(path);
    if (!file.exists()) return true;
    if (!file.open(QIODevice::ReadOnly)) {
        qWarning() << "prism::ConfigManager 无法读取未托管 Appearance:"
                   << file.errorString();
        return false;
    }
    const QJsonDocument current = QJsonDocument::fromJson(file.readAll());
    QJsonDocument candidate = QJsonDocument::fromJson(payload);
    if (!current.isObject() || !candidate.isObject()) {
        qWarning() << "prism::ConfigManager 无法合并未托管 Appearance";
        return false;
    }
    const QJsonValue appearance = current.object().value(
        QStringLiteral("Appearance"));
    if (appearance.isUndefined()) return true;
    if (!appearance.isObject()) {
        qWarning() << "prism::ConfigManager 未托管 Appearance 不是对象";
        return false;
    }
    QJsonObject root = candidate.object();
    root[QStringLiteral("Appearance")] = appearance;
    payload = QJsonDocument(root).toJson(QJsonDocument::Indented);
    return true;
}
}  // namespace

ConfigManager *ConfigManager::instance() {
    if (!s_instance) {
        s_instance = new ConfigManager(
            resolveConfigFilePath(),
            !qEnvironmentVariable(kConfigFilePathEnvironment).isEmpty());
    }
    return s_instance;
}

ConfigManager *ConfigManager::initialize(const QString &configFilePath,
                                         bool persistAppearance) {
    const QString requestedPath = QFileInfo(configFilePath).absoluteFilePath();
    if (!s_instance) {
        s_instance = new ConfigManager(requestedPath, persistAppearance);
        return s_instance;
    }
    if (QFileInfo(s_instance->configFilePath()).absoluteFilePath() != requestedPath ||
        s_instance->appearancePersistenceEnabled() != persistAppearance) {
        qFatal("prism::ConfigManager initialized with conflicting application configuration");
    }
    s_instance->applyAppearanceToRuntime();
    return s_instance;
}

ConfigManager::ConfigManager(QObject *parent)
    : ConfigManager(resolveConfigFilePath(), false, parent) {}

ConfigManager::ConfigManager(const QString &configFilePath,
                             bool persistAppearance, QObject *parent)
    : QObject(parent), m_configFilePath(configFilePath),
      m_persistAppearance(persistAppearance),
      m_persistenceWriter(writeAtomically) {
    connect(&m_persistenceWatcher, &QFutureWatcher<bool>::finished,
            this, &ConfigManager::finishPersistence);
    if (m_configFilePath.isEmpty()) {
        qWarning() << "prism::ConfigManager 拒绝空配置路径";
        return;
    }
    load();
    applyAppearanceToRuntime();
}

ConfigManager::~ConfigManager() {
    if (persistencePending() && !waitForPersistence())
        qWarning() << "prism::ConfigManager 析构前持久化未完成";
    if (m_persistenceWatcher.isRunning())
        m_persistenceWatcher.waitForFinished();
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

QVariantList ConfigManager::themeOptions() const { return prism::themeOptions(); }
QVariantList ConfigManager::skinOptions() const { return prism::skinOptions(); }
QVariantList ConfigManager::languageOptions() const { return prism::languageOptions(); }

bool ConfigManager::persistencePending() const {
    return m_activeWrite.has_value() || !m_pendingUpdates.isEmpty();
}

void ConfigManager::load() {
    detail::AppConfigState candidate{
        {
            m_state.lazyLoading,
            m_state.dwmShadow,
            m_state.micaEnabled,
            m_state.dpiScale,
            m_state.windowType,
        },
        {
            m_state.theme,
            m_state.skin,
            m_state.language,
            m_state.accentColor,
        },
    };
    QString error;
    QString invalidField;
    const detail::ConfigLoadStatus status = detail::readAppConfigState(
        configFilePath(), candidate, error, invalidField);
    if (status == detail::ConfigLoadStatus::Missing) return;
    if (status == detail::ConfigLoadStatus::Invalid) {
        qWarning() << "prism::ConfigManager 配置读取失败:"
                   << (invalidField.isEmpty() ? error : invalidField);
        return;
    }
    m_state = State{
        candidate.window.lazyLoading,
        candidate.window.dwmShadow,
        candidate.window.micaEnabled,
        candidate.window.dpiScale,
        candidate.window.windowType,
        m_persistAppearance ? candidate.appearance.theme : m_state.theme,
        m_persistAppearance ? candidate.appearance.skin : m_state.skin,
        m_persistAppearance ? candidate.appearance.language : m_state.language,
        m_persistAppearance ? candidate.appearance.accentColor : m_state.accentColor,
    };
}

QByteArray ConfigManager::serialize(const State &candidate,
                                    bool persistAppearance) {
    QJsonObject win;
    win[QStringLiteral("LazyLoading")] = candidate.lazyLoading;
    win[QStringLiteral("DwmShadow")] = candidate.dwmShadow;
    win[QStringLiteral("MicaEnabled")] = candidate.micaEnabled;
    win[QStringLiteral("DpiScale")] = candidate.dpiScale;
    win[QStringLiteral("WindowType")] = candidate.windowType;
    QJsonObject root;
    root[QStringLiteral("Window")] = win;
    if (persistAppearance) {
        QJsonObject appearance;
        appearance[QStringLiteral("Theme")] = candidate.theme;
        appearance[QStringLiteral("Skin")] = candidate.skin;
        appearance[QStringLiteral("Language")] = candidate.language;
        appearance[QStringLiteral("AccentColor")] = candidate.accentColor;
        root[QStringLiteral("Appearance")] = appearance;
    }
    return QJsonDocument(root).toJson(QJsonDocument::Indented);
}

void ConfigManager::applyAppearanceToRuntime() const {
    if (!QCoreApplication::instance()) return;
    auto *manager = ThemeManager::instance();
    manager->applyTheme(themeFromString(m_state.theme));
    manager->applySkin(skinFromString(m_state.skin));
    manager->applyAccentColor(m_state.accentColor);
}

bool ConfigManager::applyUpdate(State &candidate, const PendingUpdate &update) {
    switch (update.field) {
    case Field::LazyLoading: {
        const bool value = update.value.toBool();
        if (candidate.lazyLoading == value) return false;
        candidate.lazyLoading = value;
        return true;
    }
    case Field::DwmShadow: {
        const bool value = update.value.toBool();
        if (candidate.dwmShadow == value) return false;
        candidate.dwmShadow = value;
        return true;
    }
    case Field::MicaEnabled: {
        const bool value = update.value.toBool();
        if (candidate.micaEnabled == value) return false;
        candidate.micaEnabled = value;
        return true;
    }
    case Field::DpiScale: {
        const int value = update.value.toInt();
        if (candidate.dpiScale == value) return false;
        candidate.dpiScale = value;
        return true;
    }
    case Field::WindowType: {
        const int value = update.value.toInt();
        if (candidate.windowType == value) return false;
        candidate.windowType = value;
        return true;
    }
    case Field::Theme: {
        const QString value = update.value.toString();
        if (candidate.theme == value) return false;
        candidate.theme = value;
        return true;
    }
    case Field::Skin: {
        const QString value = update.value.toString();
        if (candidate.skin == value) return false;
        candidate.skin = value;
        return true;
    }
    case Field::Language: {
        const QString value = update.value.toString();
        if (candidate.language == value) return false;
        candidate.language = value;
        return true;
    }
    case Field::AccentColor: {
        const QString value = update.value.toString();
        if (candidate.accentColor == value) return false;
        candidate.accentColor = value;
        return true;
    }
    }
    return false;
}

void ConfigManager::enqueueUpdate(Field field, const QVariant &value,
                                  quint64 runtimeRequestId) {
    const bool wasPending = persistencePending();
    m_pendingUpdates.enqueue({field, value, runtimeRequestId});
    if (!wasPending) emit persistencePendingChanged();
    startNextPersistence();
}

void ConfigManager::enqueueRuntimeUpdate(Field field, const QVariant &value) {
    auto *manager = ThemeManager::instance();
    switch (field) {
    case Field::Theme:
        manager->applyTheme(themeFromString(value.toString()));
        break;
    case Field::Skin:
        manager->applySkin(skinFromString(value.toString()));
        break;
    case Field::AccentColor:
        manager->applyAccentColor(value.toString());
        break;
    default:
        break;
    }
    const quint64 requestId = ++m_runtimeRequestId;
    m_runtimeOverrides.at(static_cast<std::size_t>(field)) = requestId;
    enqueueUpdate(field, value, requestId);
}

QString *ConfigManager::ephemeralAppearanceValue(Field field) {
    switch (field) {
    case Field::Theme: return &m_state.theme;
    case Field::Skin: return &m_state.skin;
    case Field::Language: return &m_state.language;
    case Field::AccentColor: return &m_state.accentColor;
    default: return nullptr;
    }
}

void ConfigManager::applyEphemeralRuntime(Field field, const QString &value) {
    auto *manager = ThemeManager::instance();
    switch (field) {
    case Field::Theme: manager->applyTheme(themeFromString(value)); break;
    case Field::Skin: manager->applySkin(skinFromString(value)); break;
    case Field::AccentColor: manager->applyAccentColor(value); break;
    default: break;
    }
}

void ConfigManager::publishEphemeralField(Field field) {
    switch (field) {
    case Field::Theme: emit themeChanged(); break;
    case Field::Skin: emit skinChanged(); break;
    case Field::Language: emit languageChanged(); break;
    case Field::AccentColor: emit accentColorChanged(); break;
    default: break;
    }
}

void ConfigManager::setEphemeralAppearance(Field field, const QVariant &value) {
    const QString text = value.toString();
    applyEphemeralRuntime(field, text);
    QString *current = ephemeralAppearanceValue(field);
    if (!current || *current == text) return;
    *current = text;
    publishEphemeralField(field);
    emit configChanged();
}

void ConfigManager::startNextPersistence() {
    if (m_activeWrite.has_value()) return;
    while (!m_pendingUpdates.isEmpty()) {
        const PendingUpdate update = m_pendingUpdates.dequeue();
        State candidate = m_state;
        if (!applyUpdate(candidate, update)) {
            settleRuntimeOverride(update.field, update.runtimeRequestId, false);
            continue;
        }

        const QString path = configFilePath();
        QByteArray payload = serialize(candidate, m_persistAppearance);
        const PersistenceWriter writer = m_persistenceWriter;
        const bool preserveAppearance = !m_persistAppearance;
        m_activeWrite = ActiveWrite{
            update.field, candidate, update.runtimeRequestId};
        m_persistenceWatcher.setFuture(QtConcurrent::run(
            [writer, path, payload, preserveAppearance]() mutable {
                if (preserveAppearance &&
                    !mergeLatestAppearance(path, payload))
                    return false;
                return writer(path, payload);
            }));
        return;
    }
    emit persistencePendingChanged();
}

void ConfigManager::finishPersistence() {
    if (!m_activeWrite.has_value()) return;
    const ActiveWrite completed = *m_activeWrite;
    if (m_persistenceWatcher.result()) {
        m_state = completed.candidate;
        settleRuntimeOverride(completed.field, completed.runtimeRequestId, false);
        publishCommittedField(completed.field);
        emit configChanged();
    } else {
        settleRuntimeOverride(completed.field, completed.runtimeRequestId, true);
    }
    m_activeWrite.reset();
    startNextPersistence();
}

void ConfigManager::publishCommittedField(Field field) {
    switch (field) {
    case Field::LazyLoading:
        emit lazyLoadingChanged();
        break;
    case Field::DwmShadow:
        emit dwmShadowChanged();
        break;
    case Field::MicaEnabled:
        emit micaEnabledChanged();
        break;
    case Field::DpiScale:
        emit dpiScaleChanged();
        break;
    case Field::WindowType:
        emit windowTypeChanged();
        break;
    case Field::Theme:
        if (!hasRuntimeOverride(field))
            ThemeManager::instance()->applyTheme(themeFromString(m_state.theme));
        emit themeChanged();
        break;
    case Field::Skin:
        if (!hasRuntimeOverride(field))
            ThemeManager::instance()->applySkin(skinFromString(m_state.skin));
        emit skinChanged();
        break;
    case Field::Language:
        emit languageChanged();
        break;
    case Field::AccentColor:
        if (!hasRuntimeOverride(field))
            ThemeManager::instance()->applyAccentColor(m_state.accentColor);
        emit accentColorChanged();
        break;
    }
}

bool ConfigManager::hasRuntimeOverride(Field field) const {
    return m_runtimeOverrides.at(static_cast<std::size_t>(field)) != 0;
}

void ConfigManager::settleRuntimeOverride(Field field, quint64 requestId,
                                          bool failed) {
    if (requestId == 0) return;
    auto &activeRequest =
        m_runtimeOverrides.at(static_cast<std::size_t>(field));
    if (activeRequest != requestId) return;
    activeRequest = 0;
    if (!failed) return;

    auto *manager = ThemeManager::instance();
    switch (field) {
    case Field::Theme:
        manager->applyTheme(themeFromString(m_state.theme));
        break;
    case Field::Skin:
        manager->applySkin(skinFromString(m_state.skin));
        break;
    case Field::AccentColor:
        manager->applyAccentColor(m_state.accentColor);
        break;
    default:
        break;
    }
}

bool ConfigManager::waitForPersistence(int timeoutMs) {
    if (timeoutMs < 0) {
        qWarning() << "prism::ConfigManager 持久化等待超时不能为负数:" << timeoutMs;
        return false;
    }
    if (!persistencePending()) return true;
    if (!QCoreApplication::instance() || timeoutMs == 0) return false;

    QEventLoop loop;
    QTimer timer;
    timer.setSingleShot(true);
    connect(this, &ConfigManager::persistencePendingChanged,
            &loop, &QEventLoop::quit);
    connect(&timer, &QTimer::timeout, &loop, &QEventLoop::quit);
    timer.start(timeoutMs);
    while (persistencePending() && timer.isActive()) loop.exec();
    return !persistencePending();
}

// ---- setters: 去重 + 串行后台落盘 + 成功后发信号 ----
void ConfigManager::setLazyLoading(bool value) {
    if (!persistencePending() && m_state.lazyLoading == value) return;
    enqueueUpdate(Field::LazyLoading, value);
}
void ConfigManager::setDwmShadow(bool value) {
    if (!persistencePending() && m_state.dwmShadow == value) return;
    enqueueUpdate(Field::DwmShadow, value);
}
void ConfigManager::setDpiScale(const QVariant &candidateValue) {
    int value = 0;
    if (!strictIntegerVariant(candidateValue, value) || !isValidDpiScale(value)) {
        qWarning() << "prism::ConfigManager 无效 dpiScale:" << candidateValue;
        return;
    }
    if (!persistencePending() && m_state.dpiScale == value) return;
    enqueueUpdate(Field::DpiScale, value);
}
void ConfigManager::setMicaEnabled(bool value) {
    if (!persistencePending() && m_state.micaEnabled == value) return;
    enqueueUpdate(Field::MicaEnabled, value);
}
void ConfigManager::setWindowType(const QVariant &candidateValue) {
    int value = 0;
    if (!strictIntegerVariant(candidateValue, value) || !isValidWindowType(value)) {
        qWarning() << "prism::ConfigManager 无效 windowType:" << candidateValue;
        return;
    }
    if (!persistencePending() && m_state.windowType == value) return;
    enqueueUpdate(Field::WindowType, value);
}
void ConfigManager::setTheme(const QString &value) {
    if (!isValidTheme(value)) {
        qWarning() << "prism::ConfigManager 无效 theme:" << value;
        return;
    }
    if (!m_persistAppearance) {
        setEphemeralAppearance(Field::Theme, value);
        return;
    }
    if (!persistencePending() && m_state.theme == value) return;
    enqueueRuntimeUpdate(Field::Theme, value);
}
void ConfigManager::setSkin(const QString &value) {
    if (!isValidSkin(value)) {
        qWarning() << "prism::ConfigManager 无效 skin:" << value;
        return;
    }
    if (!m_persistAppearance) {
        setEphemeralAppearance(Field::Skin, value);
        return;
    }
    if (!persistencePending() && m_state.skin == value) return;
    enqueueRuntimeUpdate(Field::Skin, value);
}
void ConfigManager::setLanguage(const QString &value) {
    if (!isValidLanguage(value)) {
        qWarning() << "prism::ConfigManager 无效 language:" << value;
        return;
    }
    if (!m_persistAppearance) {
        setEphemeralAppearance(Field::Language, value);
        return;
    }
    if (!persistencePending() && m_state.language == value) return;
    enqueueUpdate(Field::Language, value);
}
void ConfigManager::setAccentColor(const QString &value) {
    if (!isValidAccentColor(value)) {
        qWarning() << "prism::ConfigManager 无效 accentColor:" << value;
        return;
    }
    if (!m_persistAppearance) {
        setEphemeralAppearance(Field::AccentColor, value);
        return;
    }
    if (!persistencePending() && m_state.accentColor == value) return;
    enqueueRuntimeUpdate(Field::AccentColor, value);
}

}  // namespace prism
