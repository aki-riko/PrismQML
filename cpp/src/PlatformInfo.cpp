// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - PlatformInfo 实现
#include "prism/PlatformInfo.h"
#include "prism/Platform.h"

#include <QGuiApplication>
#include <QScreen>
#include <QProcessEnvironment>

namespace prism {

PlatformInfo *PlatformInfo::instance() {
    static PlatformInfo *s = new PlatformInfo();
    return s;
}

bool PlatformInfo::isMobile() const {
    return PRISM_MOBILE;
}

bool PlatformInfo::isTouch() const {
#if PRISM_MOBILE
    return true;
#else
    // 桌面默认非触摸; 测试可用 PRISM_FORCE_TOUCH=1 强制触摸态验证响应式
    return QProcessEnvironment::systemEnvironment()
               .value(QStringLiteral("PRISM_FORCE_TOUCH")) == QLatin1String("1");
#endif
}

QString PlatformInfo::platformName() const {
#if defined(Q_OS_ANDROID)
    return QStringLiteral("android");
#elif defined(Q_OS_IOS)
    return QStringLiteral("ios");
#elif defined(Q_OS_WASM)
    return QStringLiteral("wasm");
#elif defined(Q_OS_WIN)
    return QStringLiteral("windows");
#elif defined(Q_OS_MACOS)
    return QStringLiteral("macos");
#elif defined(Q_OS_LINUX)
    return QStringLiteral("linux");
#else
    return QStringLiteral("unknown");
#endif
}

int PlatformInfo::touchTargetSize() const {
    return isTouch() ? 48 : 32;  // Material 48dp / 桌面 32px
}

int PlatformInfo::screenWidth() const {
    if (QScreen *s = QGuiApplication::primaryScreen())
        return static_cast<int>(s->availableGeometry().width());
    return 0;
}

bool PlatformInfo::isCompact() const {
    const int w = screenWidth();
    // 窄屏断点 600px (Material): 导航应改底部 Tab/抽屉
    return isMobile() || (w > 0 && w < 600);
}

}  // namespace prism
