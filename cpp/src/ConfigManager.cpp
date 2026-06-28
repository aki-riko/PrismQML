// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - ConfigManager 实现 (镜像 config_manager.py + settings_base.py)
#include "prism/ConfigManager.h"

#include <QStandardPaths>
#include <QDir>
#include <QFile>
#include <QSaveFile>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonValue>
#include <QDebug>

namespace prism {

ConfigManager *ConfigManager::instance() {
    static ConfigManager *s = new ConfigManager();
    return s;
}

ConfigManager::ConfigManager(QObject *parent) : QObject(parent) {
    load();
}

// 配置路径: ~/.prismqml/app.json (镜像 Python DEFAULT_APP_CONFIG)
QString ConfigManager::configFilePath() const {
    return QDir(QDir::homePath()).filePath(QStringLiteral(".prismqml/app.json"));
}

QString ConfigManager::getConfigPath() const { return configFilePath(); }

void ConfigManager::load() {
    QFile f(configFilePath());
    if (!f.exists() || !f.open(QIODevice::ReadOnly)) {
        // 文件不存在用默认值 (镜像 Python: using defaults)
        return;
    }
    const QByteArray data = f.readAll();
    f.close();

    QJsonParseError err{};
    const QJsonDocument doc = QJsonDocument::fromJson(data, &err);
    if (err.error != QJsonParseError::NoError || !doc.isObject()) {
        qWarning() << "prism::ConfigManager 配置解析失败:" << err.errorString();
        return;
    }
    const QJsonObject win = doc.object().value(QStringLiteral("Window")).toObject();
    if (win.contains(QStringLiteral("LazyLoading")))
        m_lazyLoading = win.value(QStringLiteral("LazyLoading")).toBool(m_lazyLoading);
    if (win.contains(QStringLiteral("DwmShadow")))
        m_dwmShadow = win.value(QStringLiteral("DwmShadow")).toBool(m_dwmShadow);
    if (win.contains(QStringLiteral("MicaEnabled")))
        m_micaEnabled = win.value(QStringLiteral("MicaEnabled")).toBool(m_micaEnabled);
    if (win.contains(QStringLiteral("DpiScale")))
        m_dpiScale = win.value(QStringLiteral("DpiScale")).toInt(m_dpiScale);
    if (win.contains(QStringLiteral("WindowType")))
        m_windowType = win.value(QStringLiteral("WindowType")).toInt(m_windowType);
}

// 原子写入 (镜像 Python: 临时文件 + os.replace, 用 QSaveFile 等价)
void ConfigManager::save() const {
    const QString path = configFilePath();
    QDir().mkpath(QFileInfo(path).absolutePath());

    QJsonObject win;
    win[QStringLiteral("LazyLoading")] = m_lazyLoading;
    win[QStringLiteral("DwmShadow")] = m_dwmShadow;
    win[QStringLiteral("MicaEnabled")] = m_micaEnabled;
    win[QStringLiteral("DpiScale")] = m_dpiScale;
    win[QStringLiteral("WindowType")] = m_windowType;
    QJsonObject root;
    root[QStringLiteral("Window")] = win;

    QSaveFile f(path);
    if (!f.open(QIODevice::WriteOnly)) {
        qWarning() << "prism::ConfigManager 保存失败:" << f.errorString();
        return;
    }
    f.write(QJsonDocument(root).toJson(QJsonDocument::Indented));
    if (!f.commit())
        qWarning() << "prism::ConfigManager 提交失败:" << f.errorString();
}

// ---- setters: 去重 + 落盘 + 发信号 (镜像 Python set 行为) ----
void ConfigManager::setLazyLoading(bool value) {
    if (m_lazyLoading != value) {
        m_lazyLoading = value; save();
        emit lazyLoadingChanged(); emit configChanged();
    }
}
void ConfigManager::setDwmShadow(bool value) {
    if (m_dwmShadow != value) {
        m_dwmShadow = value; save();
        emit dwmShadowChanged(); emit configChanged();
    }
}
void ConfigManager::setDpiScale(int value) {
    // 校验取值 (镜像 Python Validator.choice([0,100,125,150,175,200]))
    static const QList<int> kValid = {0, 100, 125, 150, 175, 200};
    if (!kValid.contains(value)) {
        qWarning() << "prism::ConfigManager 无效 dpiScale:" << value;
        return;
    }
    if (m_dpiScale != value) {
        m_dpiScale = value; save();
        emit dpiScaleChanged(); emit configChanged();
    }
}
void ConfigManager::setMicaEnabled(bool value) {
    if (m_micaEnabled != value) {
        m_micaEnabled = value; save();
        emit micaEnabledChanged(); emit configChanged();
    }
}
void ConfigManager::setWindowType(int value) {
    // 校验取值 (镜像 Python Validator.choice([0,1,2,3]))
    if (value < 0 || value > 3) {
        qWarning() << "prism::ConfigManager 无效 windowType:" << value;
        return;
    }
    if (m_windowType != value) {
        m_windowType = value; save();
        emit windowTypeChanged(); emit configChanged();
    }
}

}  // namespace prism
