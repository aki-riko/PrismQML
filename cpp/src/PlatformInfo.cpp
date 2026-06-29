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
#include <QInputMethod>

namespace prism {

PlatformInfo *PlatformInfo::instance() {
    static PlatformInfo *s = new PlatformInfo();
    return s;
}

PlatformInfo::PlatformInfo(QObject *parent) : QObject(parent) {
    // 防御: 非 GUI app(如 QCoreApplication 单测) 下无屏幕/输入法, 跳过连接避免崩溃
    if (!qobject_cast<QGuiApplication *>(QCoreApplication::instance()))
        return;
    // 连接屏幕几何/方向变化 -> screenChanged, 使 isCompact/safeArea 随旋转更新
    if (QScreen *s = QGuiApplication::primaryScreen()) {
        connect(s, &QScreen::geometryChanged, this, &PlatformInfo::screenChanged);
        connect(s, &QScreen::orientationChanged, this, &PlatformInfo::screenChanged);
        connect(s, &QScreen::availableGeometryChanged, this, &PlatformInfo::screenChanged);
    }
    // 软键盘弹出/收起 -> keyboardChanged, 使输入框避让
    if (QInputMethod *im = QGuiApplication::inputMethod()) {
        connect(im, &QInputMethod::keyboardRectangleChanged, this, &PlatformInfo::keyboardChanged);
        connect(im, &QInputMethod::visibleChanged, this, &PlatformInfo::keyboardChanged);
    }
}

int PlatformInfo::keyboardHeight() const {
    if (!qobject_cast<QGuiApplication *>(QCoreApplication::instance()))
        return 0;  // 非 GUI app 无输入法
    if (QInputMethod *im = QGuiApplication::inputMethod()) {
        if (im->isVisible())
            return static_cast<int>(im->keyboardRectangle().height());
    }
    return 0;
}

bool PlatformInfo::keyboardVisible() const {
    if (!qobject_cast<QGuiApplication *>(QCoreApplication::instance()))
        return false;
    if (QInputMethod *im = QGuiApplication::inputMethod())
        return im->isVisible();
    return false;
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
    // 测试钩子: 强制窄屏验证底部 Tab 布局
    if (QProcessEnvironment::systemEnvironment()
            .value(QStringLiteral("PRISM_FORCE_COMPACT")) == QLatin1String("1"))
        return true;
    const int w = screenWidth();
    // 窄屏断点 600px (Material): 导航应改底部 Tab/抽屉
    return isMobile() || (w > 0 && w < 600);
}

// 安全区 insets: 移动端避让状态栏/刘海/导航条。
// 注: 精确 cutout 需 Android JNI 读 DisplayCutout/WindowInsets; 当前用基于
// devicePixelRatio 的合理估算(状态栏~24dp, 手势导航条~24dp), 桌面为 0。
int PlatformInfo::safeAreaTop() const {
#if PRISM_MOBILE
    qreal dpr = 1.0;
    if (QScreen *s = QGuiApplication::primaryScreen())
        dpr = s->devicePixelRatio();
    return static_cast<int>(24 * dpr);  // 状态栏 ~24dp
#else
    return 0;
#endif
}

int PlatformInfo::safeAreaBottom() const {
#if PRISM_MOBILE
    qreal dpr = 1.0;
    if (QScreen *s = QGuiApplication::primaryScreen())
        dpr = s->devicePixelRatio();
    return static_cast<int>(24 * dpr);  // 手势导航条 ~24dp
#else
    return 0;
#endif
}

}  // namespace prism
