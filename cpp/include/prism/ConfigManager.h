// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - ConfigManager (镜像 Python config/config_manager.py + app_config.py)
// 持久化 JSON 格式与 Python 兼容: Window 保存窗口偏好，Appearance 保存主题、
// 皮肤、语言与主题色。单例默认落盘
// ~/.prismqml/app.json，首次使用前可用 PRISMQML_CONFIG_FILE 覆盖。
#pragma once

#include "prism/ConfigContracts.h"

#include <QFutureWatcher>
#include <QObject>
#include <QQueue>
#include <QString>
#include <QVariant>

#include <functional>
#include <optional>

namespace prism {

class ConfigManagerTestAccess;

class ConfigManager : public QObject {
    Q_OBJECT

    Q_PROPERTY(bool lazyLoading READ lazyLoading NOTIFY lazyLoadingChanged)
    Q_PROPERTY(bool dwmShadow READ dwmShadow NOTIFY dwmShadowChanged)
    Q_PROPERTY(int dpiScale READ dpiScale NOTIFY dpiScaleChanged)
    Q_PROPERTY(QVariantList dpiScaleOptions READ dpiScaleOptions CONSTANT)
    Q_PROPERTY(bool micaEnabled READ micaEnabled NOTIFY micaEnabledChanged)
    Q_PROPERTY(int windowType READ windowType NOTIFY windowTypeChanged)
    Q_PROPERTY(QVariantList windowTypeOptions READ windowTypeOptions CONSTANT)
    Q_PROPERTY(QString theme READ theme NOTIFY themeChanged)
    Q_PROPERTY(QVariantList themeOptions READ themeOptions CONSTANT)
    Q_PROPERTY(QString skin READ skin NOTIFY skinChanged)
    Q_PROPERTY(QVariantList skinOptions READ skinOptions CONSTANT)
    Q_PROPERTY(QString language READ language NOTIFY languageChanged)
    Q_PROPERTY(QVariantList languageOptions READ languageOptions CONSTANT)
    Q_PROPERTY(QString accentColor READ accentColor NOTIFY accentColorChanged)
    Q_PROPERTY(bool persistencePending READ persistencePending
               NOTIFY persistencePendingChanged)

public:
    static constexpr int kDefaultPersistenceTimeoutMs = 5000;

    static ConfigManager *instance();
    ~ConfigManager() override;
    // Explicit isolated path; an empty path fails closed. 显式隔离路径；空路径安全拒绝。
    explicit ConfigManager(const QString &configFilePath, QObject *parent = nullptr);

    // ---- 属性读取 (默认值镜像 Python app_config.py) ----
    bool lazyLoading() const { return m_state.lazyLoading; }
    bool dwmShadow() const { return m_state.dwmShadow; }
    int dpiScale() const { return m_state.dpiScale; }
    QVariantList dpiScaleOptions() const;
    bool micaEnabled() const { return m_state.micaEnabled; }
    int windowType() const { return m_state.windowType; }
    QVariantList windowTypeOptions() const;
    QString theme() const { return m_state.theme; }
    QVariantList themeOptions() const;
    QString skin() const { return m_state.skin; }
    QVariantList skinOptions() const;
    QString language() const { return m_state.language; }
    QVariantList languageOptions() const;
    QString accentColor() const { return m_state.accentColor; }
    bool persistencePending() const;

public slots:
    // ---- QML 可调用 setter (镜像 Python @Slot) ----
    void setLazyLoading(bool value);
    void setDwmShadow(bool value);
    void setDpiScale(const QVariant &value);
    void setMicaEnabled(bool value);
    void setWindowType(const QVariant &value);
    void setTheme(const QString &value);
    void setSkin(const QString &value);
    void setLanguage(const QString &value);
    void setAccentColor(const QString &value);
    QString getConfigPath() const;
    bool waitForPersistence(
        int timeoutMs = kDefaultPersistenceTimeoutMs);

signals:
    void configChanged();
    void lazyLoadingChanged();
    void dwmShadowChanged();
    void dpiScaleChanged();
    void micaEnabledChanged();
    void windowTypeChanged();
    void themeChanged();
    void skinChanged();
    void languageChanged();
    void accentColorChanged();
    void persistencePendingChanged();

private:
    struct State {
        bool lazyLoading = true;
        bool dwmShadow = true;
        bool micaEnabled = false;
        int dpiScale = 0;
        int windowType = 1;
        QString theme = QStringLiteral("auto");
        QString skin = QStringLiteral("fluent");
        QString language = QStringLiteral("auto");
        QString accentColor = QStringLiteral("#0e5a9c");
    };

    enum class Field {
        LazyLoading,
        DwmShadow,
        MicaEnabled,
        DpiScale,
        WindowType,
        Theme,
        Skin,
        Language,
        AccentColor,
    };

    struct PendingUpdate {
        Field field;
        QVariant value;
    };

    struct ActiveWrite {
        Field field;
        State candidate;
    };

    using PersistenceWriter =
        std::function<bool(const QString &, const QByteArray &)>;

    explicit ConfigManager(QObject *parent = nullptr);
    QString configFilePath() const;
    void load();
    static QByteArray serialize(const State &candidate);
    static bool applyUpdate(State &candidate, const PendingUpdate &update);
    void enqueueUpdate(Field field, const QVariant &value);
    void startNextPersistence();
    void finishPersistence();
    void publishCommittedField(Field field);
    void applyAppearanceToRuntime() const;

    friend class ConfigManagerTestAccess;
    QString m_configFilePath;
    State m_state;
    QQueue<PendingUpdate> m_pendingUpdates;
    std::optional<ActiveWrite> m_activeWrite;
    QFutureWatcher<bool> m_persistenceWatcher;
    PersistenceWriter m_persistenceWriter;
};

}  // namespace prism
