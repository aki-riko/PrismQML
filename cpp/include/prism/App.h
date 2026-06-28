// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - App 门面 (镜像 Python window/app.py)
#pragma once

#include "prism/Window.h"
#include <QString>
#include <memory>
#include <vector>

class QApplication;
class QQmlApplicationEngine;

namespace prism {

// App - 应用入口门面 (镜像 Python App)
// 内部持有 QApplication + QQmlApplicationEngine, 构造时完成注入装配。
// 用 QApplication(QtWidgets) 而非 QGuiApplication: 与 Python App 对齐, 且
// SystemTrayIcon 的 QMenu 等 QtWidgets 控件需要 QApplication 才能工作。
// Qt 已有的方法(quit/exec 等)在 C++ 侧直接用 qApp/本类转发, 不重复包装。
class App {
public:
    // argv 透传给 QApplication。importPath 指向 PrismQML 模块的父目录;
    // 为空时用 resolveImportPath() 解析(环境变量 PRISMQML_QML_DIR)。
    App(int &argc, char **argv, const QString &importPath = QString());
    ~App();

    App(const App &) = delete;
    App &operator=(const App &) = delete;

    // 创建窗口 (镜像 Python create_window)
    Window &createWindow(WindowType type = WindowType::Bar);

    // 进入事件循环 (转发 QApplication::exec)
    int exec();

    // 逃生口: 直接拿底层引擎/应用 (镜像 Python engine / qapp 属性)
    QQmlApplicationEngine *engine() const { return m_engine.get(); }
    QApplication *qapp() const { return m_app.get(); }

    static App *instance() { return s_instance; }

private:
    static App *s_instance;
    std::unique_ptr<QApplication> m_app;
    std::unique_ptr<QQmlApplicationEngine> m_engine;
    std::vector<std::unique_ptr<Window>> m_windows;
    QString m_importPath;
};

}  // namespace prism
