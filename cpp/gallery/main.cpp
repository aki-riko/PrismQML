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
    // 桌面: 页面 QML 磁盘目录。优先 PRISM_GALLERY_PAGES 环境变量, 否则用编译期注入的
    // 源码树默认(CMake 定义 PRISM_GALLERY_PAGES_DIR), 使无需手动设环境变量即可运行。
    QString pagesDir = QProcessEnvironment::systemEnvironment()
                           .value(QStringLiteral("PRISM_GALLERY_PAGES"));
#ifdef PRISM_GALLERY_PAGES_DIR
    if (pagesDir.isEmpty())
        pagesDir = QStringLiteral(PRISM_GALLERY_PAGES_DIR);
#endif
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
#ifdef PRISM_GALLERY_ICON_DEFAULT
        if (iconUrl.isEmpty() && !fromQrc)
            iconUrl = QStringLiteral("file:///") + QStringLiteral(PRISM_GALLERY_ICON_DEFAULT);
#endif
        if (iconUrl.isEmpty() && fromQrc)
            iconUrl = QStringLiteral("qrc:/app_icon.svg");
        if (!iconUrl.isEmpty())
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

    // 纯功能底部项(selectable=false): 点击不切页, 触发 onBottomItemClicked 回调
    // (演示导航项的功能项能力, 如 User 头像点击弹菜单)
    const int aboutIdx = w.addPage(QString(), QStringLiteral("Person"),
                                   QStringLiteral("关于"), NavPosition::Bottom,
                                   /*selectable=*/false);
    w.onBottomItemClicked([aboutIdx](int index) {
        if (index == aboutIdx)
            qInfo() << "GALLERY_FUNC_ITEM_CLICKED: 纯功能项'关于'被点击(未切页) index=" << index;
        else
            qInfo() << "GALLERY_BOTTOM_CLICKED: 底部项 index=" << index;
    });

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

    // PRISM_GALLERY_TEST_GOBACK=1: 自测返回键 goBack (桌面无返回键, 编程式验证历史栈)。
    // 序列: navigateTo(2)→(5)→goBack 应回页5的前一个即页2, 再 goBack 回页0。
    if (QProcessEnvironment::systemEnvironment()
            .value(QStringLiteral("PRISM_GALLERY_TEST_GOBACK")) == QStringLiteral("1")) {
        QTimer::singleShot(500, [&w]() {
            w.navigateTo(2);
            w.navigateTo(5);
            qInfo() << "GOBACK_TEST: 导航 0→2→5, canGoBack=" << w.canGoBack();
            const bool r1 = w.goBack();  // 应回 2
            qInfo() << "GOBACK_TEST: goBack() =" << r1 << "(期望true, 回页2)";
            const bool r2 = w.goBack();  // 应回 0
            qInfo() << "GOBACK_TEST: goBack() =" << r2 << "(期望true, 回页0)";
            const bool r3 = w.goBack();  // 历史空, 应false
            qInfo() << "GOBACK_TEST: goBack() =" << r3 << "(期望false, 历史栈空)";
            qInfo() << (r1 && r2 && !r3 ? "GOBACK_TEST_PASS" : "GOBACK_TEST_FAIL");
            QCoreApplication::quit();
        });
    }

    return app.exec();
}
