// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - Window 门面 (镜像 Python window/window_base.py + _page_manager.py)
#pragma once

#include <QString>
#include <QList>
#include <QHash>
#include <QObject>

class QQmlEngine;
class QObject;
class QQuickItem;

namespace prism {

class Window;

// NavBridge - 中转 QML currentPageChanged 信号到 Window (QML 信号无 C++ PMF, 需 slot)
class NavBridge : public QObject {
    Q_OBJECT
public:
    NavBridge(Window *owner, QObject *parent) : QObject(parent), m_owner(owner) {}
public slots:
    void onChanged(int index);
private:
    Window *m_owner;
};

// WindowType - 窗口类型枚举 (值对齐 Python WindowType IntEnum)
enum class WindowType { Split = 0, Bar = 1, Filled = 2 };

// NavPosition - 导航项位置 (镜像 Python addPage position 参数)
enum class NavPosition { Top, Bottom };

// Window - 窗口门面 (镜像 Python Window/WindowCore)
// 用字符串拼 QML 加载 Windows* 顶层窗口, addPage 注入导航项 + page_N 容器,
// 监听 currentPageChanged 懒加载页面 QML 组件并挂入对应容器。
class Window {
public:
    Window(QQmlEngine *engine, const QString &importPath, WindowType type);
    ~Window();

    void setWindowTitle(const QString &title);
    void resize(int width, int height);

    // addPage - 添加页面 (镜像 Python addPage)
    // pageQmlUrl: 页面 QML 文件路径(本地路径或 qrc/file url); 空则为纯功能导航项。
    // 返回页面索引。必须在 show() 之前调用。
    int addPage(const QString &pageQmlUrl, const QString &icon,
                const QString &text, NavPosition position = NavPosition::Top);

    void show();
    void navigateTo(int index);

    QObject *rootObject() const { return m_root; }
    bool isValid() const { return m_root != nullptr; }

private:
    friend class NavBridge;
    struct NavItem {
        QString pageQmlUrl;
        QString icon;
        QString text;
        NavPosition position;
    };

    QQmlEngine *m_engine;
    QString m_importPath;
    WindowType m_type;
    QObject *m_root = nullptr;
    QString m_title;
    int m_width = 1000;
    int m_height = 700;
    QList<NavItem> m_navItems;          // 顶部导航
    QList<NavItem> m_bottomNavItems;    // 底部导航
    QHash<int, QObject *> m_pages;      // 已创建的页面实例
    bool m_built = false;
    NavBridge *m_navBridge = nullptr;

    void build();
    void ensurePageCreated(int index);
    QQuickItem *findChildByName(const QString &name) const;
    void onCurrentPageChanged(int index);

    static QString escapeQml(const QString &text);
    static QString qmlComponentName(WindowType type);
    QString navItemsJson(const QList<NavItem> &items, int indexOffset) const;
};

}  // namespace prism
