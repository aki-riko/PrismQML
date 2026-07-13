// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - ConfigManager (镜像 Python config/config_manager.py + app_config.py)
// 持久化 JSON 格式与 Python 兼容: {"Window":{"LazyLoading":bool,"DwmShadow":bool,
//   "MicaEnabled":bool,"DpiScale":int,"WindowType":int}}。单例默认落盘
// ~/.prismqml/app.json，首次使用前可用 PRISMQML_CONFIG_FILE 覆盖。
#pragma once

#include "prism/ConfigContracts.h"

#include <QObject>
#include <QString>

namespace prism {

class ConfigManager : public QObject {
    Q_OBJECT

    Q_PROPERTY(bool lazyLoading READ lazyLoading NOTIFY lazyLoadingChanged)
    Q_PROPERTY(bool dwmShadow READ dwmShadow NOTIFY dwmShadowChanged)
    Q_PROPERTY(int dpiScale READ dpiScale NOTIFY dpiScaleChanged)
    Q_PROPERTY(QVariantList dpiScaleOptions READ dpiScaleOptions CONSTANT)
    Q_PROPERTY(bool micaEnabled READ micaEnabled NOTIFY micaEnabledChanged)
    Q_PROPERTY(int windowType READ windowType NOTIFY windowTypeChanged)
    Q_PROPERTY(QVariantList windowTypeOptions READ windowTypeOptions CONSTANT)

public:
    static ConfigManager *instance();
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

public slots:
    // ---- QML 可调用 setter (镜像 Python @Slot) ----
    void setLazyLoading(bool value);
    void setDwmShadow(bool value);
    void setDpiScale(const QVariant &value);
    void setMicaEnabled(bool value);
    void setWindowType(const QVariant &value);
    QString getConfigPath() const;

signals:
    void configChanged();
    void lazyLoadingChanged();
    void dwmShadowChanged();
    void dpiScaleChanged();
    void micaEnabledChanged();
    void windowTypeChanged();

private:
    struct State {
        bool lazyLoading = true;
        bool dwmShadow = true;
        bool micaEnabled = false;
        int dpiScale = 0;
        int windowType = 1;
    };

    explicit ConfigManager(QObject *parent = nullptr);
    QString configFilePath() const;
    void load();
    bool save(const State &candidate) const;
    bool commit(const State &candidate);

    QString m_configFilePath;
    State m_state;
};

}  // namespace prism
