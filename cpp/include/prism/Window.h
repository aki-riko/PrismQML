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
class QQuickCloseEvent;

namespace prism {

class Window;

// NavBridge - 中转 QML currentPageChanged 信号到 Window (QML 信号无 C++ PMF, 需 slot)
class NavBridge : public QObject {
    Q_OBJECT
public:
    NavBridge(Window *owner, QObject *parent) : QObject(parent), m_owner(owner) {}
public slots:
    void onChanged(int index);
    void onClosing(QQuickCloseEvent *event);  // 返回键/关闭请求 -> goBack 或退出
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
    // setWindowIcon - 设置标题栏 app 图标 (镜像 Python windowIcon 属性)
    // iconUrl: 图标路径(qrc:/file:/磁盘路径或图标名); colored: true=彩色图标跳过着色叠加。
    void setWindowIcon(const QString &iconUrl, bool colored = true);
    void resize(int width, int height);

    // addPage - 添加页面 (镜像 Python addPage)
    // pageQmlUrl: 页面 QML 文件路径(本地路径或 qrc/file url); 空则为纯功能导航项。
    // selectable: false=纯功能项(点击只触发回调不切页, 如底部 User 头像)。
    // 返回页面索引。必须在 show() 之前调用。
    int addPage(const QString &pageQmlUrl, const QString &icon,
                const QString &text, NavPosition position = NavPosition::Top,
                bool selectable = true);

    // setSplash - 配置启动画面 (镜像 Python setSplash)。show() 前调用。
    // 默认开启, icon/title 空则回退 windowIcon/windowTitle。enabled=false 禁用。
    void setSplash(bool enabled, const QString &icon = QString(),
                   const QString &title = QString(), const QString &subtitle = QString());

    void show();
    void navigateTo(int index);

    // goBack - 返回导航历史上一页 (移动端返回键惯例)。
    // 返回 true=已弹栈到上一页; false=历史栈空(调用方应退出 App)。
    bool goBack();
    bool canGoBack() const { return m_navHistory.size() > 1; }

    QObject *rootObject() const { return m_root; }
    bool isValid() const { return m_root != nullptr; }

private:
    friend class NavBridge;
    struct NavItem {
        QString pageQmlUrl;
        QString icon;
        QString text;
        NavPosition position;
        bool selectable = true;  // false=纯功能项(不切换页面, 如User头像), 仅触发回调
    };

    QQmlEngine *m_engine;
    QString m_importPath;
    WindowType m_type;
    QObject *m_root = nullptr;
    QString m_title;
    QString m_windowIcon;
    bool m_windowIconColored = true;
    int m_width = 1000;
    int m_height = 700;
    QList<NavItem> m_navItems;          // 顶部导航
    QList<NavItem> m_bottomNavItems;    // 底部导航
    QHash<int, QObject *> m_pages;      // 已创建的页面实例
    QList<int> m_navHistory;            // 导航历史栈(页面索引), 供 goBack
    bool m_inGoBack = false;            // goBack 期间抑制历史压栈, 防自压
    bool m_built = false;
    NavBridge *m_navBridge = nullptr;
    // 启动画面(SplashScreen): 默认开启, 图标/标题空则回退 windowIcon/windowTitle
    bool m_splashEnabled = true;
    QString m_splashIcon, m_splashTitle, m_splashSubtitle;
    QObject *m_splashInstance = nullptr;

    void build();
    void createSplash();  // show() 后挂 SplashScreen 覆盖层到 contentItem
    void ensurePageCreated(int index);
    QQuickItem *findChildByName(const QString &name) const;
    void onCurrentPageChanged(int index);

    static QString escapeQml(const QString &text);
    static QString qmlComponentName(WindowType type);
    QString navItemsJson(const QList<NavItem> &items, int indexOffset, bool isBottom = false) const;
};

}  // namespace prism
