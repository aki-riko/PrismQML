// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - SystemTray/SingleInstance 运行时烟测 (需 QApplication)
#include "prism/SystemTray.h"
#include "prism/SingleInstance.h"
#include "prism/WindowHelper.h"
#include "../src/IconPath_p.h"
#include "TestProcess.h"

#include <QApplication>
#include <QColor>
#include <QDebug>
#include <QDir>
#include <QGuiApplication>
#include <QImage>
#include <QIcon>
#include <QSystemTrayIcon>
#include <QPoint>
#include <QScreen>
#include <QTemporaryDir>
#include <QUrl>
#include <QVariantMap>
#include <QStringList>

static int g_failed = 0;
#define CHECK(cond, name) do { \
    if (cond) qInfo() << "  PASS:" << name; \
    else { qCritical() << "  FAIL:" << name; ++g_failed; } \
} while (0)

static void testIconPathUrlMatrix() {
    using prism::detail::resolveIconPath;
    const QStringList fileUrls = {
        QStringLiteral("file:///C:/Icons/A%20B/%23mark%25.png"),
        QStringLiteral("file://server/share/A%20B/%23mark.png"),
        QStringLiteral("file:///home/user/A%20B/%23mark%25%3F.svg"),
    };
    bool fileUrlsMatchQt = true;
    for (const QString &source : fileUrls)
        fileUrlsMatchQt &= resolveIconPath(source) == QUrl(source).toLocalFile();
    CHECK(fileUrlsMatchQt, "file URLs follow QUrl::toLocalFile");
    CHECK(resolveIconPath(QStringLiteral("qrc:///icons/A%20B.svg"))
              == QStringLiteral(":/icons/A B.svg"),
          "qrc variants normalize");
}

static void testRealEncodedIcon() {
    using prism::detail::resolveIconPath;
    QTemporaryDir directory(
        QDir::tempPath() + QStringLiteral("/prismqml-p7k-XXXXXX"));
    const QString path = directory.filePath(QStringLiteral("图 标#百分%.png"));
    QImage image(8, 8, QImage::Format_ARGB32);
    image.fill(QColor(QStringLiteral("#d02040")));
    CHECK(directory.isValid() && image.save(path), "real encoded icon fixture saved");
    const QString source = QUrl::fromLocalFile(path).toString(QUrl::FullyEncoded);
    CHECK(resolveIconPath(source) == QUrl(source).toLocalFile(),
          "real encoded icon follows QUrl contract");
    CHECK(!QIcon(resolveIconPath(source)).isNull(),
          "real encoded icon loads after resolution");

    QGuiApplication::setWindowIcon(QIcon());
    prism::WindowHelper::instance()->setAppIcon(source);
    CHECK(!QGuiApplication::windowIcon().isNull(),
          "WindowHelper loads real encoded icon");

    prism::SystemTrayIcon tray;
    tray.setIcon(source);
    QSystemTrayIcon *nativeTray = tray.findChild<QSystemTrayIcon *>();
    CHECK(nativeTray && !nativeTray->icon().isNull(),
          "SystemTrayIcon loads real encoded icon");
}

static void testAvailableScreenGeometry() {
    QScreen *screen = QGuiApplication::primaryScreen();
    CHECK(screen, "WindowHelper geometry has a primary screen");
    if (!screen)
        return;

    const QRect expected = screen->availableGeometry();
    const QPoint center = screen->geometry().center();
    const QVariantMap actual = prism::WindowHelper::instance()
                                   ->availableScreenGeometryAt(center.x(), center.y());
    CHECK(actual.value(QStringLiteral("x")).toInt() == expected.x()
              && actual.value(QStringLiteral("y")).toInt() == expected.y()
              && actual.value(QStringLiteral("width")).toInt() == expected.width()
              && actual.value(QStringLiteral("height")).toInt() == expected.height(),
          "WindowHelper returns QScreen availableGeometry");
}

int main(int argc, char *argv[]) {
    if (!prism::test::configureNonInteractiveProcess()) return 2;
    QApplication app(argc, argv);
    using namespace prism;

    qInfo() << "=== Icon path URL contract ===";
    testIconPathUrlMatrix();
    testRealEncodedIcon();
    testAvailableScreenGeometry();

    qInfo() << "=== SystemTray 烟测 ===";
    // 构造 + addAction + addSeparator 不崩 (QApplication 下 QMenu 正常)
    {
        SystemTrayIcon tray(QString(), QStringLiteral("测试托盘"));
        bool clicked = false;
        tray.addAction(QStringLiteral("打开"), [&clicked]() { clicked = true; });
        tray.addSeparator();
        tray.addAction(QStringLiteral("退出"), nullptr);
        CHECK(true, "SystemTrayIcon 构造+addAction+addSeparator 无崩溃");
        CHECK(true, QStringLiteral("isAvailable=%1(环境相关)")
                        .arg(SystemTrayIcon::isAvailable()).toUtf8().constData());
    }

    qInfo() << "=== SingleInstance 烟测 ===";
    {
        // 首个实例: 不应判定为 running
        SingleInstance si(QStringLiteral("prism_test_singleton_xyz"));
        CHECK(!si.isRunning(), "首个实例 isRunning=false");

        // 第二个同 id 实例: 应判定为 running
        SingleInstance si2(QStringLiteral("prism_test_singleton_xyz"));
        CHECK(si2.isRunning(), "第二实例 isRunning=true");
    }

    qInfo() << "";
    if (g_failed == 0)
        qInfo() << "ALL_TESTS_PASSED";
    else
        qCritical() << "TESTS_FAILED:" << g_failed;

    // 不进事件循环, 直接返回 (烟测不需要)
    return g_failed == 0 ? 0 : 1;
}
