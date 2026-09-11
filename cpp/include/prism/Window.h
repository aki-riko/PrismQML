// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - Window 门面 (镜像 Python window/window_core.py + _page_manager.py)
#pragma once

#include <QString>
#include <QList>
#include <QHash>
#include <QObject>
#include <functional>

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
    void onBottomItemClicked(int index);  // 底部导航项点击(含纯功能项) -> 用户回调
    void onCaptionActionTriggered();  // 通用标题栏动作 -> 用户回调
    void onClosing(QQuickCloseEvent *event);  // 原生关闭请求 -> goBack / 用户回调 / 放行
    void onCloseRequested();  // QML requestClose() -> 用户回调 (无原生关闭事件)
private:
    Window *m_owner;
};

// WindowCloseEvent - 可取消的关闭事件 (镜像 Python window_core.py WindowCloseEvent)
//
// 默认接受关闭; 宿主可 ignore() 取消这次关闭让窗口继续存活。requestHideOnClose()
// 声明这次已接受的关闭要「带动画隐藏而非销毁」(收进托盘): 关闭动画照播, 收尾时
// 隐藏窗口并复位关闭状态, 之后仍可再次 show/close。
//
// 与 Python 的差异(有意, 不改既有行为):
//   Python 的 closeEvent 写回 closeRequestAccepted 是同步的, 因此宿主可以在
//   closeEvent 返回「之后」再改 accepted; C++ 侧写回紧随 closeEvent 返回执行,
//   故取消关闭必须在 closeEvent 内直接调用 ignore()。
class WindowCloseEvent {
public:
    explicit WindowCloseEvent(QObject *target = nullptr);

    bool isAccepted() const { return m_accepted; }
    // 仅当事件已被接受时生效: 被取消的关闭不会隐藏窗口。
    bool hideOnCloseRequested() const { return m_accepted && m_hideOnClose; }

    void accept() { m_accepted = true; }
    void ignore() { m_accepted = false; }
    void requestHideOnClose();

    QObject *targetObject() const { return m_target; }

private:
    QObject *m_target = nullptr;
    bool m_accepted = true;
    bool m_hideOnClose = false;
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
    void setTranslatedWindowTitle(const QString &translationKey);
    // setWindowIcon - 设置标题栏 app 图标 (镜像 Python windowIcon 属性)
    // iconUrl: 图标路径(qrc:/file:/磁盘路径或图标名); colored: true=彩色图标跳过着色叠加。
    void setWindowIcon(const QString &iconUrl, bool colored = true);
    // setCaptionAction - 配置系统按钮左侧的通用标题栏动作。
    // 引擎只负责位置与样式，动作语义由宿主通过回调决定；icon 为空时隐藏。
    void setCaptionAction(const QString &icon, const QString &toolTip = QString(),
                          bool enabled = true, bool visible = true);
    void clearCaptionAction();
    void resize(int width, int height);

    // addPage - 添加页面 (镜像 Python addPage)
    // pageQmlUrl: 页面 QML 文件路径(本地路径或 qrc/file url); 空则为纯功能导航项。
    // selectable: false=纯功能项(点击只触发回调不切页, 如底部 User 头像)。
    // visible: false=保留页面索引但不在导航呈现层显示。
    // 返回页面索引。必须在 show() 之前调用。
    int addPage(const QString &pageQmlUrl, const QString &icon,
                const QString &text, NavPosition position = NavPosition::Top,
                bool selectable = true, bool visible = true);
    int addTranslatedPage(const QString &pageQmlUrl, const QString &icon,
                          const QString &translationKey,
                          NavPosition position = NavPosition::Top,
                          bool selectable = true, bool visible = true);

    // setSplash - 配置启动画面 (镜像 Python setSplash)。show() 前调用。
    // 默认开启, icon/title 空则回退 windowIcon/windowTitle。enabled=false 禁用。
    void setSplash(bool enabled, const QString &icon = QString(),
                   const QString &title = QString(), const QString &subtitle = QString());
    void setTranslatedSplash(bool enabled, const QString &icon = QString(),
                             const QString &titleKey = QString(),
                             const QString &subtitleKey = QString());

