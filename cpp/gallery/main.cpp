// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - Gallery: 纯 C++ 驱动的完整组件画廊。
// 不依赖 Python: 用 prism C++ 宿主的 addPage API 加载 examples/pages 的 13 个组件展示页,
// 让只用 C++ 的用户也能看到和 Python 版一样的组件画廊。
#include "prism/App.h"
#include "prism/ConfigManager.h"
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

    App app(argc, argv, QString(), true, resolveConfigFilePath(), true);
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

    Window &w = app.createWindow(
        static_cast<WindowType>(ConfigManager::instance()->windowType()));
    w.setTranslatedWindowTitle(QStringLiteral("gallery_90b8157cfce0dbe5"));
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
    // Demonstrate the engine-level generic caption action with an AI icon.
    // 用 AI 图标展示引擎级通用标题栏动作能力。
    w.setCaptionAction(QStringLiteral("Bot"), QStringLiteral("AI"));
    w.onCaptionActionTriggered([]() {
        qInfo() << "GALLERY_CAPTION_ACTION_TRIGGERED";
    });
    w.resize(1200, 800);

    // 启动画面(标题/图标回退到窗口配置)
    w.setTranslatedSplash(/*enabled=*/true, QString(),
                          QStringLiteral("gallery_8b6903f932b56197"),
                          QStringLiteral("loading"));

    // 13 个组件展示页 (图标/标题对照 examples/main.qml 的 navItems)
    struct Page { const char *file; const char *icon; const char *titleKey; };
    const Page pages[] = {
        {"ButtonPage.qml",     "CursorClick",       "gallery_ad1c50c9367c756d"},
        {"InputPage.qml",      "Keyboard",          "gallery_2087c777c06fefe5"},
        {"LabelPage.qml",      "Tag",               "gallery_1d0fd5f9336d9103"},
        {"CardPage.qml",       "CardUI",            "gallery_fb5640f8e12e3337"},
        {"CarouselPage.qml",   "SlideMultiple",     "gallery_85f05ecc2a4f3f5d"},
        {"FeedbackPage.qml",   "Alert",             "gallery_8b2106ca13719cb2"},
        {"MenuPage.qml",       "Navigation",        "gallery_4ce4cafdd0561280"},
        {"NavigationPage.qml", "CompassNorthwest",  "gallery_e72622fe470d04bc"},
        {"ContainerPage.qml",  "LayoutRowFour",     "gallery_6d23f04b26967d64"},
        {"ChartPage.qml",      "DataPie",           "gallery_8cb443ab83797881"},
        {"IconPage.qml",       "Icons",             "gallery_0d720eeea26466dd"},
        {"EffectsPage.qml",    "Sparkle",           "gallery_8829dbcbcfce6e54"},
        {"SettingsPage.qml",   "Settings",          "gallery_df3d58c7d84b85f2"},
    };
    int firstIdx = -1;
    for (const auto &p : pages) {
        int idx = w.addTranslatedPage(
            pagePath(QString::fromUtf8(p.file)), QString::fromUtf8(p.icon),
            QString::fromUtf8(p.titleKey));
        if (firstIdx < 0) firstIdx = idx;
    }
    qInfo() << "Gallery: addPage x" << (int)(sizeof(pages) / sizeof(pages[0]))
            << "first idx =" << firstIdx;

    // 纯功能底部项(selectable=false): 点击不切页, 触发 onBottomItemClicked 回调
    // (演示导航项的功能项能力, 如 User 头像点击弹菜单)
    const int aboutIdx = w.addTranslatedPage(
        QString(), QStringLiteral("Person"),
        QStringLiteral("gallery_52d25a9e30ba94f1"), NavPosition::Bottom,
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
