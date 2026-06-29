// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - Gallery: 纯 C++ 驱动的完整组件画廊。
// 不依赖 Python: 用 prism C++ 宿主的 addPage API 加载 examples/pages 的 13 个组件展示页,
// 让只用 C++ 的用户也能看到和 Python 版一样的组件画廊。
#include "prism/App.h"
#include "prism/Theme.h"

#include <QDebug>
#include <QDir>
#include <QString>
#include <QProcessEnvironment>
#include <QQuickWindow>
#include <QQmlApplicationEngine>
#include <QTimer>
#include <QImage>
#include <QCoreApplication>

int main(int argc, char *argv[]) {
    using namespace prism;

    App app(argc, argv);
    setSkin(Skin::Fluent);
    // 用 Fluent 默认 accent(沉稳深蓝 #0e5a9c), 不强设橙色(#F97316 是 Neobrutalism 主色)

#ifdef PRISM_QML_FROM_QRC
    app.engine()->addImportPath(QStringLiteral("qrc:/"));
    const QString pagesDir = QStringLiteral("qrc:/pages");
    const bool fromQrc = true;
#else
    const bool fromQrc = false;
    // 桌面: 页面 QML 磁盘目录。默认指向 examples/pages(与 Python gallery 共享同一份页面)。
    QString pagesDir = QProcessEnvironment::systemEnvironment()
                           .value(QStringLiteral("PRISM_GALLERY_PAGES"));
    if (pagesDir.isEmpty())
        pagesDir = QStringLiteral("D:/PrismQML/PrismQML/examples/pages");
#endif
    auto pagePath = [&](const QString &name) -> QString {
        if (fromQrc)
            return pagesDir + QLatin1Char('/') + name;
        return QDir(pagesDir).filePath(name);
    };

    Window &w = app.createWindow(WindowType::Bar);
    w.setWindowTitle(QStringLiteral("PrismQML Gallery (C++ 宿主)"));
    // 标题栏 app 图标 (桌面: examples/resources 磁盘路径; 可被 PRISM_GALLERY_ICON 覆盖)
    {
        QString iconUrl = QProcessEnvironment::systemEnvironment()
                              .value(QStringLiteral("PRISM_GALLERY_ICON"));
        if (iconUrl.isEmpty() && !fromQrc)
            iconUrl = QStringLiteral("file:///D:/PrismQML/PrismQML/examples/resources/app_icon.svg");
        else if (iconUrl.isEmpty() && fromQrc)
            iconUrl = QStringLiteral("qrc:/app_icon.svg");
        w.setWindowIcon(iconUrl, /*colored=*/true);
    }
    w.resize(1200, 800);

    // 启动画面(标题/图标回退到窗口配置)
    w.setSplash(/*enabled=*/true, QString(), QStringLiteral("PrismQML Gallery"),
                QStringLiteral("加载中..."));

    // 13 个组件展示页 (图标/标题对照 examples/main.qml 的 navItems)
    struct Page { const char *file; const char *icon; const char *title; };
    const Page pages[] = {
        {"ButtonPage.qml",     "CursorClick",       "按钮"},
        {"InputPage.qml",      "Keyboard",          "输入"},
        {"LabelPage.qml",      "Tag",               "标签"},
        {"CardPage.qml",       "CardUI",            "卡片"},
        {"CarouselPage.qml",   "SlideMultiple",     "轮播"},
        {"FeedbackPage.qml",   "Alert",             "反馈"},
        {"MenuPage.qml",       "Navigation",        "菜单"},
        {"NavigationPage.qml", "CompassNorthwest",  "导航"},
        {"ContainerPage.qml",  "LayoutRowFour",     "容器"},
        {"ChartPage.qml",      "DataPie",           "图表"},
        {"IconPage.qml",       "Icons",             "图标"},
        {"EffectsPage.qml",    "Sparkle",           "特效"},
        {"SettingsPage.qml",   "Settings",          "设置"},
    };
    int firstIdx = -1;
    for (const auto &p : pages) {
        int idx = w.addPage(pagePath(QString::fromUtf8(p.file)),
                            QString::fromUtf8(p.icon), QString::fromUtf8(p.title));
        if (firstIdx < 0) firstIdx = idx;
    }
    qInfo() << "Gallery: addPage x" << (int)(sizeof(pages) / sizeof(pages[0]))
            << "first idx =" << firstIdx;

    w.show();
    w.navigateTo(0);

    if (!w.isValid()) {
        qCritical() << "GALLERY_FAIL: 窗口创建失败";
        return 2;
    }
    qInfo() << "GALLERY_OK: prism C++ host loaded" << (int)(sizeof(pages) / sizeof(pages[0]))
            << "component pages";

    // PRISM_GRAB=<path>: 抓取窗口渲染存盘再退出 (验证非空白渲染)
    const QString grabPath = QProcessEnvironment::systemEnvironment()
                                 .value(QStringLiteral("PRISM_GRAB"));
    if (!grabPath.isEmpty()) {
        if (auto *qw = qobject_cast<QQuickWindow *>(w.rootObject())) {
            QTimer::singleShot(1200, [qw, grabPath]() {
                QImage img = qw->grabWindow();
                img.save(grabPath);
                qInfo() << "GALLERY_GRAB saved" << grabPath << img.size();
                QCoreApplication::quit();
            });
        }
    }

    return app.exec();
}
