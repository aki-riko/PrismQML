// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - Window 实现 (镜像 _window_builder.py + _page_manager.py)
#include "prism/Window.h"
#include "prism/Platform.h"
#include "prism/ConfigManager.h"
#include "prism/WindowHelper.h"

#include <QQmlEngine>
#include <QQmlComponent>
#include <QQmlContext>
#include <QObject>
#include <QQuickItem>
#include <QQuickWindow>
#include <QUrl>
#include <QDir>
#include <QStringList>
#include <QTimer>
#include <QDebug>
#include <functional>

namespace prism {

void NavBridge::onChanged(int index) {
    if (m_owner)
        m_owner->onCurrentPageChanged(index);
}

Window::Window(QQmlEngine *engine, const QString &importPath, WindowType type)
    : m_engine(engine), m_importPath(importPath), m_type(type) {}

Window::~Window() {
    if (m_root)
        m_root->deleteLater();
}

// 镜像 Python _escape_qml
QString Window::escapeQml(const QString &text) {
    QString t = text;
    t.replace(QLatin1String("\\"), QLatin1String("\\\\"));
    t.replace(QLatin1String("\""), QLatin1String("\\\""));
    t.replace(QLatin1String("\n"), QLatin1String("\\n"));
    t.replace(QLatin1String("\r"), QLatin1String("\\r"));
    t.replace(QLatin1String("\t"), QLatin1String("\\t"));
    t.replace(QLatin1String("{"), QLatin1String("\\u007B"));
    t.replace(QLatin1String("}"), QLatin1String("\\u007D"));
    return t;
}

QString Window::qmlComponentName(WindowType type) {
    switch (type) {
        case WindowType::Split:  return QStringLiteral("WindowsSplit");
        case WindowType::Bar:    return QStringLiteral("WindowsBar");
        case WindowType::Filled: return QStringLiteral("WindowsFilled");
    }
    return QStringLiteral("WindowsBar");
}

// addPage - 添加导航项 + 页面 (镜像 Python addPage), 必须在 show() 前
int Window::addPage(const QString &pageQmlUrl, const QString &icon,
                    const QString &text, NavPosition position) {
    if (m_built) {
        qWarning() << "prism::Window: addPage 必须在 show() 之前调用";
        return -1;
    }
    NavItem item{pageQmlUrl, icon, text, position};
    if (position == NavPosition::Bottom)
        m_bottomNavItems.append(item);
    else
        m_navItems.append(item);
    return m_navItems.size() + m_bottomNavItems.size() - 1;
}

// 把导航项拼成 QML 数组字面量
QString Window::navItemsJson(const QList<NavItem> &items, int indexOffset) const {
    QStringList parts;
    for (int i = 0; i < items.size(); ++i) {
        const NavItem &it = items.at(i);
        parts << QStringLiteral("{ \"text\": \"%1\", \"icon\": \"%2\", \"key\": \"page_%3\" }")
                     .arg(escapeQml(it.text), escapeQml(it.icon))
                     .arg(indexOffset + i);
    }
    return parts.join(QStringLiteral(", "));
}

void Window::setWindowTitle(const QString &title) {
    m_title = title;
    if (m_root)
        m_root->setProperty("windowTitle", title);
}

void Window::setWindowIcon(const QString &iconUrl, bool colored) {
    m_windowIcon = iconUrl;
    m_windowIconColored = colored;
    if (m_root) {
        m_root->setProperty("windowIcon", iconUrl);
        m_root->setProperty("windowIconColored", colored);
    }
    // 双保险(镜像 Python window_base.py): 宿主侧直接设 QGuiApplication 任务栏/Alt-Tab
    // 图标, 不只依赖 QML onWindowIconChanged 回调那一条路。
    if (!iconUrl.isEmpty())
        WindowHelper::instance()->setAppIcon(iconUrl);
}

void Window::resize(int width, int height) {
    m_width = width;
    m_height = height;
    if (m_root) {
        m_root->setProperty("width", width);
        m_root->setProperty("height", height);
    }
}

void Window::navigateTo(int index) {
    if (!m_root)
        return;
    // 主动懒加载目标页: QML 的 currentPageChanged 信号仅在【点击导航项】时发,
    // 编程式 navigateTo 只改 currentIndex 不发该信号, 故这里主动确保页面创建,
    // 不依赖信号 (信号路径仍由 NavBridge 处理 UI 点击场景)。
    ensurePageCreated(index);
    if (m_navHistory.isEmpty() || m_navHistory.last() != index)
        m_navHistory.append(index);
    QMetaObject::invokeMethod(m_root, "navigateTo", Q_ARG(QVariant, QVariant(index)));
}

void Window::build() {
    // Android: m_importPath 为 "qrc:/" → qmlDir="qrc:/PrismQML", import 用 qrc 前缀
    // 桌面: m_importPath 为磁盘路径 → file:/// 前缀
    const bool isQrc = m_importPath.startsWith(QStringLiteral("qrc:"));
    QString qmlDir;
    QString importPrefix;
    if (isQrc) {
        qmlDir = QStringLiteral("qrc:/PrismQML");
        importPrefix = QString();  // qrc: 路径直接用, 无 file:/// 前缀
    } else {
        qmlDir = QDir(m_importPath).filePath(QStringLiteral("PrismQML"));
        qmlDir = QDir::fromNativeSeparators(qmlDir);
        importPrefix = QStringLiteral("file:///");
    }
    const QString component = qmlComponentName(m_type);

    // 顶部导航项索引 0..N-1, 底部导航项索引接续 (与 page_N 容器一致)
    const QString navJson = navItemsJson(m_navItems, 0);
    const QString bottomJson = navItemsJson(m_bottomNavItems, m_navItems.size());

    // 为每个导航项生成 page_N 占位容器 (镜像 _window_builder page_items)
    const int total = m_navItems.size() + m_bottomNavItems.size();
    QString pagesQml;
    for (int i = 0; i < total; ++i) {
        pagesQml += QStringLiteral(
            "    Item { id: page_%1; objectName: \"page_%1\"; "
            "width: parent ? parent.width : 0; height: parent ? parent.height : 0 }\n")
            .arg(i);
    }

    // windowIcon: 标题栏 app 图标。未显式设则回退内置 Apps.svg(镜像 Python, 保证
    // windowIcon 永远非空 → 触发 onWindowIconChanged → 任务栏图标也有)。
    // 必须拼进 QML 字面量(同 windowTitle), 因 m_root 在 show()->build() 时才创建。
    QString effectiveIcon = m_windowIcon;
    if (effectiveIcon.isEmpty()) {
        effectiveIcon = (isQrc ? QStringLiteral("qrc:/PrismQML/controls/icons/fluent/Apps.svg")
                               : importPrefix + qmlDir + QStringLiteral("/controls/icons/fluent/Apps.svg"));
    }
    const QString iconQml =
        QStringLiteral("    windowIcon: \"%1\"\n    windowIconColored: %2\n")
            .arg(escapeQml(effectiveIcon),
                 m_windowIconColored ? QStringLiteral("true") : QStringLiteral("false"));

    // 消费 ConfigManager 设置 (镜像 Python _window_builder): mica 效果 + DWM 阴影模式。
    auto *cfg = ConfigManager::instance();
    const QString micaQml = QStringLiteral("    micaEnabled: %1\n")
                                .arg(cfg->micaEnabled() ? QStringLiteral("true") : QStringLiteral("false"));
    // shadowMode: dwmShadow 配置 → mode_native(1) / mode_none(3)
    const QString shadowQml = QStringLiteral("    shadowMode: %1\n")
                                  .arg(cfg->dwmShadow() ? 1 : 3);
    const QString extraQml = iconQml + micaQml + shadowQml;

    const QString qml = QStringLiteral(
        "import QtQuick\n"
        "import \"%1\"\n"
        "import \"%1/_internal\"\n"
        "\n"
        "%2 {\n"
        "    id: window\n"
        "    objectName: \"mainWindow\"\n"
        "    width: %3\n"
        "    height: %4\n"
        "    windowTitle: \"%5\"\n"
        "%9"
        "    lazyLoading: false\n"
        "    navigationItems: [%6]\n"
        "    bottomNavigationItems: [%7]\n"
        "%8"
        "}\n"
    ).arg(importPrefix + qmlDir, component)
     .arg(m_width).arg(m_height)
     .arg(escapeQml(m_title), navJson, bottomJson, pagesQml)
     .arg(extraQml);

    auto *comp = new QQmlComponent(m_engine);
    comp->setData(qml.toUtf8(), QUrl(QStringLiteral("inline-prism-window")));
    if (comp->isError()) {
        qWarning() << "prism::Window 加载失败:";
        for (const auto &e : comp->errors())
            qWarning().noquote() << "  " << e.toString();
        comp->deleteLater();
        return;
    }
    m_root = comp->create();
    if (!m_root) {
        qWarning() << "prism::Window create() 返回空";
        for (const auto &e : comp->errors())
            qWarning().noquote() << "  " << e.toString();
        comp->deleteLater();
        return;
    }
    comp->setParent(m_root);
    m_built = true;

    // 连接 currentPageChanged 信号 -> 懒加载页面 (镜像 _on_nav_changed)
    // QML 定义的信号无 C++ PMF, 用 NavBridge(带 slot 的 QObject)中转。
    if (!m_navBridge)
        m_navBridge = new NavBridge(this, m_root);
    QObject::connect(m_root, SIGNAL(currentPageChanged(int)),
                     m_navBridge, SLOT(onChanged(int)));
    // 返回键/关闭请求 -> NavBridge::onClosing (移动端返回键弹栈)
    QObject::connect(m_root, SIGNAL(closing(QQuickCloseEvent*)),
                     m_navBridge, SLOT(onClosing(QQuickCloseEvent*)));

    // 立即创建第 0 页 (默认显示页) + 初始压入导航历史
    if (total > 0) {
        ensurePageCreated(0);
        m_navHistory.append(0);
    }
}

void Window::onCurrentPageChanged(int index) {
    ensurePageCreated(index);
    // 压入导航历史(供返回键 goBack); goBack 期间不压, 连续重复同页不重复压
    if (!m_inGoBack && (m_navHistory.isEmpty() || m_navHistory.last() != index))
        m_navHistory.append(index);
}

// goBack - 返回上一页 (移动端返回键): 弹掉当前页, 导航到历史前一页。
// 返回 false 表示历史栈已空(只剩当前/为空), 调用方应退出 App。
bool Window::goBack() {
    if (m_navHistory.size() <= 1)
        return false;  // 无更早历史, 应退出
    m_navHistory.removeLast();          // 弹掉当前页
    const int prev = m_navHistory.last();
    if (m_root) {
        ensurePageCreated(prev);
        m_inGoBack = true;  // 抑制本次切换的历史压栈(防自压)
        QMetaObject::invokeMethod(m_root, "navigateTo", Q_ARG(QVariant, QVariant(prev)));
        m_inGoBack = false;
    }
    return true;
}

void NavBridge::onClosing(QQuickCloseEvent *event) {
    // Android 返回键触发窗口 closing: 能 goBack 则拦截(不关窗), 否则放行(退出)。
    // QQuickCloseEvent 公开头仅前向声明, 但它单继承 QObject 且 accepted 是
    // Q_PROPERTY → 经 QObject* 用 setProperty 设置, 避免依赖私有头。
    if (m_owner && m_owner->goBack()) {
        if (event)
            reinterpret_cast<QObject *>(event)->setProperty("accepted", false);
    }
}

// 确保页面已创建并挂入 page_N 容器 (镜像 _create_page)
void Window::ensurePageCreated(int index) {
    if (m_pages.contains(index))
        return;
    const int topN = m_navItems.size();
    const NavItem *item = nullptr;
    if (index < topN)
        item = &m_navItems[index];
    else if (index - topN < m_bottomNavItems.size())
        item = &m_bottomNavItems[index - topN];
    if (!item || item->pageQmlUrl.isEmpty())
        return;  // 纯功能项无页面

    QQuickItem *container = findChildByName(QStringLiteral("page_%1").arg(index));
    if (!container) {
        qWarning() << "prism::Window: 未找到页面容器 page_" << index;
        return;
    }

    // 加载页面 QML 组件
    // qrc:/ (Android资源) 或含 scheme:// 的用 QUrl 直接构造, 否则当本地磁盘路径
    QUrl url = (item->pageQmlUrl.startsWith(QStringLiteral("qrc:"))
                || item->pageQmlUrl.contains(QStringLiteral("://")))
                   ? QUrl(item->pageQmlUrl)
                   : QUrl::fromLocalFile(item->pageQmlUrl);
    auto *comp = new QQmlComponent(m_engine, url);
    if (comp->isError()) {
        qWarning() << "prism::Window: 页面加载失败 page_" << index;
        for (const auto &e : comp->errors())
            qWarning().noquote() << "  " << e.toString();
        comp->deleteLater();
        return;
    }
    QObject *pageObj = comp->create();
    auto *pageItem = qobject_cast<QQuickItem *>(pageObj);
    if (!pageItem) {
        qWarning() << "prism::Window: 页面根非 Item page_" << index;
        if (pageObj) pageObj->deleteLater();
        comp->deleteLater();
        return;
    }
    comp->setParent(pageItem);
    pageItem->setParentItem(container);
    // 绑定尺寸到容器 (镜像 Python bind_size)
    pageItem->setWidth(container->width());
    pageItem->setHeight(container->height());
    QObject::connect(container, &QQuickItem::widthChanged, pageItem,
                     [pageItem, container]() { pageItem->setWidth(container->width()); });
    QObject::connect(container, &QQuickItem::heightChanged, pageItem,
                     [pageItem, container]() { pageItem->setHeight(container->height()); });

    m_pages.insert(index, pageItem);
    qDebug().noquote() << "prism::Window 页面已创建 page_" << index
                       << "from" << item->pageQmlUrl;
}

// 递归按 objectName 查找子项 (镜像 _find_child_by_name)
QQuickItem *Window::findChildByName(const QString &name) const {
    if (!m_root)
        return nullptr;
    auto *win = qobject_cast<QQuickWindow *>(m_root);
    QQuickItem *root = win ? win->contentItem() : nullptr;
    if (!root)
        return nullptr;
    std::function<QQuickItem *(QQuickItem *)> findRec = [&](QQuickItem *it) -> QQuickItem * {
        if (it->objectName() == name)
            return it;
        for (QQuickItem *child : it->childItems()) {
            if (QQuickItem *r = findRec(child))
                return r;
        }
        return nullptr;
    };
    return findRec(root);
}

void Window::show() {
    if (!m_built)
        build();
    if (!m_root)
        return;
#if PRISM_MOBILE
    // 移动端: 全屏单窗口 (无边框/标题栏概念)
    // QWindow::Visibility::FullScreen = 5
    m_root->setProperty("visibility", 5);
#else
    m_root->setProperty("visible", true);
#endif
}

}  // namespace prism
