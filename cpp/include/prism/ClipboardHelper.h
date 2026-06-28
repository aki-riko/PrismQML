// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - ClipboardHelper (镜像 Python providers/clipboard.py)
#pragma once

#include <QObject>
#include <QString>

namespace prism {

class ClipboardHelper : public QObject {
    Q_OBJECT
public:
    static ClipboardHelper *instance();
public slots:
    void copy(const QString &text);
    QString paste();
private:
    explicit ClipboardHelper(QObject *parent = nullptr) : QObject(parent) {}
};

}  // namespace prism