    // onBottomItemClicked - 底部导航项点击回调 (镜像 QML bottomItemClicked 信号)。
    // 纯功能项(selectable=false, 如 User 头像)点击时触发, 参数为该项的索引;
    // 可选页面项点击也会触发(切页由框架处理, 回调用于额外响应)。
    void onBottomItemClicked(std::function<void(int)> cb);
    // onCaptionActionTriggered - 通用标题栏动作点击回调。
    void onCaptionActionTriggered(std::function<void()> cb);
    // onClosing - 关闭请求回调 (镜像 Python WindowCore.closeEvent)。
    // 用户点关闭按钮、系统关闭或 QML requestClose() 送达时触发, 此时窗口尚未开始
    // 收尾: 调用 event.ignore() 可取消关闭并让窗口继续存活; 调用
    // event.requestHideOnClose() 可让这次已接受的关闭以「带动画隐藏」收尾
    // (收进托盘), 窗口之后仍可再次显示与关闭。未设置回调时保持既有行为(直接关闭)。
    void onClosing(std::function<void(WindowCloseEvent &)> cb);

    void show();
    void navigateTo(int index);

    // goBack - 返回导航历史上一页 (移动端返回键惯例)。
    // 返回 true=已弹栈到上一页; false=历史栈空(调用方应退出 App)。
    bool goBack();
    bool canGoBack() const { return m_navHistory.size() > 1; }
    bool hasPreviousPage() const { return m_navHistory.size() > 1; }

    QObject *rootObject() const { return m_root; }
    bool isValid() const { return m_root != nullptr; }

private:
    friend class NavBridge;
    struct NavItem {
        QString pageQmlUrl;
        QString icon;
        QString text;
        bool translated = false;
        NavPosition position;
        bool selectable = true;  // false=纯功能项(不切换页面, 如User头像), 仅触发回调
        bool visible = true;    // false=保留页面索引但不在导航呈现层显示
    };

    QQmlEngine *m_engine;
    QString m_importPath;
    WindowType m_type;
    QObject *m_root = nullptr;
    QString m_title;
    bool m_titleTranslated = false;
    QString m_windowIcon;
    bool m_windowIconColored = true;
    QString m_captionActionIcon;
    QString m_captionActionToolTip;
    bool m_captionActionEnabled = true;
    bool m_captionActionVisible = false;
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
    bool m_splashTitleTranslated = false;
    bool m_splashSubtitleTranslated = false;
    std::function<void(int)> m_onBottomItemClicked;  // 底部项点击回调
    std::function<void()> m_onCaptionActionTriggered;  // 标题栏动作回调
    std::function<void(WindowCloseEvent &)> m_onClosing;  // 关闭请求回调

    void build();
    void handleBottomItemClicked(int localIndex);  // NavBridge 转发的底部项点击(局部索引→全局)
    void handleCaptionActionTriggered();  // NavBridge 转发的通用标题栏动作
    // 分发一次关闭请求给所有回调并写回 QML 决定, 返回事件是否仍被接受。
    bool dispatchClose(WindowCloseEvent &event);
    void ensurePageCreated(int index);
    QQuickItem *findChildByName(const QString &name) const;
    void onCurrentPageChanged(int index);

    static QString escapeQml(const QString &text);
    static QString qmlTextExpression(const QString &text, bool translated);
    static QString qmlComponentName(WindowType type);
    QString navItemsJson(const QList<NavItem> &items, int indexOffset, bool isBottom = false) const;
};

// WindowCore - 窗口核心类型别名 (镜像 Python window_core.py 的 WindowCore)。
// Python 中 WindowCore 是核心实现 (QObject+Builder+PageManager mixin), Window 是其门面;
// C++ 侧 Window 已内聚全部门面+核心逻辑, WindowCore 作为对称别名指向同一类型,
// 使 prism::WindowCore 可与 Python 逐字对称引用。
using WindowCore = Window;

}  // namespace prism
