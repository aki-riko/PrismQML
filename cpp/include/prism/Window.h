// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - Window 门面 (镜像 Python window/window_base.py)
#pragma once

#include <QString>
#include <functional>

class QQmlEngine;
class QObject;

namespace prism {

// WindowType - 窗口类型枚举 (值对齐 Python WindowType IntEnum)
enum class WindowType { Split = 0, Bar = 1, Filled = 2 };

// Window - 窗口门面 (镜像 Python Window/WindowCore)
// 阶段 1: 用字符串拼 QML(镜像 _window_builder 的 loadData 做法)加载 Windows* 顶层窗口,
//         提供 setWindowTitle/resize/show。导航/页面管理(addPage)属阶段 2 完整窗口层。
class Window {
public:
    Window(QQmlEngine *engine, const QString &importPath, WindowType type);
    ~Window();

    void setWindowTitle(const QString &title);
    void resize(int width, int height);
    void show();

    // 底层 QML 根对象 (逃生口)
    QObject *rootObject() const { return m_root; }

    // 是否成功创建
    bool isValid() const { return m_root != nullptr; }

private:
    QQmlEngine *m_engine;
    QString m_importPath;
    WindowType m_type;
    QObject *m_root = nullptr;
    QString m_title;
    int m_width = 1000;
    int m_height = 700;

    void build();
    static QString escapeQml(const QString &text);
    static QString qmlComponentName(WindowType type);
};

}  // namespace prism
