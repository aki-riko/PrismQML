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
#include "prism/Store.h"
#include "prism/SqlListModel.h"

#include <QDebug>
#include <QDir>
#include <QString>
#include <QProcessEnvironment>
#include <QQuickWindow>
#include <QQmlContext>
#include <QQmlApplicationEngine>
#include <QImage>
#include <QTimer>
#include <QSqlDatabase>
#include <QSqlQuery>
#include <QFile>

// 建一个临时 SQLite 作 demo 数据源, 返回路径
static QString seedDemoDb() {
    const QString dbPath = QDir::tempPath() + "/prism_demo.db";
    QFile::remove(dbPath);
    QSqlDatabase db = QSqlDatabase::addDatabase("QSQLITE", "demo_seed");
    db.setDatabaseName(dbPath);
    db.open();
    QSqlQuery q(db);
    q.exec("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, role TEXT)");
    const char *names[] = {"Alice", "Bob", "Carol", "Dave", "Eve",
                           "Frank", "Grace", "Heidi", "Ivan", "Judy"};
    const char *roles[] = {"管理员", "用户", "访客"};
    for (int i = 0; i < 10; ++i)
        q.exec(QString("INSERT INTO users(id,name,role) VALUES(%1,'%2','%3')")
                   .arg(i + 1).arg(names[i]).arg(roles[i % 3]));
    db.close();
    QSqlDatabase::removeDatabase("demo_seed");
    return dbPath;
}

int main(int argc, char *argv[]) {
    using namespace prism;

    App app(argc, argv);
    setSkin(Skin::Fluent);
    setAccentColor("#F97316");
    qInfo() << "skin =" << skinToString(getSkin())
            << "accent =" << getAccentColor() << "isDark =" << isDark();

    // 注入应用级 Store + SqlListModel 给 QML (用 App 的 engine() 逃生口)
    static Store appStore(QStringLiteral("demoStore"));
    appStore.define(QStringLiteral("clicks"), 0);
    app.engine()->rootContext()->setContextProperty(
        QStringLiteral("AppStore"), appStore.qtSignals());  // 信号桥给 QML 绑定

    static SqlListModel userModel;
    if (userModel.openDatabase(seedDemoDb())) {
        userModel.setQuery(QStringLiteral("SELECT id, name, role FROM users ORDER BY id"),
                           QStringLiteral("SELECT COUNT(*) FROM users"));
        qInfo() << "SqlListModel 行数 =" << userModel.count();
    }
    app.engine()->rootContext()->setContextProperty(QStringLiteral("UserModel"), &userModel);

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
    int data = w.addPage(QDir(pagesDir).filePath(QStringLiteral("DataPage.qml")),
                         QStringLiteral("People"), QStringLiteral("用户"));
    int settings = w.addPage(QDir(pagesDir).filePath(QStringLiteral("SettingsPage.qml")),
                             QStringLiteral("Settings"), QStringLiteral("设置"));
    int resp = w.addPage(QDir(pagesDir).filePath(QStringLiteral("ResponsivePage.qml")),
                         QStringLiteral("ResizeLarge"), QStringLiteral("响应式"));
    qInfo() << "addPage -> home" << home << "data" << data << "settings" << settings
            << "responsive" << resp;

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
            w.navigateTo(1);  // 切到 DataPage 验证页面懒加载+SqlListModel渲染
            QObject *rootObj = w.rootObject();
            QTimer::singleShot(1800, [qw, grabPath, rootObj]() {
                // 诊断: Loader 异步加载完后查导航 visible (验证响应式导航切换)
                QObject *bt = rootObj->findChild<QObject *>(QStringLiteral("bottomTabBar"));
                QObject *nb = rootObj->findChild<QObject *>(QStringLiteral("navigationBar"));
                qInfo() << "NAV_DIAG bottomTabBar.visible ="
                        << (bt ? bt->property("visible").toBool() : false)
                        << "navigationBar.visible ="
                        << (nb ? nb->property("visible").toBool() : false)
                        << "(bt:" << (bt != nullptr) << "nb:" << (nb != nullptr) << ")";
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
