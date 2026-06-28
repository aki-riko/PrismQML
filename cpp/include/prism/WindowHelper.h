// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - WindowHelper (镜像 Python core/window_helper.py)
#pragma once

#include <QObject>
#include <QString>

namespace prism {

// WindowHelper - 任务栏/Alt-Tab 应用图标 (QML: WindowHelper.setAppIcon)
class WindowHelper : public QObject {
    Q_OBJECT
public:
    static WindowHelper *instance();
public slots:
    void setAppIcon(const QString &icon);
private:
    explicit WindowHelper(QObject *parent = nullptr) : QObject(parent) {}
    static QString resolveIconPath(const QString &icon);
};

}  // namespace prism
