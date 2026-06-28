// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - ConfigManager (镜像 Python config/config_manager.py + app_config.py)
// 持久化 JSON 格式与 Python 兼容: {"Window":{"LazyLoading":bool,"DwmShadow":bool,
//   "MicaEnabled":bool,"DpiScale":int,"WindowType":int}}, 落盘 ~/.prismqml/app.json
#pragma once

#include <QObject>
#include <QString>

namespace prism {

class ConfigManager : public QObject {
    Q_OBJECT

    Q_PROPERTY(bool lazyLoading READ lazyLoading NOTIFY lazyLoadingChanged)
    Q_PROPERTY(bool dwmShadow READ dwmShadow NOTIFY dwmShadowChanged)
    Q_PROPERTY(int dpiScale READ dpiScale NOTIFY dpiScaleChanged)
    Q_PROPERTY(bool micaEnabled READ micaEnabled NOTIFY micaEnabledChanged)
    Q_PROPERTY(int windowType READ windowType NOTIFY windowTypeChanged)

public:
    static ConfigManager *instance();

    // ---- 属性读取 (默认值镜像 Python app_config.py) ----
    bool lazyLoading() const { return m_lazyLoading; }
    bool dwmShadow() const { return m_dwmShadow; }
    int dpiScale() const { return m_dpiScale; }
    bool micaEnabled() const { return m_micaEnabled; }
    int windowType() const { return m_windowType; }

public slots:
    // ---- QML 可调用 setter (镜像 Python @Slot) ----
    void setLazyLoading(bool value);
    void setDwmShadow(bool value);
    void setDpiScale(int value);
    void setMicaEnabled(bool value);
    void setWindowType(int value);
    QString getConfigPath() const;

signals:
    void configChanged();
    void lazyLoadingChanged();
    void dwmShadowChanged();
    void dpiScaleChanged();
    void micaEnabledChanged();
    void windowTypeChanged();

private:
    explicit ConfigManager(QObject *parent = nullptr);
    QString configFilePath() const;
    void load();
    void save() const;

    bool m_lazyLoading = true;    // Window/LazyLoading default True
    bool m_dwmShadow = true;      // Window/DwmShadow   default True
    bool m_micaEnabled = false;   // Window/MicaEnabled default False
    int m_dpiScale = 0;           // Window/DpiScale    default 0 (跟随系统)
    int m_windowType = 1;         // Window/WindowType  default 1 (Bar)
};

}  // namespace prism
