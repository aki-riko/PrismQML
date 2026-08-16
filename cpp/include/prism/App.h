// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - App 门面 (镜像 Python window/app.py)
#pragma once

#include "prism/SystemTray.h"
#include "prism/Window.h"
#include <QString>
#include <memory>
#include <optional>
#include <vector>
#include <functional>

class QApplication;
class QQmlApplicationEngine;

namespace prism {

class AppLifecycleBridge;  // 内部: 中转 Qt applicationStateChanged 信号
class Updater;             // 自动更新底层 (enableAutoUpdate 使用)

inline constexpr char kQmlXhrAllowFileReadEnvironment[] = "QML_XHR_ALLOW_FILE_READ";

// Must run before QQmlEngine creation. 必须在创建 QQmlEngine 前调用。
void configureQmlEnvironment(bool allowFileRead = true);

// App - 应用入口门面 (镜像 Python App)
// 内部持有 QApplication + QQmlApplicationEngine, 构造时完成注入装配。
// 用 QApplication(QtWidgets) 而非 QGuiApplication: 与 Python App 对齐, 且
// SystemTrayIcon 的 QMenu 等 QtWidgets 控件需要 QApplication 才能工作。
// Qt 已有的方法(quit/exec 等)在 C++ 侧直接用 qApp/本类转发, 不重复包装。
class App {
public:
    // argv 透传给 QApplication。importPath 指向 PrismQML 模块的父目录;
    // 为空时用 resolveImportPath() 解析(环境变量 PRISMQML_QML_DIR)。
    // configFilePath 非空时默认持久化应用外观；显式 false 由宿主自行管理外观。
    App(int &argc, char **argv, const QString &importPath = QString(),
        bool allowQmlFileRead = true,
        const QString &configFilePath = QString(),
        std::optional<bool> persistAppearance = std::nullopt);
    ~App();

    App(const App &) = delete;
    App &operator=(const App &) = delete;

    // 创建窗口 (镜像 Python create_window)
    Window &createWindow(WindowType type = WindowType::Bar);

    // Set one shared runtime icon for Qt, windows, splash, and managed trays.
    // 设置 Qt、窗口、启动画面及托管托盘共用的运行时图标。
    void setApplicationIcon(const QString &icon, bool colored = true);
    const QString &applicationIcon() const { return m_applicationIcon; }
    bool applicationIconColored() const { return m_applicationIconColored; }

    // 创建由 App 托管的托盘；托盘会在 QML 引擎销毁前释放。
    SystemTrayIcon &createSystemTrayIcon(const QString &icon = QString(),
                                         const QString &toolTip = QString(),
                                         bool menuOnLeftClick = true);

    // 进入事件循环 (转发 QApplication::exec)
    int exec();

    // ==================== 移动端生命周期 (桌面也可用) ====================
    // onPause: 应用进入后台(移动端切走/锁屏) — 宜保存状态/暂停动画。
    // onResume: 应用回到前台 — 宜刷新/恢复。
    // 基于 Qt applicationStateChanged(Suspended/Hidden -> pause, Active -> resume)。
    void onPause(std::function<void()> cb);
    void onResume(std::function<void()> cb);

    // ==================== 自动更新 (一等能力) ====================
    // 一行接入 GitHub Release 自动更新:内部 new Updater 并注入为 QML 上下文
    // 属性 "appUpdater",配合 QML 门面 AutoUpdater{ updater: appUpdater } 使用。
    //   repo           形如 "owner/repo"
    //   currentVersion 当前版本 (如 "1.0.0";建议由 CMake/构建注入,勿硬编码)
    //   assetKeyword   Release 资产名匹配关键字 (默认 "Setup")
    // 重复调用以最后一次为准。返回底层 Updater 指针 (所有权仍归 App)。
    Updater *enableAutoUpdate(const QString &repo,
                              const QString &currentVersion,
                              const QString &assetKeyword = QStringLiteral("Setup"));

    // 逃生口: 直接拿底层引擎/应用 (镜像 Python engine / qapp 属性)
    QQmlApplicationEngine *engine() const { return m_engine.get(); }
    QApplication *qapp() const { return m_app.get(); }

    static App *instance() { return s_instance; }

private:
    friend class AppLifecycleBridge;
    static App *s_instance;
    std::unique_ptr<QApplication> m_app;
    std::unique_ptr<QQmlApplicationEngine> m_engine;
    std::vector<std::unique_ptr<Window>> m_windows;
    std::vector<std::unique_ptr<SystemTrayIcon>> m_systemTrays;
    QString m_importPath;
    QString m_applicationIcon;
    bool m_applicationIconColored = true;
    std::unique_ptr<AppLifecycleBridge> m_lifecycle;
    std::function<void()> m_onPause;
    std::function<void()> m_onResume;
    std::unique_ptr<Updater> m_updater;  // 自动更新底层实例 (enableAutoUpdate 创建)
};

}  // namespace prism

