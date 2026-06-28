// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - demo: 对称 API 多页面应用
// 对照 Python README:
//   app=App(); w=app.create_window(WindowType.BAR)
//   w.addPage(HomePage,"Home","首页"); w.addPage(SettingsPage,"Settings","设置"); w.show()
#include "prism/App.h"
#include "prism/Theme.h"

#include <QDebug>
#include <QDir>
#include <QString>
#include <QProcessEnvironment>
#include <QQuickWindow>
#include <QImage>
#include <QTimer>

int main(int argc, char *argv[]) {
    using namespace prism;

    App app(argc, argv);
    setSkin(Skin::Fluent);
    setAccentColor("#F97316");
    qInfo() << "skin =" << skinToString(getSkin())
            << "accent =" << getAccentColor() << "isDark =" << isDark();

    // 页面 QML 目录: 环境变量 PRISM_DEMO_PAGES, fallback 到源码相对路径
    QString pagesDir = QProcessEnvironment::systemEnvironment()
                           .value(QStringLiteral("PRISM_DEMO_PAGES"));
    if (pagesDir.isEmpty())
        pagesDir = QStringLiteral("D:/PrismQML/PrismQML/cpp/demo/pages");

    Window &w = app.createWindow(WindowType::Bar);
    w.setWindowTitle(QStringLiteral("PrismQML C++ 宿主 Demo"));
    w.resize(1200, 800);

    // 对称 API: addPage(页面QML, 图标, 文本)
    int home = w.addPage(QDir(pagesDir).filePath(QStringLiteral("HomePage.qml")),
                         QStringLiteral("Home"), QStringLiteral("首页"));
    int settings = w.addPage(QDir(pagesDir).filePath(QStringLiteral("SettingsPage.qml")),
                             QStringLiteral("Settings"), QStringLiteral("设置"));
    qInfo() << "addPage -> home index" << home << ", settings index" << settings;

    if (!w.isValid() && (home < 0)) {
        // isValid 在 show() 前为 false 属正常; 这里仅占位
    }

    w.show();

    if (!w.isValid()) {
        qCritical() << "DEMO_FAIL: 窗口创建失败";
        return 2;
    }
    qInfo() << "DEMO_OK: prism::Window with pages created via C++ host";

    // PRISM_GRAB=<path>: 真实平台下延迟抓取窗口渲染存盘再退出 (验证非空白渲染)
    const QString grabPath = QProcessEnvironment::systemEnvironment()
                                 .value(QStringLiteral("PRISM_GRAB"));
    if (!grabPath.isEmpty()) {
        if (auto *qw = qobject_cast<QQuickWindow *>(w.rootObject())) {
            QTimer::singleShot(1500, [qw, grabPath]() {
                QImage img = qw->grabWindow();
                if (!img.isNull() && img.save(grabPath))
                    qInfo().noquote() << "PRISM_GRABBED" << grabPath
                                      << img.width() << "x" << img.height();
                else
                    qWarning() << "PRISM_GRAB_FAIL";
                QCoreApplication::exit(0);
            });
        }
    }
    return app.exec();
}
