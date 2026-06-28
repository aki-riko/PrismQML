// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - 访问器别名 + NavigationItem (与 Python __all__ 对称)
// Python 用 getX()/get_x() 风格自由函数取单例; C++ 提供同名别名转发到 instance(),
// 使两边 API 逐字对称。NavigationItem 镜像 Python 数据类(C++ 也可直接用 addPage)。
#pragma once

#include "prism/ThemeManager.h"
#include "prism/ShadowManager.h"
#include "prism/MicaManager.h"
#include "prism/ConfigManager.h"
#include "prism/AcrylicHelper.h"
#include "prism/ClipboardHelper.h"
#include "prism/QRCodeGenerator.h"
#include "prism/ScreenEyedropper.h"
#include "prism/SvgImageProvider.h"
#include "prism/SystemTray.h"
#include "prism/Logger.h"
#include "prism/Platform.h"
#include <QString>
#include <functional>

#if PRISM_HAS_WINDOW_CHROME && defined(Q_OS_WIN)
#  include <QGuiApplication>
#endif

namespace prism {

// ==================== getter 别名 (镜像 Python get*/get_* 自由函数) ====================
inline ThemeManager *getThemeManager() { return ThemeManager::instance(); }
inline ShadowManager *getShadowManager() { return ShadowManager::instance(); }
inline MicaManager *get_mica_manager() { return MicaManager::instance(); }
inline ConfigManager *getConfigManager() { return ConfigManager::instance(); }
inline AcrylicHelper *get_acrylic_helper() { return AcrylicHelper::instance(); }
inline ClipboardHelper *get_clipboard_helper() { return ClipboardHelper::instance(); }
inline QRCodeGenerator *get_qrcode_generator() { return QRCodeGenerator::instance(); }
inline ScreenEyedropperManager *get_screen_eyedropper_manager() {
    return ScreenEyedropperManager::instance();
}
inline SvgImageProvider *get_svg_provider() { return SvgImageProvider::instance(); }
inline QRCodeImageProvider *get_qrcode_provider() {
    // provider 由引擎在 registerTypes 中 new; 此处提供一个独立实例供按需使用
    static QRCodeImageProvider *p = new QRCodeImageProvider();
    return p;
}

// createSystemTrayIcon (镜像 Python 工厂函数)
inline SystemTrayIcon *createSystemTrayIcon(const QString &icon = QString(),
                                            const QString &toolTip = QString()) {
    return new SystemTrayIcon(icon, toolTip);
}

// ==================== 装配/工具 别名 (镜像 Python 模块级函数) ====================
// init_style: 初始化 QML 控件样式为 Basic (Python 在 QGuiApplication 前调)
// C++ 用纯 QML 控件不依赖 QtQuick.Controls Style, 此处保留为对称 no-op。
inline void init_style() { qputenv("QT_QUICK_CONTROLS_STYLE", "Basic"); }

// installDwmSyncFilter: 安装 DWM 同步事件过滤器 (仅桌面 Windows 有意义)
// C++ 的 NativeWindow 已用 QAbstractNativeEventFilter 处理, 此处对称保留。
inline void installDwmSyncFilter() { /* 桌面 NativeWindow 已处理; 移动端 no-op */ }

// getLogger: 取日志器 (镜像 Python getLogger; C++ 日志是 prism::log 命名空间函数,
// 返回一个轻量包装供链式调用对称)。直接用 prism::log::info(...) 更地道。
struct LoggerRef {
    void debug(const QString &m, const QString &t = {}) const { log::debug(m, t); }
    void info(const QString &m, const QString &t = {}) const { log::info(m, t); }
    void warning(const QString &m, const QString &t = {}) const { log::warning(m, t); }
    void error(const QString &m, const QString &t = {}) const { log::error(m, t); }
};
inline LoggerRef getLogger() { return LoggerRef{}; }

// ==================== NavigationItem (镜像 Python 数据类) ====================
// 描述一个导航项。C++ 既可用 App/Window 的 addPage(url,icon,text) 直接添加,
// 也可构造 NavigationItem 显式持有配置 (对称 Python API)。
struct NavigationItem {
    QString text;
    QString icon;
    QString pageQmlUrl;                   // 页面 QML (空=纯功能项)
    std::function<void()> onActivated;    // 功能项回调 (可选)

    NavigationItem() = default;
    NavigationItem(const QString &t, const QString &i, const QString &url = QString())
        : text(t), icon(i), pageQmlUrl(url) {}
};

}  // namespace prism
