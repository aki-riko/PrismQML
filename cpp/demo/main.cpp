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

#ifdef PRISM_QML_FROM_QRC
    // Android: QML 从 qrc 资源加载 (addImportPath qrc:/ 找 qrc:/PrismQML/qmldir)
    app.engine()->addImportPath(QStringLiteral("qrc:/"));
    const QString pagesDir = QStringLiteral("qrc:/pages");
    const bool fromQrc = true;
#else
    const bool fromQrc = false;
#endif

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

#ifndef PRISM_QML_FROM_QRC
    // 桌面: 页面 QML 磁盘目录。优先 PRISM_DEMO_PAGES 环境变量, 否则用编译期注入的
    // 源码树默认(CMake 定义 PRISM_DEMO_PAGES_DIR), 使无需手动设环境变量即可运行。
    QString pagesDir = QProcessEnvironment::systemEnvironment()
                           .value(QStringLiteral("PRISM_DEMO_PAGES"));
#ifdef PRISM_DEMO_PAGES_DIR
    if (pagesDir.isEmpty())
        pagesDir = QStringLiteral(PRISM_DEMO_PAGES_DIR);
#endif
#endif
    // 统一页面路径: Android 用 qrc, 桌面用磁盘
    auto pagePath = [&](const QString &name) -> QString {
        if (fromQrc)
            return pagesDir + QLatin1Char('/') + name;       // qrc:/pages/Name.qml
        return QDir(pagesDir).filePath(name);                // 磁盘绝对路径
    };

    Window &w = app.createWindow(WindowType::Bar);
    w.setWindowTitle(QStringLiteral("PrismQML C++ 宿主 Demo"));
    w.resize(1200, 800);

    // 对称 API: addPage(页面QML, 图标, 文本)
    int home = w.addPage(pagePath(QStringLiteral("HomePage.qml")),
                         QStringLiteral("Home"), QStringLiteral("首页"));
    int data = w.addPage(pagePath(QStringLiteral("DataPage.qml")),
                         QStringLiteral("People"), QStringLiteral("用户"));
    int settings = w.addPage(pagePath(QStringLiteral("SettingsPage.qml")),
                             QStringLiteral("Settings"), QStringLiteral("设置"));
    int resp = w.addPage(pagePath(QStringLiteral("ResponsivePage.qml")),
                         QStringLiteral("ResizeLarge"), QStringLiteral("响应式"));
    qInfo() << "addPage -> home" << home << "data" << data << "settings" << settings
            << "responsive" << resp;

    if (!w.isValid() && (home < 0)) {
        // isValid 在 show() 前为 false 属正常; 这里仅占位
    }

    // 移动端生命周期演示: 切后台/回前台时回调 (真机切走/锁屏触发)
    app.onPause([]() { qInfo() << "LIFECYCLE: onPause (app 进入后台)"; });
    app.onResume([]() { qInfo() << "LIFECYCLE: onResume (app 回到前台)"; });

    w.show();

    // 启动时导航建立历史 (演示返回键弹栈 + 响应式页含输入框测软键盘)
    w.navigateTo(1);
    w.navigateTo(3);

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
