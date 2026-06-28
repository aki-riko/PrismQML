// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - ScreenEyedropperManager (镜像 Python providers/screen_eyedropper.py)
// 全屏取色: startPicking 弹覆盖窗, 点击处取屏幕像素, colorPicked 回传
#pragma once

#include <QObject>
#include <QColor>

namespace prism {

class EyedropperOverlay;  // 内部全屏覆盖窗

class ScreenEyedropperManager : public QObject {
    Q_OBJECT
public:
    static ScreenEyedropperManager *instance();

public slots:
    void startPicking(bool isDark = false);
    void stopPicking();

signals:
    void colorPicked(const QColor &color);
    void pickingStarted();
    void pickingFinished();
    void pickingCancelled();

private:
    explicit ScreenEyedropperManager(QObject *parent = nullptr);
    EyedropperOverlay *m_overlay = nullptr;
};

}  // namespace prism
